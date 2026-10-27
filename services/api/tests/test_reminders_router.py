"""HTTP-level tests for GET /v1/reminders and /v1/scheduler/status
(app.reminders.router). No test exercised the actual endpoint before —
it shipped referencing `Reminder.target_date` / `Reminder.days_before`,
neither of which exist on the model (the real columns are
`scheduled_for` / `window`), so every real call 500'd. Regression guard
for that.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution, Instrument, Reminder
from app.models.enums import AppRole, InstrumentStatus, InstrumentType

client = TestClient(app)


@pytest.fixture
def reminder_setup(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"REM-{uuid.uuid4().hex[:6]}",
        name="Institute of Reminder Testing",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-rem-{uuid.uuid4().hex[:8]}",
        email=f"viewer-{uuid.uuid4().hex[:6]}@eng.edu",
        full_name="Institution Viewer",
        role=AppRole.INSTITUTION_VIEWER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        status=InstrumentStatus.EXPIRING,
        instrument_number="REM/TEST/0001",
        amount=3500000,
        maturity_date=datetime.now(UTC) + timedelta(days=45),
    )
    db_session.add(instrument)
    db_session.flush()

    reminder = Reminder(
        id=uuid.uuid4(),
        institution_id=inst.id,
        instrument_id=instrument.id,
        window="T-60",
        channel="in_app",
        scheduled_for=instrument.maturity_date - timedelta(days=60),
        status="pending",
    )
    db_session.add(reminder)
    db_session.commit()
    return inst, user, instrument, reminder


def test_list_reminders_returns_200_not_500(reminder_setup):
    """The actual bug found live: this endpoint 500'd on every call."""
    inst, user, instrument, reminder = reminder_setup
    token = create_access_token(user)

    res = client.get("/v1/reminders", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    row = body[0]
    assert row["id"] == str(reminder.id)
    assert row["instrument_id"] == str(instrument.id)
    assert row["window"] == "T-60"
    assert row["status"] == "pending"
    assert row["channel"] == "in_app"
    assert row["target_date"] is not None


def test_list_reminders_scoped_to_own_institution(db_session, reminder_setup):
    """A viewer from a different institution must not see this reminder."""
    inst, user, instrument, reminder = reminder_setup

    other_inst = Institution(
        id=uuid.uuid4(), aicte_code=f"OTH-{uuid.uuid4().hex[:6]}", name="Other Institute"
    )
    db_session.add(other_inst)
    db_session.flush()
    other_user = AppUser(
        id=uuid.uuid4(),
        institution_id=other_inst.id,
        keycloak_sub=f"sub-oth-{uuid.uuid4().hex[:8]}",
        email=f"other-{uuid.uuid4().hex[:6]}@eng.edu",
        full_name="Other Institution Viewer",
        role=AppRole.INSTITUTION_VIEWER,
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    token = create_access_token(other_user)
    res = client.get("/v1/reminders", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    assert res.json() == []


def test_scheduler_status_reports_no_approved_schedule_by_default(reminder_setup):
    inst, user, instrument, reminder = reminder_setup
    token = create_access_token(user)

    res = client.get("/v1/scheduler/status", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    body = res.json()
    assert body["has_approved_schedule"] is False
    assert body["active_schedule_version"] is None
    assert "no approved" in body["status_alert"].lower()
