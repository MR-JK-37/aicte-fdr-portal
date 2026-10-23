import os
import uuid
from datetime import UTC, datetime

import pytest

from app.models.core import (
    AppRole,
    AppUser,
    CallSession,
    Institution,
    Instrument,
    Reminder,
)
from app.models.enums import InstrumentType
from app.voice.bot import (
    SarvamNotConfiguredError,
    assert_sarvam_configured,
    build_portal_tools,
    get_voice_bot_config,
)
from app.voice.dialogue import VoiceDialogueManager
from app.voice.security import set_user_pin


@pytest.fixture
def bot_fixture(db_session):
    inst = Institution(aicte_code=f"BOT-{uuid.uuid4().hex[:6]}", name="National Tech Institute")
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"head-{uuid.uuid4().hex[:6]}@nti.ac.in",
        full_name="Prof. Sunita Rao",
        role=AppRole.INSTITUTION,
        preferred_language="en",
    )
    set_user_pin(db_session, user, "9988")
    db_session.add(user)
    db_session.flush()

    fdr = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-BOT-4455",
        amount=50000000,  # 50 Lakh
        maturity_date=datetime(2026, 12, 1, 0, 0, 0, tzinfo=UTC),
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


def test_voice_bot_config():
    config = get_voice_bot_config()
    assert config.stt_model == "saaras:v3"
    assert config.tts_model == "bulbul:v3"
    assert config.allow_interruptions is True


def test_assert_sarvam_unconfigured():
    old = os.environ.pop("SARVAM_API_KEY", None)
    try:
        with pytest.raises(SarvamNotConfiguredError) as exc_info:
            assert_sarvam_configured()
        assert "SARVAM_API_KEY is not set" in str(exc_info.value)
    finally:
        if old:
            os.environ["SARVAM_API_KEY"] = old


def test_portal_tools_binding(db_session, bot_fixture):
    _inst, user, _fdr, _rem, call_session = bot_fixture
    as_of = datetime(2026, 10, 23, 10, 0, 0, tzinfo=UTC)
    dm = VoiceDialogueManager(db_session, call_session, user, as_of)
    tools = build_portal_tools(dm)

    # 1. Tools exist
    assert "verify_pin" in tools
    assert "get_call_brief" in tools
    assert "list_institutions" in tools
    assert "read_details" in tools
    assert "ack" in tools
    assert "snooze" in tools
    assert "escalate" in tools

    # 2. Pre-PIN calls to read details are privacy-protected
    details_res = tools["read_details"]()
    assert "cannot be disclosed before PIN verification" in details_res["say"]

    # 3. Enter PIN tool
    pin_res = tools["verify_pin"]("9988")
    assert pin_res["action_taken"] == "pin_verified"
    assert "Thank you, Prof." in pin_res["say"]

    # 4. Post-PIN list institutions tool
    inst_res = tools["list_institutions"]()
    assert "National Tech Institute" in inst_res["say"]
    assert "ending in four four five five" in inst_res["say"]

    # 5. Ack tool
    ack_res = tools["ack"]("yes")
    assert ack_res["action_taken"] == "acknowledged"
    assert "Done. Your acknowledgement is recorded" in ack_res["say"]
