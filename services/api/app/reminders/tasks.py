"""Reminder-ladder cadence task.

Previously a Celery task on Celery Beat's 15-minute cron
(app/celery_app.py, removed). This phase replaces that mechanism with
the Postgres-outbox pattern's DB-leased scheduler loop
(app.outbox.scheduler.run_forever), per MASTER_PROMPT §4.2 ("Celery/
Valkey optional later; do not add unless needed") and §10.2. This is
now a plain function the scheduler loop calls directly on its own
cadence — no broker, no Beat process.

Runs the scheduler (creates due Reminder rows against the real clock)
then advances the ladder for every unacknowledged reminder.
"""

from sqlalchemy import select, text

from app.clock import RealClock
from app.db import SessionLocal
from app.models.core import Reminder
from app.reminders.ladder import advance_ladder
from app.reminders.scheduler import run_scheduler


def process_reminder_ladder() -> dict:
    session = SessionLocal()
    # The scheduler loop runs in production — the real clock is the
    # only clock allowed here (CLAUDE.md non-negotiable #10).
    clock = RealClock()
    try:
        session.execute(text("SELECT set_config('app.role', 'bureau_admin', true)"))

        scheduler_result = run_scheduler(session, clock)

        unacknowledged = (
            session.execute(select(Reminder).where(Reminder.acknowledged_at.is_(None)))
            .scalars()
            .all()
        )
        ladder_results = [advance_ladder(session, r, clock) for r in unacknowledged]
        ladder_results = [r for r in ladder_results if r is not None]

        session.commit()
        return {
            "reminders_created": len(scheduler_result.reminders_created),
            "transitions_applied": scheduler_result.transitions_applied,
            "ladder_steps_executed": len(ladder_results),
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
