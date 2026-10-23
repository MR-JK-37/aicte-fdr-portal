"""Call PIN security, cryptographic hashing, and channel locking.

Per Blueprint.txt §5.4 and §5.5:
- Per-user PIN (hashed), entered by DTMF or spoken.
- No financial details spoken before PIN verification.
- Maximum 3 PIN attempts -> 3rd failure locks voice channel for 24 hours.
- Lock event recorded in immutable hash-chained audit_log.
"""

from datetime import datetime, timedelta
import hashlib
import hmac
import os
import secrets

from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.models.core import AppUser, CallSession


def hash_pin(raw_pin: str, salt: bytes | None = None) -> str:
    """Hashes a call PIN using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    if not raw_pin.strip():
        raise ValueError("PIN cannot be empty")
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", raw_pin.strip().encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256$100000${salt.hex()}${dk.hex()}"


def verify_pin(raw_pin: str, stored_hash: str | None) -> bool:
    """Verifies a raw PIN against a stored PBKDF2 hash using constant-time comparison."""
    if not stored_hash or not raw_pin:
        return False
    parts = stored_hash.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    iterations = int(parts[1])
    salt = bytes.fromhex(parts[2])
    expected_dk = bytes.fromhex(parts[3])
    actual_dk = hashlib.pbkdf2_hmac("sha256", raw_pin.strip().encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_dk, expected_dk)


def set_user_pin(session: Session, user: AppUser, raw_pin: str) -> None:
    """Sets the call PIN for an AppUser."""
    user.call_pin_hash = hash_pin(raw_pin)
    session.add(user)


def verify_user_call_pin(
    session: Session,
    user: AppUser,
    call_session: CallSession,
    entered_pin: str,
    as_of: datetime,
) -> tuple[bool, str]:
    """Verifies the PIN for an in-flight call session.

    Returns:
      (True, "verified") if valid.
      (False, "locked") if channel was already locked or just locked on 3rd failure.
      (False, "incorrect_N_attempts_remaining") if invalid but attempts remain.
    """
    # 1. Check if user is currently locked out
    if user.call_pin_locked_until and as_of < user.call_pin_locked_until:
        call_session.status = "locked"
        return False, "locked"

    # 2. Check PIN
    if user.call_pin_hash and verify_pin(entered_pin, user.call_pin_hash):
        call_session.pin_attempts = 0
        call_session.status = "in_progress"
        return True, "verified"

    # 3. Handle failure
    call_session.pin_attempts += 1
    if call_session.pin_attempts >= 3:
        user.call_pin_locked_until = as_of + timedelta(hours=24)
        call_session.status = "locked"
        session.add(user)
        session.add(call_session)

        # Write immutable security audit log entry
        append_audit_entry(
            session,
            action="voice_channel_locked",
            entity_type="call_session",
            entity_id=str(call_session.id),
            before={"pin_attempts": 2, "locked": False},
            after={
                "pin_attempts": call_session.pin_attempts,
                "locked_until": user.call_pin_locked_until.isoformat(),
                "reason": "3_consecutive_pin_failures",
            },
            actor_id=str(user.id),
            institution_id=str(user.institution_id) if user.institution_id else None,
        )
        return False, "locked"

    session.add(call_session)
    remaining = 3 - call_session.pin_attempts
    return False, f"incorrect_{remaining}_attempts_remaining"
