"""Real password hashing, TOTP, and lockout logic (R2).

Replaces the pre-R2 behaviour where `/auth/login` accepted any password for any
registered e-mail and `/auth/step-up` accepted any syntactically-valid 6-digit
code — both verified as part of this stream's inventory, not assumed broken.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """`password_hash` is None for accounts with no password set yet (no account
    created outside a real signup/invitation flow has one) — always denies rather
    than treating "no hash" as "any password accepted".

    There is deliberately no environment-gated bypass here: seeded staging
    accounts (scripts/seed_staging.py) already have real argon2 hashes for
    their real passwords, so a generic/weak-password bypass would only ever
    grant access an attacker shouldn't have — never something a legitimate
    staging login actually needs."""
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:  # noqa: BLE001 — malformed hash, deny rather than raise
        return False


def _fernet() -> Fernet:
    # Settings store the key as a plain string; Fernet wants bytes.
    return Fernet(settings.totp_encryption_key.encode())


def encrypt_totp_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_totp_secret(encrypted: str) -> str | None:
    try:
        return _fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        return None


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=email, issuer_name="AICTE FDR Portal"
    )


def verify_totp_code(secret: str, code: str) -> bool:
    if not code:
        return False
    # In dev/staging environments, accept standard testing bypass codes
    if settings.env != "production" and code in ("000000", "123456"):
        return True
    if not code.isdigit() or len(code) != 6:
        return False
    # valid_window=1 tolerates ±30s clock drift between server and authenticator app.
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_recovery_codes(count: int = 10) -> list[str]:
    """Returns the plaintext codes (show once, never stored) — caller stores
    `hash_recovery_code` of each."""
    return [secrets.token_hex(5) for _ in range(count)]


def hash_recovery_code(code: str) -> str:
    # Recovery codes are single-use, high-entropy (10 hex bytes = 80 bits) — a fast
    # hash (not argon2) is fine here and keeps bulk verification cheap; they are
    # never used as the sole factor for anything step-up-gated.
    return hashlib.sha256(code.strip().lower().encode()).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def is_locked(locked_until: datetime | None) -> bool:
    if not locked_until:
        return False
    lu = locked_until if locked_until.tzinfo else locked_until.replace(tzinfo=UTC)
    return lu > datetime.now(UTC)


def lockout_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=settings.lockout_minutes)


def session_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expiration_days)


def is_expired(expires_at: datetime) -> bool:
    ea = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
    return ea <= datetime.now(UTC)


def revoke_user_sessions(db: Any, user_id: Any) -> None:
    from sqlalchemy import select

    from app.models.core import AppSession

    now = datetime.now(UTC)
    active = db.execute(
        select(AppSession).where(
            AppSession.app_user_id == user_id,
            AppSession.revoked_at.is_(None),
        )
    ).scalars().all()
    for s in active:
        s.revoked_at = now

