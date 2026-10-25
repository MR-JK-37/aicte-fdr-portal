"""DB-leased singleton scheduler loop — replaces Celery Beat.

Why a Postgres advisory lock and not Celery Beat: MASTER_PROMPT §4.2
picks the Postgres outbox over Celery/Valkey for this phase ("Celery/
Valkey optional later; do not add unless needed"). An advisory lock
(`pg_try_advisory_lock`) held for the lifetime of one worker process's
scheduler loop gives the same "exactly one active scheduler" guarantee
Beat gave, without a second broker/scheduler process: whichever worker
replica acquires the lock runs the loop; every other replica's attempt
to acquire it fails immediately, and that replica just runs its own
outbox-consumer loop (app.outbox.worker) without also scheduling.

The lock is session-scoped (`pg_advisory_lock`/`pg_try_advisory_lock`,
not the `_xact_` variants) and tied to the lifetime of the single
dedicated connection this loop holds open — if that process dies, its
connection drops and Postgres releases the lock automatically, so a
crashed scheduler can never wedge the lease; the next replica to poll
acquires it.

Heartbeat / `scheduler_runs`: MASTER_PROMPT §16's `/readyz` contract and
F-19's "scheduler/worker status" admin view both want a durable
heartbeat to read. No `scheduler_runs` table exists yet — per this
phase's task brief, that table is Phase 4 work (once the reminder engine
proper is built), not something to invent a migration for here. Until
then the heartbeat is only logged (`scheduler.heartbeat`); a future
Phase 4 change should write it into a real `scheduler_runs` table
instead (or in addition).
"""

from __future__ import annotations

import logging
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.reminders.tasks import process_reminder_ladder

logger = logging.getLogger(__name__)

# Arbitrary but fixed 64-bit advisory-lock key. pg_try_advisory_lock
# namespaces purely by this integer process-wide, so it must never
# collide with another subsystem's use of advisory locks in this
# database. Every worker replica must try to lock this exact literal.
SCHEDULER_ADVISORY_LOCK_KEY = (
    0x46445253  # "FDRS" packed into 32 bits, as a human-checkable mnemonic
)

# Celery Beat's old cadence (MASTER_PROMPT §10.2 / app.celery_app, removed).
DEFAULT_INTERVAL_SECONDS = 15 * 60
DEFAULT_POLL_INTERVAL_SECONDS = 5.0


def try_acquire_scheduler_lease(
    session: Session, key: int = SCHEDULER_ADVISORY_LOCK_KEY
) -> bool:
    return bool(
        session.execute(
            text("SELECT pg_try_advisory_lock(:key)"),
            {"key": key},
        ).scalar()
    )


def release_scheduler_lease(
    session: Session, key: int = SCHEDULER_ADVISORY_LOCK_KEY
) -> None:
    session.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})


def run_forever(
    *,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> None:
    """Entry point for the scheduler half of the `worker` docker-compose
    process (see app.outbox.run_worker).

    Holds one dedicated connection for the advisory lock's lifetime and,
    for as long as it holds the lease, runs `process_reminder_ladder` on
    `interval_seconds` cadence. If it never acquires the lease (another
    replica already holds it), it just polls for the lease at
    `poll_interval_seconds` and does nothing else — the outbox-consumer
    loop in the same process keeps running regardless.
    """
    lock_session = SessionLocal()
    have_lease = False
    try:
        while True:
            if not have_lease:
                have_lease = try_acquire_scheduler_lease(lock_session)
                if have_lease:
                    logger.info("scheduler.lease_acquired")
                else:
                    time.sleep(poll_interval_seconds)
                    continue

            started = time.monotonic()
            try:
                result = process_reminder_ladder()
                logger.info("scheduler.heartbeat", extra={"ok": True, **result})
            except Exception:
                logger.exception("scheduler.run_failed")
            elapsed = time.monotonic() - started
            time.sleep(max(0.0, interval_seconds - elapsed))
    finally:
        if have_lease:
            release_scheduler_lease(lock_session)
        lock_session.close()
