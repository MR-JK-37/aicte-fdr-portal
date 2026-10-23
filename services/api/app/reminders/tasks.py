"""Celery task wired into Beat's 15-minute schedule (app/celery_app.py).
Runs the scheduler (creates due Reminder rows against the real clock)
then advances the ladder for every unacknowledged reminder.
"""

from sqlalchemy import select, text

from app.celery_app import celery_app
from app.clock import RealClock
from app.db import SessionLocal
from app.models.core import Reminder
from app.reminders.ladder import advance_ladder
from app.reminders.scheduler import run_scheduler


@celery_app.task(name="app.reminders.tasks.process_reminder_ladder")
def process_reminder_ladder() -> dict:
    session = SessionLocal()
    # Celery Beat runs in production — the real clock is the only clock
    # allowed here (CLAUDE.md non-negotiable #10).
    clock = RealClock()
    try:
        session.execute(text("SELECT set_config('app.role', 'bureau_admin', true)"))

        scheduler_result = run_scheduler(session, clock)

        unacknowledged = session.execute(
            select(Reminder).where(Reminder.acknowledged_at.is_(None))
        ).scalars().all()
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
