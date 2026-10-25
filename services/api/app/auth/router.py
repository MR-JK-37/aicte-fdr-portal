from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, Header, Response

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import create_access_token, get_current_principal, get_db
from app.auth.navigation import get_navigation_for_role
from app.auth.schemas import (
    DevAccountOut,
    DevLoginRequest,
    LoginRequest,
    MfaEnrolConfirmRequest,
    MfaEnrolConfirmResponse,
    MfaEnrolStartResponse,
    NavigationResponse,
    NavItemOut,
    ProfileCompletionItem,
    ProfileCompletionResponse,
    RefreshRequest,
    SessionInfo,
    StepUpRequest,
    StepUpResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserPermissionsResponse,
    UserProfileResponse,
)
from app.auth.security import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_recovery_codes,
    generate_refresh_token,
    generate_totp_secret,
    hash_recovery_code,
    hash_refresh_token,
    is_expired,
    is_locked,
    lockout_expiry,
    session_expiry,
    totp_provisioning_uri,
    verify_password,
    verify_totp_code,
)
from app.authz import ROLE_PERMISSIONS_MATRIX, Principal
from app.config import settings
from app.models.core import AppSession, AppUser
from app.problem_json import ForbiddenError, NotFoundError, UnauthenticatedError

router = APIRouter(tags=["auth"])


def _issue_session_and_tokens(
    user: AppUser, db: Session, response: Response, device_label: str | None
) -> TokenResponse:
    """One place that creates a session row + access/refresh token pair, used by
    both /auth/login and (eventually) any other real-credential-verified path."""
    refresh_token = generate_refresh_token()
    session = AppSession(
        id=uuid.uuid4(),
        app_user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        device_label=device_label,
        expires_at=session_expiry(),
    )
    db.add(session)
    db.flush()  # need session.id for the access token claim before commit

    access_token = create_access_token(user, session_id=session.id)
    db.commit()

    response.set_cookie(
        key=settings.session_cookie_name,
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
        max_age=settings.access_token_expiration_seconds,
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
        max_age=settings.refresh_token_expiration_days * 86400,
        path="/v1/auth",
    )

    now = datetime.now(UTC)
    step_up_valid = bool(
        user.step_up_valid_until
        and (
            user.step_up_valid_until.replace(tzinfo=UTC)
            if user.step_up_valid_until.tzinfo is None
            else user.step_up_valid_until.astimezone(UTC)
        )
        >= now
    )

    user_profile = UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        institution_id=str(user.institution_id) if user.institution_id else None,
        region_id=user.region_id,
        mfa_enrolled=user.mfa_enrolled,
        step_up_valid=step_up_valid,
        step_up_valid_until=user.step_up_valid_until,
        delegation_limit=user.delegation_limit,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expiration_seconds,
        refresh_token=refresh_token,
        user=user_profile,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(
    req: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    # Set internal context to query user by email
    from app.db import set_app_context

    set_app_context(db, role="platform_operator")

    user = db.execute(
        select(AppUser).where(AppUser.email == req.email.strip().lower())
    ).scalar_one_or_none()

    # Same generic error for "no such user" and "wrong password" — AUTH_ROLES_MATRIX.md
    # §2.2(1): "no account enumeration".
    generic_error = "Invalid credentials"

    if not user:
        raise UnauthenticatedError(generic_error)

    if not user.is_active:
        raise ForbiddenError("User account is deactivated")

    if is_locked(user.locked_until):
        raise ForbiddenError(
            "Account temporarily locked after repeated failed sign-in attempts"
        )

    if not verify_password(req.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= settings.max_login_attempts:
            user.locked_until = lockout_expiry()
            user.failed_login_count = 0
        db.commit()
        raise UnauthenticatedError(generic_error)

    if user.totp_secret_encrypted:
        secret = decrypt_totp_secret(user.totp_secret_encrypted)
        totp_valid = False
        if secret and req.totp_code and verify_totp_code(secret, req.totp_code):
            totp_valid = True
        elif req.totp_code and user.recovery_codes_hashed:
            code_hash = hash_recovery_code(req.totp_code)
            if code_hash in user.recovery_codes_hashed:
                totp_valid = True
                user.recovery_codes_hashed = [
                    h for h in user.recovery_codes_hashed if h != code_hash
                ]
                db.flush()

        if not totp_valid:
            raise UnauthenticatedError(
                "Valid TOTP code required" if not req.totp_code else generic_error
            )

    user.failed_login_count = 0
    db.commit()

    # The commit above ends the transaction `set_app_context`'s SET LOCAL context was
    # scoped to — re-establish it before the app_sessions insert below, which is
    # RLS-protected and needs app.role set in the transaction performing the insert.
    set_app_context(db, role="platform_operator")
    token_response = _issue_session_and_tokens(user, db, response, req.device_label)

    append_audit_entry(
        db,
        action="auth.login",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    db.commit()

    return token_response


def _refuse_outside_dev_staging() -> None:
    """Dev/staging-only convenience endpoints 404 in production — same refusal
    rule as scripts/seed_staging.py and the existing TOTP testing bypass in
    app/auth/security.py:verify_totp_code. Never reachable outside those envs,
    and never anything a client needs secrets to use."""
    if settings.env == "production":
        raise NotFoundError("Not found")


@router.get("/auth/dev-accounts", response_model=list[DevAccountOut])
def list_dev_accounts(db: Session = Depends(get_db)) -> list[DevAccountOut]:
    """Lists the seeded staging roster for one-click role login in non-prod
    environments only. Returns email/role/name — never a password or TOTP
    secret, so there is nothing here for a client bundle or public repo to
    leak (CLAUDE.md non-negotiable #1)."""
    _refuse_outside_dev_staging()

    from app.db import set_app_context

    set_app_context(db, role="platform_operator")
    users = (
        db.execute(select(AppUser).where(AppUser.is_active.is_(True)))
        .scalars()
        .all()
    )
    return [
        DevAccountOut(
            email=u.email,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            full_name=u.full_name,
        )
        for u in users
    ]


@router.post("/auth/dev-login", response_model=TokenResponse)
def dev_login(
    req: DevLoginRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    """One-click login as a known seeded account, non-prod only. No password
    or TOTP is accepted or required — the refusal in `_refuse_outside_dev_staging`
    is the only gate, exactly as `verify_totp_code`'s 000000/123456 bypass
    already works for this codebase in non-production. Issues a real session
    through the same path as a credentialed login, and is audited distinctly
    (`auth.dev_login`) so it is never indistinguishable from a real login in
    the audit trail."""
    _refuse_outside_dev_staging()

    from app.db import set_app_context

    set_app_context(db, role="platform_operator")

    user = db.execute(
        select(AppUser).where(AppUser.email == req.email.strip().lower())
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise NotFoundError("Dev account", req.email)

    token_response = _issue_session_and_tokens(user, db, response, req.device_label)

    append_audit_entry(
        db,
        action="auth.dev_login",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    db.commit()

    return token_response


@router.post("/auth/logout")
def logout(
    response: Response,
    authorization: str | None = Header(None, alias="Authorization"),
    fdr_session: str | None = Cookie(None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
    )
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
        path="/v1/auth",
    )
    try:
        principal = get_current_principal(
            authorization=authorization, fdr_session=fdr_session, db=db
        )
        if principal:
            from app.notifications.devices import revoke_all_user_devices

            revoke_all_user_devices(db, principal.id)
            if principal.session_id:
                session = db.get(AppSession, principal.session_id)
                if session and session.app_user_id == principal.id:
                    session.revoked_at = datetime.now(UTC)
            append_audit_entry(
                db,
                action="auth.logout",
                entity_type="app_user",
                entity_id=str(principal.id),
                actor_id=str(principal.id),
            )
            db.commit()
    except UnauthenticatedError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.debug("Non-critical cleanup failure on logout: %s", exc)
    return {"message": "Logged out successfully"}


@router.post("/auth/logout-all")
def logout_all(
    response: Response,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Revokes every session for the caller — AUTH_ROLES_MATRIX.md §2.2(7): "Sign out
    everywhere"."""
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
    )
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
        path="/v1/auth",
    )

    from app.notifications.devices import revoke_all_user_devices

    revoke_all_user_devices(db, principal.id)
    now = datetime.now(UTC)
    sessions = db.execute(
        select(AppSession).where(
            AppSession.app_user_id == principal.id, AppSession.revoked_at.is_(None)
        )
    ).scalars()
    for s in sessions:
        s.revoked_at = now

    append_audit_entry(
        db,
        action="auth.logout_all",
        entity_type="app_user",
        entity_id=str(principal.id),
        actor_id=str(principal.id),
    )
    db.commit()
    return {"message": "Signed out of all sessions"}


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(
    req: RefreshRequest,
    response: Response,
    fdr_refresh: str | None = Cookie(None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
) -> TokenResponse:
    from app.db import set_app_context

    set_app_context(db, role="platform_operator")

    presented = req.refresh_token or fdr_refresh
    if not presented:
        raise UnauthenticatedError("Refresh token missing")

    presented_hash = hash_refresh_token(presented)

    current_match = db.execute(
        select(AppSession).where(AppSession.refresh_token_hash == presented_hash)
    ).scalar_one_or_none()

    if (
        current_match
        and not current_match.revoked_at
        and not is_expired(current_match.expires_at)
    ):
        user = db.get(AppUser, current_match.app_user_id)
        if not user or not user.is_active:
            raise UnauthenticatedError("Account no longer available")

        # Rotate: this token becomes the "previous" one, a fresh one takes over.
        new_refresh_token = generate_refresh_token()
        current_match.previous_token_hash = current_match.refresh_token_hash
        current_match.refresh_token_hash = hash_refresh_token(new_refresh_token)
        current_match.last_seen_at = datetime.now(UTC)
        db.flush()

        access_token = create_access_token(user, session_id=current_match.id)
        db.commit()

        response.set_cookie(
            key=settings.session_cookie_name,
            value=access_token,
            httponly=True,
            samesite="strict",
            secure=(settings.env == "production"),
            max_age=settings.access_token_expiration_seconds,
        )
        response.set_cookie(
            key=settings.refresh_cookie_name,
            value=new_refresh_token,
            httponly=True,
            samesite="strict",
            secure=(settings.env == "production"),
            max_age=settings.refresh_token_expiration_days * 86400,
            path="/v1/auth",
        )

        now = datetime.now(UTC)
        step_up_valid = bool(
            user.step_up_valid_until
            and (
                user.step_up_valid_until.replace(tzinfo=UTC)
                if user.step_up_valid_until.tzinfo is None
                else user.step_up_valid_until.astimezone(UTC)
            )
            >= now
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expiration_seconds,
            refresh_token=new_refresh_token,
            user=UserProfileResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                role=user.role.value if hasattr(user.role, "value") else str(user.role),
                institution_id=str(user.institution_id)
                if user.institution_id
                else None,
                region_id=user.region_id,
                mfa_enrolled=user.mfa_enrolled,
                step_up_valid=step_up_valid,
                step_up_valid_until=user.step_up_valid_until,
                delegation_limit=user.delegation_limit,
            ),
        )

    # Not the current token for any session — check whether it's a *previously
    # rotated-out* token being replayed. That's a theft/reuse signal: kill the
    # session it belonged to immediately rather than silently rejecting.
    reused_session = db.execute(
        select(AppSession).where(
            AppSession.previous_token_hash == presented_hash,
            AppSession.revoked_at.is_(None),
        )
    ).scalar_one_or_none()
    if reused_session:
        reused_session.revoked_at = datetime.now(UTC)
        append_audit_entry(
            db,
            action="auth.refresh_token_reuse_detected",
            entity_type="app_session",
            entity_id=str(reused_session.id),
            actor_id=str(reused_session.app_user_id),
            after={"revoked": True},
        )
        db.commit()

    raise UnauthenticatedError("Invalid or expired refresh token")


@router.get("/auth/sessions", response_model=list[SessionInfo])
def list_sessions(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> list[SessionInfo]:
    sessions = db.execute(
        select(AppSession)
        .where(AppSession.app_user_id == principal.id, AppSession.revoked_at.is_(None))
        .order_by(AppSession.last_seen_at.desc())
    ).scalars()
    return [
        SessionInfo(
            session_id=str(s.id),
            device_label=s.device_label,
            ip_area=s.ip_area,
            created_at=s.created_at,
            last_seen_at=s.last_seen_at,
            expires_at=s.expires_at,
            current=(s.id == principal.session_id),
        )
        for s in sessions
        if not is_expired(s.expires_at)
    ]


@router.delete("/auth/sessions/{session_id}")
def revoke_session(
    session_id: uuid.UUID,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    session = db.get(AppSession, session_id)
    if not session or session.app_user_id != principal.id:
        # Same 404 for "doesn't exist" and "not yours" — cross-tenant ids never 403.
        raise NotFoundError("Session not found")

    session.revoked_at = datetime.now(UTC)
    append_audit_entry(
        db,
        action="auth.session_revoked",
        entity_type="app_session",
        entity_id=str(session.id),
        actor_id=str(principal.id),
    )
    db.commit()
    return {"message": "Session revoked"}


@router.get("/me", response_model=UserProfileResponse)
def get_me(
    principal: Principal = Depends(get_current_principal),
) -> UserProfileResponse:
    now = datetime.now(UTC)
    step_up_valid = bool(
        principal.step_up_valid_until
        and (
            principal.step_up_valid_until.replace(tzinfo=UTC)
            if principal.step_up_valid_until.tzinfo is None
            else principal.step_up_valid_until.astimezone(UTC)
        )
        >= now
    )

    return UserProfileResponse(
        id=str(principal.id),
        email=principal.email,
        full_name=principal.full_name,
        role=principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role),
        institution_id=str(principal.institution_id)
        if principal.institution_id
        else None,
        region_id=principal.region_id,
        mfa_enrolled=principal.mfa_enrolled,
        step_up_valid=step_up_valid,
        step_up_valid_until=principal.step_up_valid_until,
        delegation_limit=principal.delegation_limit,
    )


@router.get("/me/permissions", response_model=UserPermissionsResponse)
def get_my_permissions(
    principal: Principal = Depends(get_current_principal),
) -> UserPermissionsResponse:
    role_perms = ROLE_PERMISSIONS_MATRIX.get(principal.role, {})
    return UserPermissionsResponse(
        role=principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role),
        permissions=sorted(role_perms.keys()),
    )


@router.get("/me/navigation", response_model=NavigationResponse)
def get_my_navigation(
    principal: Principal = Depends(get_current_principal),
) -> NavigationResponse:
    """The sidebar/tab manifest for the caller's role (AUTH_ROLES_MATRIX.md §1).
    Clients render from this — role names are never hard-coded in client nav logic
    (AUTH_ROLES_MATRIX.md §2.3)."""
    nav = get_navigation_for_role(principal.role)

    def _to_out(item):
        return NavItemOut(
            key=item.key,
            label_key=item.label_key,
            icon_key=item.icon_key,
            route=item.route,
            required_permission=item.required_permission,
        )

    return NavigationResponse(
        landing_route=nav.landing_route,
        web_sidebar=[_to_out(i) for i in nav.web_sidebar],
        mobile_tabs=[_to_out(i) for i in nav.mobile_tabs],
    )


@router.get("/me/profile-completion", response_model=ProfileCompletionResponse)
def get_my_profile_completion(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ProfileCompletionResponse:
    user = db.get(AppUser, principal.id)
    if not user:
        raise UnauthenticatedError("User record not found")

    required_items = [
        ProfileCompletionItem(
            key="name", label_key="profile.name", complete=bool(user.full_name)
        ),
        ProfileCompletionItem(
            key="designation",
            label_key="profile.designation",
            complete=bool(user.designation),
        ),
        ProfileCompletionItem(
            key="verified_mobile",
            label_key="profile.verified_mobile",
            # Never true until a real SMS/OTP provider exists — see migration
            # e5f6a7b8c9d0. This item is meant to stay incomplete, not a bug.
            complete=user.mobile_verified,
        ),
        ProfileCompletionItem(
            key="language",
            label_key="profile.language",
            complete=bool(user.preferred_language),
        ),
        ProfileCompletionItem(
            key="mfa_enrolled",
            label_key="profile.mfa_enrolled",
            complete=user.mfa_enrolled,
        ),
    ]
    optional_items = [
        ProfileCompletionItem(
            key="passkey",
            label_key="profile.passkey",
            # No passkey system exists yet (docs/phase-reports/R2.md) — always
            # false, always optional, never counted toward the percentage.
            complete=False,
            optional=True,
        ),
    ]

    completed = sum(1 for i in required_items if i.complete)
    percent = round(100 * completed / len(required_items)) if required_items else 0

    return ProfileCompletionResponse(
        percent=percent, items=required_items + optional_items
    )


@router.patch("/me/profile", response_model=UserProfileResponse)
def update_my_profile(
    req: UpdateProfileRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    user = db.get(AppUser, principal.id)
    if not user:
        raise UnauthenticatedError("User record not found")

    before = {
        "full_name": user.full_name,
        "designation": user.designation,
        "mobile_number": user.mobile_number,
        "preferred_language": user.preferred_language,
    }

    if req.full_name is not None:
        user.full_name = req.full_name
    if req.designation is not None:
        user.designation = req.designation
    if req.mobile_number is not None:
        # Changing the number invalidates any prior verification — there isn't one
        # yet (mobile_verified is always False today), but this keeps the
        # invariant correct once a real verification flow exists.
        user.mobile_number = req.mobile_number
        user.mobile_verified = False
    if req.preferred_language is not None:
        user.preferred_language = req.preferred_language

    append_audit_entry(
        db,
        action="auth.profile_updated",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
        before=before,
        after={
            "full_name": user.full_name,
            "designation": user.designation,
            "mobile_number": user.mobile_number,
            "preferred_language": user.preferred_language,
        },
    )
    db.commit()

    now = datetime.now(UTC)
    step_up_valid = bool(
        user.step_up_valid_until
        and (
            user.step_up_valid_until.replace(tzinfo=UTC)
            if user.step_up_valid_until.tzinfo is None
            else user.step_up_valid_until.astimezone(UTC)
        )
        >= now
    )
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        institution_id=str(user.institution_id) if user.institution_id else None,
        region_id=user.region_id,
        mfa_enrolled=user.mfa_enrolled,
        step_up_valid=step_up_valid,
        step_up_valid_until=user.step_up_valid_until,
        delegation_limit=user.delegation_limit,
    )


@router.post("/auth/step-up", response_model=StepUpResponse)
def perform_step_up(
    req: StepUpRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StepUpResponse:
    user = db.get(AppUser, principal.id)
    if not user:
        raise UnauthenticatedError("User record not found")

    if not user.totp_secret_encrypted:
        raise ForbiddenError(
            "Step-up requires TOTP to be enrolled first (POST /v1/auth/mfa/enrol/confirm)"
        )

    secret = decrypt_totp_secret(user.totp_secret_encrypted)
    if not secret or not verify_totp_code(secret, req.otp_code):
        raise ForbiddenError("Invalid step-up TOTP code")

    valid_until = datetime.now(UTC) + timedelta(minutes=15)
    user.step_up_valid_until = valid_until

    append_audit_entry(
        db,
        action="auth.step_up_verified",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
        after={"step_up_valid_until": valid_until.isoformat()},
    )
    db.commit()

    return StepUpResponse(
        success=True,
        step_up_valid_until=valid_until,
        message="Step-up authentication verified successfully for 15 minutes",
    )


@router.post("/auth/mfa/enrol/start", response_model=MfaEnrolStartResponse)
def start_mfa_enrolment(
    principal: Principal = Depends(get_current_principal),
) -> MfaEnrolStartResponse:
    """Generates a candidate TOTP secret. Nothing is persisted until
    `/auth/mfa/enrol/confirm` proves the caller's authenticator app actually has it —
    an abandoned enrolment must never leave a usable, unconfirmed secret in the DB."""
    secret = generate_totp_secret()
    return MfaEnrolStartResponse(
        secret=secret,
        provisioning_uri=totp_provisioning_uri(secret, principal.email),
    )


@router.post("/auth/mfa/enrol/confirm", response_model=MfaEnrolConfirmResponse)
def confirm_mfa_enrolment(
    req: MfaEnrolConfirmRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> MfaEnrolConfirmResponse:
    if not verify_totp_code(req.secret, req.totp_code):
        raise ForbiddenError("TOTP code did not match the enrolment secret")

    user = db.get(AppUser, principal.id)
    if not user:
        raise UnauthenticatedError("User record not found")

    recovery_codes = generate_recovery_codes()
    user.totp_secret_encrypted = encrypt_totp_secret(req.secret)
    user.mfa_enrolled = True
    user.recovery_codes_hashed = [hash_recovery_code(c) for c in recovery_codes]

    append_audit_entry(
        db,
        action="auth.mfa_enrolled",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
        after={"mfa_enrolled": True},
    )
    db.commit()

    # Recovery codes are returned exactly once, in plaintext, at the moment they're
    # generated — only their hashes are ever stored (app/auth/security.py).
    return MfaEnrolConfirmResponse(success=True, recovery_codes=recovery_codes)
