import uuid
from datetime import timedelta

from app.models import Institution, Instrument, Reminder
from app.models.enums import InstrumentStatus, InstrumentType
from app.reminders.scheduler import run_scheduler


def _make_instrument(
    db_session, clock, *, days_to_maturity: int, status=InstrumentStatus.ACTIVE
):
    inst = Institution(
        aicte_code=f"SCH-{uuid.uuid4().hex[:8]}", name="Scheduler Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    as_of = clock.now()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-SCH-{uuid.uuid4().hex[:6]}",
        amount=500000,
        status=status,
        maturity_date=as_of + timedelta(days=days_to_maturity),
    )
    db_session.add(instrument)
    db_session.flush()
    return instrument


def test_far_future_maturity_creates_no_reminders(db_session, clock):
    instrument = _make_instrument(db_session, clock, days_to_maturity=200)
    result = run_scheduler(db_session, clock)
    assert instrument.id not in [r.instrument_id for r in result.reminders_created]


def test_within_90_days_creates_t90_reminder_and_transitions_to_expiring(
    db_session, clock
):
    instrument = _make_instrument(db_session, clock, days_to_maturity=85)
    result = run_scheduler(db_session, clock)
    windows = {
        r.window for r in result.reminders_created if r.instrument_id == instrument.id
    }
    assert "T-90" in windows
    assert instrument.status == InstrumentStatus.EXPIRING


def test_past_maturity_transitions_to_matured_and_creates_all_windows(
    db_session, clock
):
    instrument = _make_instrument(
        db_session, clock, days_to_maturity=-1, status=InstrumentStatus.EXPIRING
    )
    result = run_scheduler(db_session, clock)
    windows = {
        r.window for r in result.reminders_created if r.instrument_id == instrument.id
    }
    assert windows == {"T-90", "T-60", "T-30", "T-7", "T-0"}
    assert instrument.status == InstrumentStatus.MATURED


def test_scheduler_is_idempotent_across_runs(db_session, clock):
    instrument = _make_instrument(db_session, clock, days_to_maturity=85)
    run_scheduler(db_session, clock)
    second_result = run_scheduler(db_session, clock)
    assert instrument.id not in [
        r.instrument_id for r in second_result.reminders_created
    ]

    from sqlalchemy import select

    rows = (
        db_session.execute(
            select(Reminder).where(Reminder.instrument_id == instrument.id)
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1  # exactly one T-90 reminder, not duplicated


def test_clock_plus_300_days_matures_a_fresh_instrument(db_session, clock):
    instrument = _make_instrument(db_session, clock, days_to_maturity=200)
    run_scheduler(db_session, clock)
    assert instrument.status == InstrumentStatus.ACTIVE  # not yet due

    clock.advance(days=300)
    result = run_scheduler(db_session, clock)
    assert instrument.status == InstrumentStatus.MATURED
    windows = {
        r.window for r in result.reminders_created if r.instrument_id == instrument.id
    }
    assert windows == {"T-90", "T-60", "T-30", "T-7", "T-0"}
