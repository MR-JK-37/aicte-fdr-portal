from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Cookie, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authz import PermissionVerb, Principal, authorise
from app.config import settings
from app.db import SessionLocal, set_app_context
from app.models.core import AppUser
from app.problem_json import UnauthenticatedError


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(user: AppUser, expires_delta: int | None = None) -> str:
    now = datetime.now(UTC)
    exp = int(
        (
            now + timedelta(seconds=expires_delta or settings.jwt_expiration_seconds)
        ).timestamp()
    )
    payload = {
        "sub": user.keycloak_sub or str(user.id),
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "institution_id": str(user.institution_id) if user.institution_id else None,
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
    set_app_context(
        db,
        role=role_str,
        institution_id=str(user.institution_id) if user.institution_id else None,
        user_id=str(user.id),
        role_scope={
            "institution_id": str(user.institution_id) if user.institution_id else None,
            "region_id": user.region_id,
        },
        assurance={"mfa": user.mfa_enrolled, "step_up": step_up_valid},
    )

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
    )


def require_permission(verb: PermissionVerb | str) -> Callable[[Principal], Principal]:
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        authorise(principal, verb)
        return principal

    return dependency
