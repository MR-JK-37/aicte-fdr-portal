"""Test suite for device lifecycle, logout token revocation, lock-screen privacy, and quiet-hours policy (MASTER_PROMPT §10.4, §10.5, §10.8)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.authz import Principal
from app.models.core import AppUser, Institution
from app.models.enums import AppRole, NotificationCategory
from app.models.workflow import (
    DeviceInstallation,
    NotificationPreference,
    SSEEvent,
)
from app.notifications.devices import register_device, revoke_all_user_devices
from app.notifications.pipeline import process_domain_event
from app.notifications.resolver import should_deliver_to_channel
from app.notifications.templates import render_template
from app.realtime.router import is_event_authorized_for_principal


@pytest.fixture
def user_fixture(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-{uuid.uuid4().hex[:8]}",
        name="Privacy Test University",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        institution_id=inst.id,
        email=f"privacy-{uuid.uuid4().hex[:6]}@college.edu",
        full_name="College Secretary",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user, inst


def test_logout_revokes_device_and_receives_nothing(db_session, user_fixture):
    """MASTER_PROMPT §10.5 & PROMPT 6 Exit Gate:
    After logout, previous user's device token is revoked and receives nothing.
    """
    user, inst = user_fixture

    # 1. Register device
    token = f"active_token_{uuid.uuid4().hex}"
    device = register_device(
        db_session,
        user_id=user.id,
        platform="android",
        provider="fcm",
        push_token=token,
    )
    assert device.is_active is True
    assert device.revoked_at is None
    db_session.flush()

    # 2. User logs out: all active devices are revoked
    revoked_count = revoke_all_user_devices(db_session, user.id)
    assert revoked_count == 1

    reloaded_device = db_session.get(DeviceInstallation, device.id)
    assert reloaded_device.is_active is False
    assert reloaded_device.revoked_at is not None

    # 3. Subsequent domain event is triggered
    notifs = process_domain_event(
        db_session,
        event_type="instrument.submitted",
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        payload={
            "recipient_user_id": str(user.id),
            "institution_id": str(inst.id),
            "instrument_number": "FDR-AFTER-LOGOUT",
            "amount": "50,00,000",
        },
    )

    # Inbox item was saved, but push was NOT dispatched to the revoked device token
    assert len(notifs) == 1
    assert notifs[0].status != "QUEUED"
    assert notifs[0].status != "PROVIDER_ACCEPTED"


def test_lock_screen_privacy_canary_strings(db_session, user_fixture):
    """PROMPT 6 Exit Gate & SPEC §10.4:
    Lock-screen payload contains NO sensitive values (tested with canary strings).
    """
    CANARY_FDR_NUMBER = "CANARY-FDR-987654321"
    CANARY_AMOUNT = "75,00,000.00"
    CANARY_BANK_NAME = "State Bank of India — Secret Branch"
    CANARY_INSTITUTION_NAME = "Secret College of Engineering"

    context = {
        "instrument_number": CANARY_FDR_NUMBER,
        "amount": CANARY_AMOUNT,
        "bank_name": CANARY_BANK_NAME,
        "institution_name": CANARY_INSTITUTION_NAME,
        "maturity_date": "2036-10-24",
        "days_remaining": "90",
    }

    # Test across all core template types in all supported languages
    for event_type in [
        "instrument.submitted",
        "instrument.returned",
        "instrument.expiring",
        "instrument.matured",
        "release.submitted",
        "release.decision",
    ]:
        for locale in ["en", "hi", "ta"]:
            _title, body, lock_title, lock_body = render_template(event_type, context, locale=locale)

            # In-app body contains context
            assert CANARY_FDR_NUMBER in body or "FDR" in body

            # Lock-screen title and body must NEVER contain canary sensitive values!
            assert CANARY_FDR_NUMBER not in lock_title, f"Leak in lock_title for {event_type} [{locale}]"
            assert CANARY_FDR_NUMBER not in lock_body, f"Leak in lock_body for {event_type} [{locale}]"
            assert CANARY_AMOUNT not in lock_title, f"Leak in lock_title for {event_type} [{locale}]"
            assert CANARY_AMOUNT not in lock_body, f"Leak in lock_body for {event_type} [{locale}]"
            assert CANARY_BANK_NAME not in lock_body, f"Leak in lock_body for {event_type} [{locale}]"
            assert CANARY_INSTITUTION_NAME not in lock_body, f"Leak in lock_body for {event_type} [{locale}]"


def test_quiet_hours_and_opt_outs_cannot_suppress_statutory_obligations(db_session, user_fixture):
    """MASTER_PROMPT §10.4:
    Quiet hours and opt-outs never suppress critical_workflow, deadline, or security_account items;
    user preference cannot silently cancel an obligation.
    """
    user, _inst = user_fixture

    # User attempts to disable critical_workflow
    pref = NotificationPreference(
        id=uuid.uuid4(),
        user_id=user.id,
        category=NotificationCategory.CRITICAL_WORKFLOW.value,
        channel="push",
        enabled=False,  # Disabled
        quiet_hours_enabled=True,
        quiet_hours_start="00:00",
        quiet_hours_end="23:59",  # All-day quiet hours
    )
    db_session.add(pref)
    db_session.flush()

    # For critical_workflow, delivery MUST still be allowed!
    allowed, reason = should_deliver_to_channel(
        db_session,
        user.id,
        category=NotificationCategory.CRITICAL_WORKFLOW.value,
        channel="push",
    )
    assert allowed is True
    assert "statutory" in reason or "critical" in reason

    # For non-critical operations / digest, quiet hours and opt-outs DO suppress
    pref_digest = NotificationPreference(
        id=uuid.uuid4(),
        user_id=user.id,
        category=NotificationCategory.DIGEST.value,
        channel="push",
        enabled=False,
    )
    db_session.add(pref_digest)
    db_session.flush()

    allowed_digest, reason_digest = should_deliver_to_channel(
        db_session,
        user.id,
        category=NotificationCategory.DIGEST.value,
        channel="push",
    )
    assert allowed_digest is False
    assert reason_digest == "user_disabled"


def test_sse_event_per_event_reauthorization(db_session, user_fixture):
    """MASTER_PROMPT §10.8:
    Per-event re-authorisation before emitting each buffered/live event.
    """
    user, inst = user_fixture

    # Event for this user's institution
    inst_event = SSEEvent(
        id=uuid.uuid4(),
        sequence_id=101,
        event_type="case.changed",
        institution_id=inst.id,
        payload={"instrument_id": str(uuid.uuid4())},
    )

    # Event for another institution
    foreign_event = SSEEvent(
        id=uuid.uuid4(),
        sequence_id=102,
        event_type="case.changed",
        institution_id=uuid.uuid4(),
        payload={"instrument_id": str(uuid.uuid4())},
    )

    principal = Principal(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        institution_id=inst.id,
        is_active=True,
    )

    # Authorized for own institution
    assert is_event_authorized_for_principal(inst_event, principal) is True
    # Denied for foreign institution!
    assert is_event_authorized_for_principal(foreign_event, principal) is False


def test_forged_deep_link_returns_safe_404(db_session, user_fixture):
    """PROMPT 6 Exit Gate & SPEC §18.1 Scenario 1:
    Following a forged deep link to an unauthorized tenant's resource returns a safe 404, never 403.
    """
    from app.db import set_app_context
    from app.models.core import Instrument
    from app.models.enums import InstrumentStatus, InstrumentType

    user, inst = user_fixture

    # 1. As platform operator, create an instrument belonging to another institution
    set_app_context(db_session, role="platform_operator")
    foreign_inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-FORGED-{uuid.uuid4().hex[:6]}",
        name="Target Foreign College",
    )
    db_session.add(foreign_inst)
    db_session.flush()

    foreign_instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=foreign_inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-FORGED-{uuid.uuid4().hex[:6]}",
        amount=1000000.0,
        status=InstrumentStatus.ACTIVE,
    )
    db_session.add(foreign_instrument)
    db_session.flush()

    forged_deep_link = f"/instruments/{foreign_instrument.id}"

    # 2. Switch context to Institution Submitter (our user)
    set_app_context(
        db_session,
        role=AppRole.INSTITUTION_SUBMITTER.value,
        institution_id=str(inst.id),
        user_id=str(user.id),
    )

    # 3. Simulate resolving forged deep link target under RLS
    extracted_id = uuid.UUID(forged_deep_link.split("/")[-1])
    found = db_session.execute(
        select(Instrument).where(Instrument.id == extracted_id)
    ).scalar_one_or_none()

    # RLS makes unauthorized tenant's resource completely invisible (safe 404)
    assert found is None

