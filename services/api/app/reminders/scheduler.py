"""Computes which maturity reminder windows (T-90/60/30/7/0) are due for
each active instrument, against the sim clock, and idempotently creates
the Reminder rows the ladder (ladder.py) then works through. Also drives
the automated ACTIVE->EXPIRING->MATURED lifecycle transitions Phase 3's
`lifecycle.py` built the "system" pseudo-role for.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import sim_clock
from app.lifecycle import apply_transition
from app.models.core import Instrument, Reminder
from app.models.enums import InstrumentStatus

# (window label, days-before-maturity threshold), most-advance-notice first.
WINDOWS: list[tuple[str, int]] = [("T-90", 90), ("T-60", 60), ("T-30", 30), ("T-7", 7), ("T-0", 0)]


@dataclass
class SchedulerResult:
    reminders_created: list[Reminder]
    transitions_applied: int


def _days_remaining(maturity_date: datetime, as_of: datetime) -> int:
    return (maturity_date.date() - as_of.date()).days


def run_scheduler(session: Session) -> SchedulerResult:
    as_of = sim_clock.now(session)
    instruments = session.execute(
        select(Instrument).where(
            Instrument.status.in_([InstrumentStatus.ACTIVE, InstrumentStatus.EXPIRING]),
            Instrument.maturity_date.isnot(None),
        )
    ).scalars().all()

    created: list[Reminder] = []
    transitions = 0

    for instrument in instruments:
        days_remaining = _days_remaining(instrument.maturity_date, as_of)

        if days_remaining <= 0 and instrument.status != InstrumentStatus.MATURED:
            apply_transition(
                session,
                instrument,
                InstrumentStatus.MATURED,
                actor_role="system",
                actor_id=None,
                reason=f"Sim clock reached maturity date (days_remaining={days_remaining})",
            )
            transitions += 1
        elif days_remaining <= 90 and instrument.status == InstrumentStatus.ACTIVE:
            apply_transition(
                session,
                instrument,
                InstrumentStatus.EXPIRING,
                actor_role="system",
                actor_id=None,
                reason=f"Within 90-day maturity window (days_remaining={days_remaining})",
            )
            transitions += 1

        for window_label, threshold_days in WINDOWS:
            if days_remaining > threshold_days:
                continue
            existing = session.execute(
                select(Reminder).where(Reminder.instrument_id == instrument.id, Reminder.window == window_label)
            ).scalar_one_or_none()
            if existing is not None:
                continue
            reminder = Reminder(
                institution_id=instrument.institution_id,
                instrument_id=instrument.id,
                window=window_label,
                channel="in_app",
                scheduled_for=as_of,
                status="pending",
            )
            session.add(reminder)
            created.append(reminder)

    session.flush()
    return SchedulerResult(reminders_created=created, transitions_applied=transitions)
