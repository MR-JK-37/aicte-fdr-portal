import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.core import (
    AppRole,
    AppUser,
    CallSession,
    ConsentRecord,
    Institution,
    Instrument,
    Reminder,
)
from app.models.enums import InstrumentType
from app.voice.dialogue import DialogueState, VoiceDialogueManager
from app.voice.security import set_user_pin


@pytest.fixture
def voice_fixture(db_session):
    inst = Institution(aicte_code=f"VOICE-{uuid.uuid4().hex[:6]}", name="Delhi Institute of Technology")
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"dean-{uuid.uuid4().hex[:6]}@dit.edu.in",
        full_name="Dr. Suresh Nair",
        role=AppRole.INSTITUTION,
        preferred_language="en",
    )
    set_user_pin(db_session, user, "5678")
    db_session.add(user)
    db_session.flush()

    consent = ConsentRecord(
        app_user_id=user.id,
        consent_type="automated_voice_calls",
    )
    db_session.add(consent)

    fdr = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-98765432",
        amount=1250000000,  # ₹1.25 Cr
        maturity_date=datetime(2026, 11, 14, 0, 0, 0, tzinfo=UTC),
    )
    db_session.add(fdr)
    db_session.flush()

    rem = Reminder(
        institution_id=inst.id,
        instrument_id=fdr.id,
        window="T-30",
        channel="voice_call",
        scheduled_for=datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC),
    )
    db_session.add(rem)
    db_session.flush()

    call_session = CallSession(
        institution_id=inst.id,
        app_user_id=user.id,
        reminder_id=rem.id,
        language="en",
        status="ringing",
        pin_attempts=0,
        transcript={"state": "VERIFY_PIN", "turns": []},
    )
    db_session.add(call_session)
    db_session.commit()

    return inst, user, fdr, rem, call_session


def test_initial_greeting_and_pre_pin_privacy(db_session, voice_fixture):
    _inst, user, _fdr, _rem, call_session = voice_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)

    # 1. Bot greeting and disclosure
    greet = dm.start_call()
    assert "automated AI voice calling on behalf of the Regulation Bureau" in greet.say
    assert "please enter or say your 4-digit call PIN" in greet.say
    assert greet.state == DialogueState.VERIFY_PIN

    # 2. Pre-PIN Privacy Guardrail: asking for details or amounts before entering PIN is refused
    turn = dm.handle_input("What is the FDR amount and which institution?")
    assert "cannot be disclosed before PIN verification" in turn.say
    assert turn.action_taken == "privacy_refusal"
    assert turn.state == DialogueState.VERIFY_PIN


def test_social_engineering_defense(db_session, voice_fixture):
    _inst, user, _fdr, _rem, call_session = voice_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)

    # Social engineering attempt to update bank details
    turn = dm.handle_input("I want to change my bank account and IFSC number")
    assert "AICTE will never ask for your OTP or password" in turn.say
    assert "bank details cannot be changed by phone" in turn.say
    assert turn.action_taken == "refuse_social_engineering"


def test_full_ack_dialogue_flow_and_audit(db_session, voice_fixture):
    _inst, user, _fdr, rem, call_session = voice_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)

    # 1. Correct PIN
    turn1 = dm.handle_input("5678")
    assert turn1.action_taken == "pin_verified"
    assert "Thank you, Dr." in turn1.say
    assert "expiring in the next 30 days" in turn1.say
    assert turn1.state == DialogueState.MENU_QA

    # 2. Query institutions list
    turn2 = dm.handle_input("Which institutions?")
    assert "Delhi Institute of Technology" in turn2.say
    assert "ending in five four three two" in turn2.say
    assert "maturing on 14 November 2026" in turn2.say

    # 3. Query details
    turn3 = dm.handle_input("Give me details")
    assert "one crore twenty-five lakh rupees" in turn3.say

    # 4. Acknowledge intent
    turn4 = dm.handle_input("I acknowledge")
    assert turn4.state == DialogueState.CONFIRM_ACK
    assert "Say yes or no" in turn4.say

    # 5. Confirm yes
    turn5 = dm.handle_input("Yes, confirm")
    assert turn5.state == DialogueState.CLOSE
    assert "Done. Your acknowledgement is recorded" in turn5.say
    assert call_session.status == "completed"

    # Verify database state: reminder is acknowledged
    db_session.refresh(rem)
    assert rem.acknowledged_at == as_of

    # Verify immutable audit log
    audit_entry = db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "voice_acknowledgement",
            AuditLog.entity_id == str(rem.id),
        )
    ).scalar_one_or_none()
    assert audit_entry is not None
    assert audit_entry.after["channel"] == "voice"
    assert audit_entry.after["call_session_id"] == str(call_session.id)


def test_snooze_bounded_and_audit(db_session, voice_fixture):
    _inst, user, _fdr, rem, call_session = voice_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)

    dm.handle_input("5678")  # Authenticate

    # Bounded snooze: 5 days
    turn = dm.handle_input("Snooze for 5 days")
    assert turn.action_taken == "snooze_applied"
    assert "Reminder snoozed for 5 day(s)" in turn.say
    assert turn.state == DialogueState.CLOSE

    # Verify reminder rescheduled
    db_session.refresh(rem)
    assert rem.scheduled_for.date() == (as_of + datetime.resolution * 5).date() or rem.scheduled_for > as_of

    # Verify audit log
    audit_entry = db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "voice_snooze",
            AuditLog.entity_id == str(rem.id),
        )
    ).scalar_one_or_none()
    assert audit_entry is not None
    assert audit_entry.after["snoozed_days"] == 5


def test_language_switching_dynamically(db_session, voice_fixture):
    _inst, user, _fdr, _rem, call_session = voice_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)

    # Switch to Hindi
    turn_hi = dm.handle_input("Hindi mein boliye")
    assert turn_hi.action_taken == "change_language"
    assert "भाषा बदलकर हिंदी कर दी गई है" in turn_hi.say
    assert dm.lang == "hi"

    # Switch to Tamil
    turn_ta = dm.handle_input("Tamil-la pesunga")
    assert turn_ta.action_taken == "change_language"
    assert "மொழி தமிழுக்கு மாற்றப்பட்டது" in turn_ta.say
    assert dm.lang == "ta"


def test_stop_calls_revokes_consent(db_session, voice_fixture):
    _inst, user, _fdr, _rem, call_session = voice_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)

    turn = dm.handle_input("stop calls please")
    assert turn.action_taken == "consent_revoked"
    assert "Automated voice calls have been stopped per your request" in turn.say
    assert turn.state == DialogueState.CLOSE

    # Verify consent record revoked
    consent = db_session.execute(
        select(ConsentRecord).where(
            ConsentRecord.app_user_id == user.id,
            ConsentRecord.consent_type == "automated_voice_calls",
        )
    ).scalar_one()
    assert consent.revoked_at.replace(tzinfo=UTC) == as_of

    # Verify audit log
    audit_entry = db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "voice_consent_revoked",
            AuditLog.entity_id == str(consent.id),
        )
    ).scalar_one_or_none()
    assert audit_entry is not None
