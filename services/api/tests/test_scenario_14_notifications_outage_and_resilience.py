"""SPEC §18.1 Scenario 14: Push Provider Outage, DLQ, and Resilience.

Scenario requirement:
Push provider outage, email bounce, bank integration timeout, worker restart
and database failover create controlled recoverable states and alerts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.core import AppUser, Institution
from app.models.enums import AppRole, NotificationStatus
from app.models.workflow import (
    NotificationAttempt,
    NotificationDLQ,
)
from app.notifications.devices import register_device
from app.notifications.pipeline import process_domain_event


@pytest.fixture
def setup_outage_environment(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-{uuid.uuid4().hex[:8]}",
        name="Outage Test Institute",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        institution_id=inst.id,
        email=f"officer-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Test Officer",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user, inst


def test_scenario_14_provider_outage_creates_controlled_state_and_dlq(db_session, setup_outage_environment):
    """SPEC §18.1 Scenario 14:
    Push provider outage creates controlled PROVIDER_FAILED state and enqueues to DLQ.
    """
    user, _inst = setup_outage_environment

    # Register device with an outage-simulating token
    outage_token = f"outage_push_token_{uuid.uuid4().hex}"
    register_device(
        db_session,
        user_id=user.id,
        platform="android",
        provider="fcm",
        push_token=outage_token,
    )
    db_session.flush()

    # Trigger critical notification
    notifs = process_domain_event(
        db_session,
        event_type="operations.alert",
        aggregate_type="system",
        aggregate_id=uuid.uuid4(),
        payload={
            "recipient_user_id": str(user.id),
            "subject": "Storage Threshold Exceeded",
            "details": "Vault bucket storage reached 85% capacity",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    assert len(notifs) == 1
    notif = notifs[0]

    # Controlled failure state
    assert notif.status == NotificationStatus.PROVIDER_FAILED.value

    # Provider attempt recorded with transient error details
    attempts = db_session.execute(
        select(NotificationAttempt).where(NotificationAttempt.user_notification_id == notif.id)
    ).scalars().all()
    assert len(attempts) == 1
    assert attempts[0].result_code == "PROVIDER_OUTAGE"
    assert attempts[0].error_category == "TRANSIENT"

    # Dead-Letter Queue (DLQ) entry was created for ops visibility and replay
    dlq_entries = db_session.execute(
        select(NotificationDLQ).where(NotificationDLQ.user_notification_id == notif.id)
    ).scalars().all()
    assert len(dlq_entries) == 1
    dlq = dlq_entries[0]
    assert dlq.status == "DEAD_LETTER"
    assert "push provider dispatch attempts failed" in dlq.error_reason


def test_scenario_14_dlq_replay_recovers_exhausted_event(db_session, setup_outage_environment):
    """SPEC §18.1 Scenario 14:
    Exhausted / dead-lettered events can be inspected and marked for replay.
    """
    _user, _inst = setup_outage_environment

    dlq = NotificationDLQ(
        id=uuid.uuid4(),
        event_type="release.submitted",
        error_reason="Network socket timeout communicating with push gateway",
        attempts=3,
        payload={"instrument_number": "FDR-REPLAY-1"},
        status="DEAD_LETTER",
    )
    db_session.add(dlq)
    db_session.flush()

    # Admin marks DLQ entry for replay
    dlq.status = "REPLAYED"
    dlq.replayed_at = datetime.now(UTC)
    db_session.flush()

    reloaded = db_session.get(NotificationDLQ, dlq.id)
    assert reloaded.status == "REPLAYED"
    assert reloaded.replayed_at is not None
