import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.models.core import AppRole, AppUser, ConsentRecord, Institution
from app.voice.security import set_user_pin


@pytest.fixture
def client_fixture(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    inst = Institution(aicte_code=f"API-{uuid.uuid4().hex[:6]}", name="APEX Technical Campus")
    db_session.add(inst)
    db_session.flush()

    user_with_consent = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"principal-{uuid.uuid4().hex[:6]}@apex.edu",
        full_name="Dr. Anita Desai",
        role=AppRole.INSTITUTION,
        preferred_language="en",
        quiet_hours_start=21,
        quiet_hours_end=8,
    )
    set_user_pin(db_session, user_with_consent, "4321")
    db_session.add(user_with_consent)
    db_session.flush()

    consent = ConsentRecord(
        app_user_id=user_with_consent.id,
        consent_type="automated_voice_calls",
    )
    db_session.add(consent)

    user_no_consent = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"registrar-{uuid.uuid4().hex[:6]}@apex.edu",
        full_name="Prof. Raman",
        role=AppRole.INSTITUTION,
        preferred_language="hi",
    )
    db_session.add(user_no_consent)
    db_session.commit()

    yield client, inst, user_with_consent, user_no_consent
    app.dependency_overrides.clear()


def test_trigger_call_requires_consent(client_fixture):
    client, _inst, _user_with_consent, user_no_consent = client_fixture
    resp = client.post("/api/v1/calls/trigger", json={"user_id": str(user_no_consent.id)})
    assert resp.status_code == 403
    assert "User has not granted active consent" in resp.json()["detail"]


def test_trigger_call_success_and_webrtc_offer(client_fixture, db_session):
    client, _inst, user_with_consent, _user_no_consent = client_fixture
    resp = client.post("/api/v1/calls/trigger", json={"user_id": str(user_with_consent.id)})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert "token" in data
    assert data["status"] == "ringing"

    session_id = data["session_id"]
    token = data["token"]

    # 1. Invalid token on WebRTC offer
    bad_offer = client.post(
        f"/api/v1/calls/{session_id}/webrtc/offer",
        json={"sdp": "fake_offer_sdp", "token": "tampered_token"},
    )
    assert bad_offer.status_code == 401

    # 2. Valid token on WebRTC offer
    good_offer = client.post(
        f"/api/v1/calls/{session_id}/webrtc/offer",
        json={"sdp": "fake_offer_sdp", "token": token},
    )
    assert good_offer.status_code == 200
    answer_data = good_offer.json()
    assert answer_data["type"] == "answer"
    assert "opus/48000/2" in answer_data["sdp"]

    # Verify session is now in_progress
    sess_resp = client.get(f"/api/v1/calls/{session_id}")
    assert sess_resp.status_code == 200
    assert sess_resp.json()["status"] == "in_progress"


def test_dtmf_entry_and_dialogue_turn(client_fixture):
    client, _inst, user_with_consent, _user_no_consent = client_fixture
    resp = client.post("/api/v1/calls/trigger", json={"user_id": str(user_with_consent.id)})
    session_id = resp.json()["session_id"]

    # DTMF input for PIN entry: "4321"
    dtmf_resp = client.post(f"/api/v1/calls/{session_id}/dtmf", json={"digits": "4321"})
    assert dtmf_resp.status_code == 200
    dtmf_data = dtmf_resp.json()
    assert dtmf_data["action_taken"] == "pin_verified"
    assert "Thank you, Dr." in dtmf_data["say"]
    assert dtmf_data["state"] == "MENU_QA"

    # Dialogue turn post-PIN
    turn_resp = client.post(
        f"/api/v1/calls/{session_id}/turn",
        json={"utterance": "Hindi mein boliye"},
    )
    assert turn_resp.status_code == 200
    assert turn_resp.json()["action_taken"] == "change_language"
    assert "भाषा बदलकर हिंदी कर दी गई है" in turn_resp.json()["say"]


def test_pstn_simulation_notice(client_fixture):
    client, _inst, user_with_consent, _user_no_consent = client_fixture
    resp = client.post("/api/v1/calls/trigger", json={"user_id": str(user_with_consent.id)})
    session_id = resp.json()["session_id"]

    pstn_resp = client.post(f"/api/v1/calls/{session_id}/pstn")
    assert pstn_resp.status_code == 200
    pstn_data = pstn_resp.json()
    assert pstn_data["status"] == "simulated"
    assert "TRAI 1600-series transactional header" in pstn_data["notice"]
    assert "twiml_preview" in pstn_data


def test_hangup_endpoint(client_fixture):
    client, _inst, user_with_consent, _user_no_consent = client_fixture
    resp = client.post("/api/v1/calls/trigger", json={"user_id": str(user_with_consent.id)})
    session_id = resp.json()["session_id"]

    hangup_resp = client.post(f"/api/v1/calls/{session_id}/hangup")
    assert hangup_resp.status_code == 200
    assert hangup_resp.json()["status"] == "completed"

    sess_resp = client.get(f"/api/v1/calls/{session_id}")
    assert sess_resp.json()["status"] == "completed"
    assert sess_resp.json()["ended_at"] is not None
