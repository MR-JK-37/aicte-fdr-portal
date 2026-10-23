from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.core import AppRole, AppUser, CallSession, Institution
from app.voice.security import (
    hash_pin,
    set_user_pin,
    verify_pin,
    verify_user_call_pin,
)


def test_hash_and_verify_pin():
    pin = "4821"
    hashed = hash_pin(pin)
    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert verify_pin(pin, hashed) is True
    assert verify_pin("9999", hashed) is False
    assert verify_pin("", hashed) is False
    assert verify_pin("4821", "") is False


def test_pin_failure_locks_after_3_attempts(db_session):
    inst = Institution(aicte_code=f"SEC-{uuid.uuid4().hex[:6]}", name="Security Test Inst")
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"officer-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="Rajesh Sharma",
        role=AppRole.INSTITUTION,
        preferred_language="en",
    )
    set_user_pin(db_session, user, "1234")
    db_session.add(user)
    db_session.flush()

    call_session = CallSession(
        institution_id=inst.id,
        app_user_id=user.id,
        language="en",
        status="ringing",
        pin_attempts=0,
    )
    db_session.add(call_session)
    db_session.commit()

    now = datetime(2026, 10, 23, 10, 0, 0, tzinfo=timezone.utc)

    # Attempt 1: wrong PIN
    ok, reason = verify_user_call_pin(db_session, user, call_session, "0000", now)
    assert ok is False
    assert reason == "incorrect_2_attempts_remaining"
    assert call_session.pin_attempts == 1
    assert user.call_pin_locked_until is None

    # Attempt 2: wrong PIN
    ok, reason = verify_user_call_pin(db_session, user, call_session, "1111", now)
    assert ok is False
    assert reason == "incorrect_1_attempts_remaining"
    assert call_session.pin_attempts == 2
    assert user.call_pin_locked_until is None

    # Attempt 3: 3rd wrong PIN -> LOCKS for 24 hours
    ok, reason = verify_user_call_pin(db_session, user, call_session, "2222", now)
    assert ok is False
    assert reason == "locked"
    assert call_session.status == "locked"
    assert user.call_pin_locked_until == now + timedelta(hours=24)

    # Verify immutable audit log row was appended
    audit_entry = db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "voice_channel_locked",
            AuditLog.entity_id == str(call_session.id),
        )
    ).scalar_one_or_none()
    assert audit_entry is not None
    assert audit_entry.after["reason"] == "3_consecutive_pin_failures"

    # Attempt 4: Even with correct PIN, locked user cannot authenticate before lock expiry
    ok, reason = verify_user_call_pin(db_session, user, call_session, "1234", now + timedelta(hours=1))
    assert ok is False
    assert reason == "locked"

    # After 24 hours (lock expires), correct PIN succeeds
    ok, reason = verify_user_call_pin(db_session, user, call_session, "1234", now + timedelta(hours=25))
    assert ok is True
    assert reason == "verified"
    assert call_session.pin_attempts == 0
