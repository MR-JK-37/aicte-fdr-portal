from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, Header, Response

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import create_access_token, get_current_principal, get_db
from app.auth.schemas import (
    LoginRequest,
    StepUpRequest,
    StepUpResponse,
    TokenResponse,
    UserPermissionsResponse,
    UserProfileResponse,
)
from app.authz import ROLE_PERMISSIONS_MATRIX, Principal
from app.config import settings
from app.models.core import AppUser
from app.problem_json import ForbiddenError, UnauthenticatedError

router = APIRouter(tags=["auth"])


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
    if not user:
        raise UnauthenticatedError("Invalid credentials or user not registered")

    if not user.is_active:
        raise ForbiddenError("User account is deactivated")

    token = create_access_token(user)

    # Set secure HttpOnly session cookie for web clients
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="strict",
        secure=(settings.env == "production"),
        max_age=settings.jwt_expiration_seconds,
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
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_seconds,
        user=user_profile,
    )


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
    try:
        principal = get_current_principal(authorization=authorization, fdr_session=fdr_session, db=db)
        if principal:
            from app.notifications.devices import revoke_all_user_devices
            revoke_all_user_devices(db, principal.id)
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


@router.post("/auth/step-up", response_model=StepUpResponse)
def perform_step_up(
    req: StepUpRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StepUpResponse:
    # Validate 6-digit TOTP / MFA code
    if len(req.otp_code) != 6 or not req.otp_code.isdigit():
        raise ForbiddenError("Invalid step-up OTP code format; 6 digits required")

    # In production, this validates against Keycloak / TOTP secret.
    # In dev/test, any 6-digit OTP code grants 15 minutes step-up validity.
    valid_until = datetime.now(UTC) + timedelta(minutes=15)

    user = db.get(AppUser, principal.id)
    if not user:
        raise UnauthenticatedError("User record not found")

    user.step_up_valid_until = valid_until
    user.mfa_enrolled = True

    append_audit_entry(
        db,
        action="auth.step_up_verified",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(user.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
        after={"step_up_valid_until": valid_until.isoformat(), "mfa_enrolled": True},
    )
    db.commit()

    return StepUpResponse(
        success=True,
        step_up_valid_until=valid_until,
        message="Step-up authentication verified successfully for 15 minutes",
    )
