from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Cookie, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authz import PermissionVerb, Principal, authorise
from app.config import settings
from app.db import get_db, set_app_context
from app.models.core import AppUser
from app.models.enums import AppRole
from app.problem_json import UnauthenticatedError


def create_access_token(
    user: AppUser,
    expires_delta: int | None = None,
    session_id: uuid.UUID | str | None = None,
) -> str:
    now = datetime.now(UTC)
    exp = int(
        (
            now
            + timedelta(
                seconds=expires_delta or settings.access_token_expiration_seconds
            )
        ).timestamp()
    )
    payload = {
        "sub": user.keycloak_sub or str(user.id),
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "institution_id": str(user.institution_id) if user.institution_id else None,
        "session_id": str(session_id) if session_id else None,
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_principal(
    authorization: str | None = Header(None, alias="Authorization"),
    fdr_session: str | None = Cookie(None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db),
) -> Principal:
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif fdr_session:
        token = fdr_session.strip()

    if not token:
        raise UnauthenticatedError("Authentication credential missing or malformed")

    try:
        data = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise UnauthenticatedError("Session token has expired")
    except jwt.PyJWTError as e:
        raise UnauthenticatedError(f"Invalid authentication token: {e}")

    user_id_str = data.get("user_id")
    if not user_id_str:
        raise UnauthenticatedError("Token missing user identity claim")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthenticatedError("Invalid user identity in token")

    # Set user context so RLS policy on app_users permits lookup
    token_role = data.get("role", "")
    set_app_context(db, role=token_role, user_id=user_id_str)

    # Fetch user from database to ensure fresh status and role
    user = db.execute(
        select(AppUser).where(AppUser.id == user_uuid)
    ).scalar_one_or_none()
    if not user:
        raise UnauthenticatedError("Authenticated user record not found")

    if not user.is_active:
        raise UnauthenticatedError("User account is deactivated")

    # Determine step-up validity
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

    # Establish RLS parameters in the database transaction
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    role_scope_dict: dict[str, Any] = {
        "institution_id": str(user.institution_id) if user.institution_id else None,
        "region_id": user.region_id,
    }
    if user.role == AppRole.BANK_VERIFIER:
        if "@sbi." in user.email.lower():
            role_scope_dict["bank_name"] = "State Bank of India"
        elif "@pnb." in user.email.lower():
            role_scope_dict["bank_name"] = "Punjab National Bank"
        elif "@hdfc." in user.email.lower():
            role_scope_dict["bank_name"] = "HDFC Bank"
        elif "@icici." in user.email.lower():
            role_scope_dict["bank_name"] = "ICICI Bank"

    set_app_context(
        db,
        role=role_str,
        institution_id=str(user.institution_id) if user.institution_id else None,
        user_id=str(user.id),
        role_scope=role_scope_dict,
        assurance={"mfa": user.mfa_enrolled, "step_up": step_up_valid},
    )

    session_id_str = data.get("session_id")
    session_uuid = None
    if session_id_str:
        try:
            session_uuid = uuid.UUID(session_id_str)
        except ValueError:
            session_uuid = None

    return Principal(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        institution_id=user.institution_id,
        region_id=user.region_id,
        delegation_limit=user.delegation_limit,
        is_active=user.is_active,
        mfa_enrolled=user.mfa_enrolled,
        step_up_valid_until=user.step_up_valid_until,
        role_scope=role_scope_dict,
        session_id=session_uuid,
    )


def require_permission(verb: PermissionVerb | str) -> Callable[[Principal], Principal]:
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        authorise(principal, verb)
        return principal

    return dependency
