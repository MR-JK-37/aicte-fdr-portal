"""Celery app for the worker and beat processes. Lives inside services/api
so tasks have full access to the DB models, RLS-aware sessions, and the
rest of the application — the original services/worker split (Phase 1)
was a minimal standalone Celery project with no access to any of that,
which made it unable to actually implement the Phase 7 reminder/
escalation ladder. Consolidated here; services/worker was removed.
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("fdr_worker", broker=settings.valkey_url, backend=settings.valkey_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# autodiscover_tasks() is lazy and only fires on a real worker's bootstrap
# sequence (verified: calling it, then .finalize(), in a plain script left
# app.reminders.tasks unregistered) — an explicit import is simpler and
# deterministic regardless of how this module gets loaded.
import app.reminders.tasks  # noqa: F401

# Real wall-clock cadence per the brief: "Celery Beat every 15 minutes".
# What counts as "due" inside that task is computed against the real
# clock (app.clock.RealClock) — there is no simulated/time-travel clock
# in production (CLAUDE.md non-negotiable #10).
celery_app.conf.beat_schedule = {
    "process-reminder-ladder-every-15-minutes": {
        "task": "app.reminders.tasks.process_reminder_ladder",
        "schedule": crontab(minute="*/15"),
    },
}


@celery_app.task(name="worker.ping")
def ping() -> str:
    return "pong"
