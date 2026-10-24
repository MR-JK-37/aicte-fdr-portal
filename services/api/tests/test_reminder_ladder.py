import uuid
from datetime import datetime, timedelta

import httpx
import pytest

from app.models import AppUser, Institution, Instrument, Reminder
from app.models.enums import AppRole, InstrumentStatus, InstrumentType
from app.reminders.ladder import (
    LADDER_STEPS,
    _in_quiet_hours,
    acknowledge_reminder,
    advance_ladder,
)


def _make_reminder_with_contact(
    db_session, clock, *, quiet_hours_start=21, quiet_hours_end=8
):
    inst = Institution(
        aicte_code=f"LAD-{uuid.uuid4().hex[:8]}", name="Ladder Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-LAD-{uuid.uuid4().hex[:6]}",
        amount=500000,
        status=InstrumentStatus.EXPIRING,
        maturity_date=clock.now() + timedelta(days=5),
    )
    db_session.add(instrument)
    contact = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"kc-{uuid.uuid4().hex[:8]}",
        email=f"contact-{uuid.uuid4().hex[:8]}@example.test",
        full_name="Institution Contact",
        role=AppRole.INSTITUTION_SUBMITTER,
        preferred_language="en",
        quiet_hours_start=quiet_hours_start,
        quiet_hours_end=quiet_hours_end,
    )
    db_session.add(contact)
    db_session.flush()
    reminder = Reminder(
        institution_id=inst.id,
        instrument_id=instrument.id,
        window="T-7",
        channel="in_app",
        scheduled_for=clock.now(),
        status="pending",
    )
    db_session.add(reminder)
    db_session.flush()
    return instrument, contact, reminder


def test_first_call_sends_in_app_step(db_session, clock):
    _, _, reminder = _make_reminder_with_contact(db_session, clock)
    result = advance_ladder(db_session, reminder, clock)
    assert result.step == "in_app"
    assert result.sent is True
    assert reminder.ladder_step == 0


def test_does_not_escalate_before_delay_elapses(db_session, clock):
    _, _, reminder = _make_reminder_with_contact(db_session, clock)
    advance_ladder(db_session, reminder, clock)  # in_app
    again = advance_ladder(
        db_session, reminder, clock
    )  # same clock time, delay not elapsed
    assert again is None
    assert reminder.ladder_step == 0


def test_escalates_to_push_after_delay(db_session, clock):
    _, _, reminder = _make_reminder_with_contact(
        db_session, clock, quiet_hours_start=0, quiet_hours_end=0
    )
    advance_ladder(db_session, reminder, clock)  # in_app
    clock.advance(days=2)
    result = advance_ladder(db_session, reminder, clock)
    assert result.step == "push"
    assert reminder.ladder_step == 1
    # No Firebase project configured in this environment — must fail
    # closed with a clear reason, not silently pretend to send.
    assert result.sent is False
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" in result.reason


def test_push_skipped_during_quiet_hours(db_session, clock):
    now_hour = clock.now().hour
    # A one-hour quiet window starting at the current hour, so the push
    # step (sent ~2 days later, same hour-of-day) lands inside it.
    start = now_hour
    end = (now_hour + 1) % 24
    _, _, reminder = _make_reminder_with_contact(
        db_session, clock, quiet_hours_start=start, quiet_hours_end=end
    )
    advance_ladder(db_session, reminder, clock)
    clock.advance(days=2)
    result = advance_ladder(db_session, reminder, clock)
    assert result.step == "push"
    assert result.sent is False
    assert result.reason == "quiet hours"
    # ladder_step tracks which step we're AT, not whether it delivered —
    # quiet hours suppress the send, not the step pointer (same design
    # the full-ladder test below relies on to progress through every
    # step name regardless of individual delivery success).
    assert reminder.ladder_step == LADDER_STEPS.index("push")


def test_full_ladder_reaches_regulation_bureau_with_clock_plus_300_days(
    db_session, clock
):
    from app.models import Escalation

    _, _, reminder = _make_reminder_with_contact(
        db_session, clock, quiet_hours_start=0, quiet_hours_end=0
    )
    seen_steps = []
    for _ in range(len(LADDER_STEPS) + 2):
        clock.advance(days=300)
        result = advance_ladder(db_session, reminder, clock)
        if result is not None:
            seen_steps.append(result.step)

    assert seen_steps == LADDER_STEPS
    assert reminder.ladder_step == len(LADDER_STEPS) - 1

    from sqlalchemy import select

    escalation = db_session.execute(
        select(Escalation).where(Escalation.instrument_id == reminder.instrument_id)
    ).scalar_one_or_none()
    assert escalation is not None
    assert escalation.escalated_to == "Regulation Bureau"

    # Terminal step — further calls are no-ops, not errors.
    assert advance_ladder(db_session, reminder, clock) is None


def test_acknowledge_stops_further_escalation(db_session, clock):
    _, _, reminder = _make_reminder_with_contact(db_session, clock)
    advance_ladder(db_session, reminder, clock)
    acknowledge_reminder(db_session, reminder, clock)
    clock.advance(days=300)
    assert advance_ladder(db_session, reminder, clock) is None
    assert reminder.ladder_step == 0


def test_email_step_sends_a_real_smtp_message_caught_by_mailpit(db_session, clock):
    _, contact, reminder = _make_reminder_with_contact(db_session, clock)
    # Walk the ladder up to (and including) the email step.
    advance_ladder(db_session, reminder, clock)  # in_app
    clock.advance(days=2)
    advance_ladder(db_session, reminder, clock)  # push
    clock.advance(days=2)
    result = advance_ladder(db_session, reminder, clock)  # email
    assert result.step == "email"
    assert result.sent is True

    try:
        resp = httpx.get("http://localhost:8025/api/v1/messages", timeout=5)
    except httpx.ConnectError:
        pytest.skip("Mailpit not reachable from this environment")
    resp.raise_for_status()
    messages = resp.json()["messages"]
    assert any(m["To"][0]["Address"] == contact.email for m in messages)


def test_pstn_whatsapp_step_is_simulated_by_default(db_session, clock):
    _, _, reminder = _make_reminder_with_contact(
        db_session, clock, quiet_hours_start=0, quiet_hours_end=0
    )
    advance_ladder(db_session, reminder, clock)  # in_app
    for _ in range(2):
        clock.advance(days=2)
        advance_ladder(db_session, reminder, clock)  # push, email
    clock.advance(days=2)
    result = advance_ladder(db_session, reminder, clock)  # pstn_whatsapp
    assert result.step == "pstn_whatsapp"
    assert result.sent is False
    assert "SIMULATED" in result.reason


def test_zero_width_quiet_window_means_never_quiet():
    user = AppUser(
        keycloak_sub="x",
        email="x@example.test",
        full_name="x",
        role=AppRole.INSTITUTION_SUBMITTER,
        quiet_hours_start=5,
        quiet_hours_end=5,
    )
    for hour in range(24):
        assert _in_quiet_hours(user, datetime(2026, 1, 1, hour)) is False


def test_non_wrapping_quiet_window():
    user = AppUser(
        keycloak_sub="x",
        email="x@example.test",
        full_name="x",
        role=AppRole.INSTITUTION_SUBMITTER,
        quiet_hours_start=9,
        quiet_hours_end=17,
    )
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 9)) is True
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 16)) is True
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 17)) is False
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 8)) is False


def test_wrapping_quiet_window_past_midnight():
    user = AppUser(
        keycloak_sub="x",
        email="x@example.test",
        full_name="x",
        role=AppRole.INSTITUTION_SUBMITTER,
        quiet_hours_start=21,
        quiet_hours_end=8,
    )
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 22)) is True
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 2)) is True
    assert _in_quiet_hours(user, datetime(2026, 1, 1, 12)) is False
