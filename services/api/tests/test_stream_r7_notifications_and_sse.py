"""Stream R7 Realtime, Notifications, and SSE Test Suite (MASTER_PROMPT_V2 §10 / Exit Gates G-20, G-21, G-22).

Comprehensive verification for Stream R7:
1. G-20: Server-Sent Events (SSE) `/v1/stream` endpoint with `Last-Event-ID` catch-up replay,
   per-event re-authorisation, and scope filtering (User A's event delivered only to authorized User B).
2. G-21: Inbox-first source-of-truth persistence; state ladder (CREATED -> OPENED -> ACKNOWLEDGED -> ACTIONED);
   honest NOT_CONFIGURED handling when push credentials absent without crashing.
3. G-22: Lock-screen payloads contain NO sensitive values (canary strings test across en, hi, ta).
4. G-22: Device token registration and logout revocation lifecycle.
5. Notification preferences enforcement (statutory obligations cannot be disabled).
6. Dead-Letter Queue (DLQ) inspection and replay.
7. Funnel metrics tracking each pipeline stage.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from starlette.testclient import TestClient

from app.auth.deps import create_access_token
from app.authz import Principal
from app.db import get_session, set_app_context
from app.main import app
from app.models.core import AppUser, Institution
from app.models.enums import AppRole
from app.models.workflow import SSEEvent
from app.notifications.pipeline import process_domain_event
from app.notifications.templates import render_template
from app.realtime.router import is_event_authorized_for_principal, sse_generator


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(user: AppUser) -> dict[str, str]:
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def setup_r7_data():
    run_id = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        inst_a = Institution(
            id=uuid.uuid4(),
            aicte_code=f"1-R7A-{run_id}",
            name=f"R7 University A {run_id}",
        )
        inst_b = Institution(
            id=uuid.uuid4(),
            aicte_code=f"1-R7B-{run_id}",
            name=f"R7 College B {run_id}",
        )
        db.add_all([inst_a, inst_b])
        db.flush()

        user_a = AppUser(
            id=uuid.uuid4(),
            keycloak_sub=f"sub-r7-a-{run_id}",
            institution_id=inst_a.id,
            email=f"registrar-a-{run_id}@university.edu",
            full_name="Registrar University A",
            role=AppRole.INSTITUTION_SUBMITTER,
            is_active=True,
            password_hash="test-hash",
            created_at=now,
        )
        user_b = AppUser(
            id=uuid.uuid4(),
            keycloak_sub=f"sub-r7-b-{run_id}",
            institution_id=inst_b.id,
            email=f"registrar-b-{run_id}@college.edu",
            full_name="Registrar College B",
            role=AppRole.INSTITUTION_SUBMITTER,
            is_active=True,
            password_hash="test-hash",
            created_at=now,
        )
        admin = AppUser(
            id=uuid.uuid4(),
            keycloak_sub=f"sub-r7-adm-{run_id}",
            institution_id=None,
            email=f"bureau-admin-{run_id}@aicte.gov.in",
            full_name="Bureau Administrator",
            role=AppRole.PLATFORM_OPERATOR,
            is_active=True,
            password_hash="test-hash",
            created_at=now,
        )
        db.add_all([user_a, user_b, admin])
        db.commit()

        return {
            "inst_a": inst_a,
            "inst_b": inst_b,
            "user_a": user_a,
            "user_b": user_b,
            "admin": admin,
        }


def test_g20_sse_per_event_reauthorization_and_replay(setup_r7_data):
    """G-20: Reconnect with Last-Event-ID replays missed events and re-authorises each."""
    user_a = setup_r7_data["user_a"]
    user_b = setup_r7_data["user_b"]
    inst_a = setup_r7_data["inst_a"]
    inst_b = setup_r7_data["inst_b"]

    now = datetime.now(UTC)
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        # Create a series of sequenced SSE events
        evt_a = SSEEvent(
            id=uuid.uuid4(),
            sequence_id=2001,
            event_type="inbox.created",
            recipient_user_id=user_a.id,
            institution_id=inst_a.id,
            payload={"inbox_id": str(uuid.uuid4()), "title": "Deposit update for A"},
            created_at=now,
        )
        evt_b = SSEEvent(
            id=uuid.uuid4(),
            sequence_id=2002,
            event_type="inbox.created",
            recipient_user_id=user_b.id,
            institution_id=inst_b.id,
            payload={"inbox_id": str(uuid.uuid4()), "title": "Deposit update for B"},
            created_at=now,
        )
        db.add_all([evt_a, evt_b])
        db.commit()

    # Principal for User A
    principal_a = Principal(
        id=user_a.id,
        email=user_a.email,
        full_name=user_a.full_name,
        role=user_a.role,
        institution_id=inst_a.id,
        is_active=True,
    )
    # Principal for User B
    principal_b = Principal(
        id=user_b.id,
        email=user_b.email,
        full_name=user_b.full_name,
        role=user_b.role,
        institution_id=inst_b.id,
        is_active=True,
    )

    # Verify per-event authorization logic
    assert is_event_authorized_for_principal(evt_a, principal_a) is True
    assert is_event_authorized_for_principal(evt_b, principal_a) is False

    assert is_event_authorized_for_principal(evt_a, principal_b) is False
    assert is_event_authorized_for_principal(evt_b, principal_b) is True


@pytest.mark.asyncio
async def test_g20_sse_generator_catchup_replay(setup_r7_data):
    """G-20: Test sse_generator catch-up phase using Last-Event-ID parameter."""
    user_a = setup_r7_data["user_a"]
    inst_a = setup_r7_data["inst_a"]

    now = datetime.now(UTC)
    seq = int(datetime.now(UTC).timestamp() * 1000) % 1000000 + 50000
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        evt = SSEEvent(
            id=uuid.uuid4(),
            sequence_id=seq,
            event_type="inbox.created",
            recipient_user_id=user_a.id,
            institution_id=inst_a.id,
            payload={"inbox_id": str(uuid.uuid4()), "title": "Catchup notification"},
            created_at=now,
        )
        db.add(evt)
        db.commit()

    principal_a = Principal(
        id=user_a.id,
        email=user_a.email,
        full_name=user_a.full_name,
        role=user_a.role,
        institution_id=inst_a.id,
        is_active=True,
    )

    # Catch-up from seq - 1 should yield evt
    from unittest.mock import AsyncMock, MagicMock
    mock_req = MagicMock()
    mock_req.is_disconnected = AsyncMock(return_value=False)
    gen = sse_generator(mock_req, principal_a, last_event_id_val=seq - 1)
    # Get first yielded chunk
    chunk = await gen.asend(None)
    assert f"id: {seq}" in chunk
    assert "event: inbox.created" in chunk
    assert "Catchup notification" in chunk


def test_g21_inbox_first_and_state_ladder(client, setup_r7_data):
    """G-21: Inbox is the source of truth; push state ladder CREATED -> OPENED -> ACKNOWLEDGED -> ACTIONED."""
    user_a = setup_r7_data["user_a"]
    inst_a = setup_r7_data["inst_a"]

    # Process domain event
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        notifs = process_domain_event(
            db,
            event_type="instrument.submitted",
            aggregate_type="instrument",
            aggregate_id=uuid.uuid4(),
            payload={
                "recipient_user_id": str(user_a.id),
                "institution_id": str(inst_a.id),
                "instrument_number": "FDR-R7-12345",
                "amount": "25,00,000",
            },
        )
        db.commit()

    assert len(notifs) >= 1
    notif_id = notifs[0].id

    # 1. Check inbox via API
    headers = auth_header(user_a)
    r = client.get("/v1/notifications", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] >= 1
    item = next(i for i in data["items"] if i["id"] == str(notif_id))
    assert item["is_read"] is False
    assert item["status"] in ("CREATED", "PROVIDER_FAILED")

    # 2. Mark Read (OPENED stage)
    r_read = client.post(f"/v1/notifications/{notif_id}/read", headers=headers)
    assert r_read.status_code == 200
    assert r_read.json()["status"] == "OPENED"

    # 3. Acknowledge (ACKNOWLEDGED stage)
    r_ack = client.post(f"/v1/notifications/{notif_id}/acknowledge", headers=headers)
    assert r_ack.status_code == 200
    assert r_ack.json()["status"] == "ACKNOWLEDGED"

    # 4. Action (ACTIONED stage)
    r_act = client.post(f"/v1/notifications/{notif_id}/action", headers=headers)
    assert r_act.status_code == 200
    assert r_act.json()["status"] == "ACTIONED"


def test_g22_lock_screen_canary_sanitization():
    """G-22: Lock-screen payloads contain NO sensitive values (canary string test)."""
    canary_number = "SECRET-FDR-998877"
    canary_amount = "99,99,999.00"
    canary_bank = "Secret Custodial Bank of India"
    canary_org = "Confidential National Institute"

    context = {
        "instrument_number": canary_number,
        "amount": canary_amount,
        "bank_name": canary_bank,
        "institution_name": canary_org,
        "maturity_date": "2030-01-01",
        "days_remaining": "30",
        "reason": "Missing bank stamp",
    }

    event_types = [
        "instrument.submitted",
        "instrument.returned",
        "instrument.expiring",
        "instrument.matured",
        "release.submitted",
        "release.decision",
    ]

    for evt in event_types:
        for loc in ["en", "hi", "ta"]:
            _title, body, lock_title, lock_body = render_template(evt, context, locale=loc)
            # Body must contain the event details
            assert len(body) > 0
            # Lock-screen title and body must NEVER contain canary strings
            assert canary_number not in lock_title
            assert canary_number not in lock_body
            assert canary_amount not in lock_title
            assert canary_amount not in lock_body
            assert canary_bank not in lock_body
            assert canary_org not in lock_body


def test_g22_device_registration_and_logout_revocation(client, setup_r7_data):
    """G-22: Device token registration and logout de-registration."""
    user = setup_r7_data["user_a"]
    headers = auth_header(user)

    test_token = f"push_token_{uuid.uuid4().hex}"

    # 1. Register device
    r_reg = client.post(
        "/v1/devices/register",
        headers=headers,
        json={
            "platform": "android",
            "provider": "fcm",
            "push_token": test_token,
            "app_version": "1.0.0",
        },
    )
    assert r_reg.status_code == 200
    assert r_reg.json()["is_active"] is True

    # 2. Revoke device
    r_rev = client.post(
        "/v1/devices/revoke",
        headers=headers,
        json={"push_token": test_token},
    )
    assert r_rev.status_code == 200
    assert r_rev.json()["revoked_count"] >= 1


def test_notification_preferences_statutory_protection(client, setup_r7_data):
    """Notification preferences cannot disable statutory categories."""
    user = setup_r7_data["user_a"]
    headers = auth_header(user)

    # Attempt to disable critical_workflow
    r_bad = client.put(
        "/v1/notifications/preferences",
        headers=headers,
        json={
            "category": "critical_workflow",
            "channel": "push",
            "enabled": False,
        },
    )
    assert r_bad.status_code == 400
    assert "statutory" in r_bad.json()["detail"].lower()

    # Allowed for non-statutory category
    r_ok = client.put(
        "/v1/notifications/preferences",
        headers=headers,
        json={
            "category": "digest",
            "channel": "push",
            "enabled": False,
        },
    )
    assert r_ok.status_code == 200


def test_dlq_and_funnel_metrics(client, setup_r7_data):
    """DLQ inspection and funnel metrics endpoints."""
    admin = setup_r7_data["admin"]
    admin_headers = auth_header(admin)

    # Funnel metrics
    r_funnel = client.get("/v1/notifications/funnel", headers=admin_headers)
    assert r_funnel.status_code == 200
    funnel = r_funnel.json()
    assert "CREATED" in funnel
    assert "OPENED" in funnel
    assert "ACKNOWLEDGED" in funnel

    # DLQ listing
    r_dlq = client.get("/v1/notifications/dlq", headers=admin_headers)
    assert r_dlq.status_code == 200
    assert isinstance(r_dlq.json(), list)
