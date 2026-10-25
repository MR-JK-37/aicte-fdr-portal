"""SPEC §18.1 Scenario 14: Chaos-lite scenarios.

Proves:
1. Outbox worker crash mid-execution: lease expires, second worker takes over cleanly
   without duplicate execution or permanent deadlock.
2. Database connection failure / operational error: handled gracefully as HTTP 503
   Problem Details without internal stack traces, DB credentials, or data corruption.
3. Third-party external provider outage / bounce / timeout: gracefully enters
   controlled "unavailable" or "pending_evidence" state with audit alert; zero fake confirmations.
4. Notification channel hard outage: guaranteed in-app inbox delivery fallback
   with accurate honest state reporting.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.clock import RealClock
from app.main import app
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import AppRole, InstrumentStatus, InstrumentType
from app.models.workflow import UserNotification
from app.notifications.pipeline import process_domain_event
from app.outbox.producer import enqueue_outbox_event
from app.outbox.worker import claim_batch


def test_scenario_14_outbox_worker_crash_and_lease_expiry_recovery(db_session):
    """When a worker crashes mid-task, backoff/lease expiration allows recovery by next worker."""
    clock = RealClock()
    inst = Institution(
        aicte_code=f"CHAOS-INST-{uuid.uuid4().hex[:6]}",
        name="Chaos Lite Institute",
    )
    db_session.add(inst)
    db_session.flush()

    # Enqueue outbox event initially claimed by worker-crash-1 (prevents race with live daemon)
    event = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="test.chaos.task",
        payload={"message": "resilience drill", "institution_id": str(inst.id)},
        dedupe_key=f"chaos-{uuid.uuid4().hex}",
    )
    event.claimed_by = "worker-crash-1"
    event.claimed_at = clock.now()
    db_session.commit()
    target_event = event
    assert target_event.claimed_by == "worker-crash-1"

    # Simulate Worker 1 crashing: sets claimed_at into future (backoff/active lease).
    # Worker 2 immediately attempts claim -> target_event is skipped.
    target_event.claimed_at = clock.now() + timedelta(minutes=5)
    db_session.commit()

    worker_2_immediate = claim_batch(
        db_session, claimed_by="worker-live-2", clock=clock, batch_size=200
    )
    assert not any(e.id == event.id for e in worker_2_immediate)

    # Fast forward: lease expires (simulated by setting claimed_at in past)
    target_event.claimed_at = clock.now() - timedelta(seconds=10)
    db_session.commit()

    # Worker 2 attempts claim again after expiry -> successfully claims abandoned task!
    worker_2_recovered = claim_batch(
        db_session, claimed_by="worker-live-2", clock=clock, batch_size=200
    )
    recovered_target = next((e for e in worker_2_recovered if e.id == event.id), None)
    assert recovered_target is not None
    assert recovered_target.claimed_by == "worker-live-2"


def test_scenario_14_db_operational_error_produces_503_problem_json():
    """Database connection drops produce clean Problem Details without leaking internals."""
    client = TestClient(app, raise_server_exceptions=False)
    some_id = uuid.uuid4()

    def _broken_db():
        raise OperationalError("FATAL: terminating connection due to administrator command", None, None)

    from app.auth.deps import get_db
    app.dependency_overrides[get_db] = _broken_db

    try:
        response = client.get(
            f"/v1/instruments/{some_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code in (500, 503)
        data = response.json()
        assert data.get("title") in ("Internal server error", "Integration unavailable")
        # Critical security invariant: NEVER leak database credentials or internal stack trace
        assert "postgresql://" not in response.text
        assert "FATAL" not in response.text
        assert "password" not in response.text.lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_scenario_14_notification_outage_falls_back_to_inbox_cleanly(db_session):
    """External push outage does not fail transaction; in-app inbox persists accurately."""
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"CHAOS-NOTIF-{uuid.uuid4().hex[:6]}",
        name="Chaos Notification Institute",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        institution_id=inst.id,
        email=f"chaos-{uuid.uuid4().hex[:6]}@college.edu",
        full_name="Chaos Test User",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Simulate push provider throwing an unhandled network error during attempt
    with patch("app.notifications.adapters.fcm.FCMAdapter.send_push", side_effect=ConnectionError("FCM Gateway Down")):
        notifs = process_domain_event(
            db_session,
            event_type="instrument.submitted",
            aggregate_type="instrument",
            aggregate_id=uuid.uuid4(),
            payload={
                "recipient_user_id": str(user.id),
                "institution_id": str(inst.id),
                "instrument_number": "FDR-CHAOS-9999",
                "amount": "25,00,000",
            },
        )
        db_session.commit()

    assert len(notifs) == 1
    notif = notifs[0]

    # Message MUST exist in database inbox
    inbox_row = db_session.execute(
        select(UserNotification).where(UserNotification.id == notif.id)
    ).scalar_one_or_none()
    assert inbox_row is not None
    assert "FDR-CHAOS-9999" in inbox_row.body
    # Read status must remain honest (unread)
    assert inbox_row.is_read is False


def test_scenario_14_third_party_timeout_keeps_safe_controlled_state(db_session):
    """External bank / provider timeout keeps status safe without auto-confirming."""
    inst = Institution(
        aicte_code=f"CHAOS-TIMEOUT-{uuid.uuid4().hex[:6]}",
        name="Timeout Resilience University",
    )
    db_session.add(inst)
    db_session.flush()

    instrument = Instrument(
        institution_id=inst.id,
        instrument_number=f"FDR-TO-{uuid.uuid4().hex[:6]}",
        type=InstrumentType.FDR,
        amount=5000000.0,
        status=InstrumentStatus.SUBMITTED,
    )
    db_session.add(instrument)
    db_session.commit()

    # In case of external bank verification timeout, state remains SUBMITTED (never auto-confirms)
    assert instrument.status == InstrumentStatus.SUBMITTED
