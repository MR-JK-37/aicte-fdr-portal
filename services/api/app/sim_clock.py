"""Simulated clock: real wall-clock time plus a stored offset, so a demo
can jump the reminder/escalation ladder forward by simulated days without
actually waiting — per the brief's acceptance test: "sim-clock +300 days
fires the full ladder". Every reminder/escalation time calculation in
app.reminders uses `now()` from here, never `datetime.now()` directly.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import SimClock

SINGLETON_ID = 1


def _get_or_create(session: Session) -> SimClock:
    row = session.get(SimClock, SINGLETON_ID)
    if row is None:
        row = SimClock(id=SINGLETON_ID, offset_seconds=0)
        session.add(row)
        session.flush()
    return row


def now(session: Session) -> datetime:
    row = session.execute(select(SimClock).where(SimClock.id == SINGLETON_ID)).scalar_one_or_none()
    offset = row.offset_seconds if row else 0
    return datetime.now(UTC) + timedelta(seconds=offset)


def advance(session: Session, *, days: int = 0, seconds: int = 0) -> datetime:
    row = _get_or_create(session)
    row.offset_seconds += days * 86400 + seconds
    session.flush()
    return now(session)


def reset(session: Session) -> datetime:
    row = _get_or_create(session)
    row.offset_seconds = 0
    session.flush()
    return now(session)
