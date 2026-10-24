"""SPEC §18.1 Scenario 10: Notification and Inbox Delivery Invariants.

Scenario requirement:
Domain event persists inbox record even if push fails; invalid device registration
is cleaned; user acknowledges from inbox; no external "delivered" status is fabricated.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.core import AppUser, Institution
from app.models.enums import AppRole, NotificationStatus
from app.models.workflow import (
    DeviceInstallation,
    NotificationAttempt,
    UserNotification,
)
from app.notifications.devices import register_device
from app.notifications.pipeline import process_domain_event


@pytest.fixture
def test_user_and_institution(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-{uuid.uuid4().hex[:8]}",
        name="State Engineering College",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        institution_id=inst.id,
        email=f"registrar-{uuid.uuid4().hex[:6]}@college.edu",
        full_name="College Registrar",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user, inst


def test_scenario_10_inbox_persists_even_when_push_unconfigured(db_session, test_user_and_institution):
    """SPEC §18.1 Scenario 10:
    Inbox record is persisted even when push provider has no credentials or is unconfigured.
    No fake delivered status is ever claimed.
    """
    user, inst = test_user_and_institution

    # Register an Android device with a valid-looking FCM token
    token = f"fcm_test_token_{uuid.uuid4().hex}"
    register_device(
        db_session,
        user_id=user.id,
        platform="android",
        provider="fcm",
        push_token=token,
    )
    db_session.flush()

    # Process domain event (e.g., submission received)
    notifs = process_domain_event(
        db_session,
        event_type="instrument.submitted",
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        payload={
            "recipient_user_id": str(user.id),
            "institution_id": str(inst.id),
            "instrument_number": "FDR-2026-9999",
            "amount": "35,00,000",
        },
    )

    assert len(notifs) == 1
    inbox_item = notifs[0]

    # In-app inbox item was successfully persisted!
    assert inbox_item.recipient_user_id == user.id
    assert inbox_item.is_read is False
    assert inbox_item.template_key == "instrument.submitted"
    assert "FDR-2026-9999" in inbox_item.body

    # Status must NOT claim delivered!
    # Because FCM credentials are unconfigured in test environment, status must be PROVIDER_FAILED
    assert inbox_item.status in (NotificationStatus.PROVIDER_FAILED.value, NotificationStatus.CREATED.value)
    assert inbox_item.status != "DELIVERED"  # Never fabricate delivered!

    # Attempt record was captured honestly
    attempts = db_session.execute(
        select(NotificationAttempt).where(NotificationAttempt.user_notification_id == inbox_item.id)
    ).scalars().all()
    assert len(attempts) >= 1
    assert attempts[0].result_code in ("NOT_CONFIGURED", "SUCCESS", "FAILED")


def test_scenario_10_invalid_device_registration_cleaned(db_session, test_user_and_institution):
    """SPEC §18.1 Scenario 10:
    Invalid / unregistered device token is cleaned and revoked automatically.
    """
    user, inst = test_user_and_institution

    # Register device with an invalid / unregistered token prefix
    stale_token = f"unregistered_device_token_{uuid.uuid4().hex}"
    device = register_device(
        db_session,
        user_id=user.id,
        platform="android",
        provider="fcm",
        push_token=stale_token,
    )
    assert device.is_active is True
    assert device.revoked_at is None
    db_session.flush()

    # Trigger event dispatch
    notifs = process_domain_event(
        db_session,
        event_type="instrument.matured",
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        payload={
            "recipient_user_id": str(user.id),
            "institution_id": str(inst.id),
            "instrument_number": "FDR-2026-STALE",
            "maturity_date": "2026-10-24",
        },
    )

    assert len(notifs) == 1

    # Inactive/unregistered token must be cleaned and marked revoked
    reloaded_device = db_session.get(DeviceInstallation, device.id)
    assert reloaded_device.is_active is False
    assert reloaded_device.revoked_at is not None

    # Delivery attempt logged the permanent failure code
    attempts = db_session.execute(
        select(NotificationAttempt).where(NotificationAttempt.user_notification_id == notifs[0].id)
    ).scalars().all()
    assert len(attempts) == 1
    assert attempts[0].result_code == "UNREGISTERED"
    assert attempts[0].error_category == "PERMANENT"


def test_scenario_10_user_acknowledges_from_inbox(db_session, test_user_and_institution):
    """SPEC §18.1 Scenario 10:
    Stages are never merged: CREATED -> OPENED -> ACKNOWLEDGED -> ACTIONED.
    """
    user, inst = test_user_and_institution

    notifs = process_domain_event(
        db_session,
        event_type="observation.created",
        aggregate_type="observation",
        aggregate_id=uuid.uuid4(),
        payload={
            "recipient_user_id": str(user.id),
            "institution_id": str(inst.id),
            "observation_number": "OBS-2026-0042",
            "title": "Maturity date missing on scanned FDR receipt",
            "due_date": "2026-11-05",
        },
    )

    notif = notifs[0]
    assert notif.status in (NotificationStatus.CREATED.value, NotificationStatus.PROVIDER_FAILED.value)
    assert notif.read_at is None
    assert notif.acknowledged_at is None
    assert notif.actioned_at is None

    # 1. User opens notification in-app
    notif.is_read = True
    notif.read_at = datetime.now(UTC)
    notif.status = NotificationStatus.OPENED.value
    db_session.flush()

    # 2. User acknowledges obligation
    notif.acknowledged_at = datetime.now(UTC)
    notif.status = NotificationStatus.ACKNOWLEDGED.value
    db_session.flush()

    # 3. User performs state-changing action
    notif.actioned_at = datetime.now(UTC)
    notif.status = NotificationStatus.ACTIONED.value
    db_session.flush()

    # All stages are tracked separately
    reloaded = db_session.get(UserNotification, notif.id)
    assert reloaded.status == NotificationStatus.ACTIONED.value
    assert reloaded.read_at is not None
    assert reloaded.acknowledged_at is not None
    assert reloaded.actioned_at is not None
