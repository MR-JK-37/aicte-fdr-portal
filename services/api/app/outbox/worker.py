"""Outbox consumer loop (MASTER_PROMPT §10.2 steps 2-6).

Runs as the `worker` docker-compose process (see
infra/docker/docker-compose.yml and app.outbox.run_worker). Claims
unprocessed rows with `SELECT ... FOR UPDATE SKIP LOCKED` so multiple
worker replicas can run concurrently without double-processing the same
row, dispatches each through the handler registry (app.outbox.handlers),
and on success marks `processed_at`; on failure bumps `attempts` and
`last_error` and sets `claimed_at` to a jittered-exponential-backoff
point in the future so the row isn't immediately reclaimed.

Real handlers (notification dispatch, reminder escalation, etc.) are
later-phase work; this module is the generic claim/dedupe/retry
machinery every one of them will run through unchanged.
"""

from __future__ import annotations

import logging
import random
import socket
import time
import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.clock import Clock, RealClock
from app.db import SessionLocal
from app.outbox.handlers import get_handler
from app.outbox.models import OutboxEvent

logger = logging.getLogger(__name__)

# A row that has failed MAX_ATTEMPTS times stops being claimed at all —
# it is effectively dead-lettered in place (visible via attempts +
# last_error on the row; a dedicated dead-letter view/replay endpoint is
# F-19 admin work for a later phase).
MAX_ATTEMPTS = 10
BASE_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 300.0
DEFAULT_BATCH_SIZE = 20
DEFAULT_POLL_INTERVAL_SECONDS = 2.0


def _worker_identity() -> str:
    return f"{socket.gethostname()}:{uuid.uuid4().hex[:8]}"


def _backoff_delay(attempts: int) -> float:
    """Exponential backoff with full jitter: after its Nth failed
    attempt a row isn't claimable again until a random point between
    now and roughly `2**N` seconds later (capped) — randomised so a
    batch of rows that all just failed together doesn't retry in
    lockstep and immediately re-collide."""
    capped = min(BASE_BACKOFF_SECONDS * (2**attempts), MAX_BACKOFF_SECONDS)
    return random.uniform(0, capped)


@dataclass
class ClaimResult:
    claimed: int
    processed: int
    failed: int


def claim_batch(
    session: Session,
    *,
    claimed_by: str,
    clock: Clock,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[OutboxEvent]:
    """Claims up to `batch_size` unprocessed rows that have not
    exhausted their attempts and are not currently backed off.

    `FOR UPDATE SKIP LOCKED` is what makes this safe across multiple
    worker processes: a row another worker's transaction already holds
    a lock on is silently skipped rather than blocked on, so two workers
    never process the same row concurrently and neither one stalls
    waiting for the other.
    """
    now = clock.now()
    candidates = (
        session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.processed_at.is_(None), OutboxEvent.attempts < MAX_ATTEMPTS
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(
                batch_size * 2
            )  # over-fetch: some may still be backed off, see filter below
            .with_for_update(skip_locked=True)
        )
        .scalars()
        .all()
    )

    claimed: list[OutboxEvent] = []
    for row in candidates:
        if row.claimed_at is not None and row.claimed_at > now:
            continue  # still backed off (or genuinely being worked by whoever set this)
        row.claimed_at = now
        row.claimed_by = claimed_by
        claimed.append(row)
        if len(claimed) >= batch_size:
            break
    session.flush()
    return claimed


def process_claimed_row(session: Session, row: OutboxEvent, *, clock: Clock) -> bool:
    """Runs the registered handler for one claimed row. Returns True on
    success (row marked `processed_at`), False on failure (row's retry
    bookkeeping updated, left unprocessed)."""
    handler = get_handler(row.event_type)
    if handler is None:
        row.attempts += 1
        row.last_error = f"no handler registered for event_type={row.event_type!r}"
        row.claimed_at = clock.now() + timedelta(seconds=_backoff_delay(row.attempts))
        logger.warning(
            "outbox.no_handler", extra={"event_type": row.event_type, "id": str(row.id)}
        )
        return False

    try:
        handler(session, row)
    except Exception as exc:  # noqa: BLE001 - any handler failure is a retryable outbox failure
        row.attempts += 1
        row.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        row.claimed_at = clock.now() + timedelta(seconds=_backoff_delay(row.attempts))
        logger.warning(
            "outbox.handler_failed",
            extra={
                "event_type": row.event_type,
                "id": str(row.id),
                "attempts": row.attempts,
            },
        )
        return False

    row.processed_at = clock.now()
    row.attempts += 1
    return True


def run_once(
    session: Session,
    *,
    claimed_by: str,
    clock: Clock,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> ClaimResult:
    """Claims and processes one batch, committing the result. Exposed
    separately from `run_forever` so tests can drive exactly one pass
    deterministically."""
    rows = claim_batch(
        session, claimed_by=claimed_by, clock=clock, batch_size=batch_size
    )
    processed = failed = 0
    for row in rows:
        if process_claimed_row(session, row, clock=clock):
            processed += 1
        else:
            failed += 1
    session.commit()
    return ClaimResult(claimed=len(rows), processed=processed, failed=failed)


def run_forever(
    *, poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
) -> None:
    """Entry point for the outbox-consumer half of the `worker`
    docker-compose process (see app.outbox.run_worker)."""
    clock = RealClock()
    claimed_by = _worker_identity()
    logger.info("outbox.worker_starting", extra={"claimed_by": claimed_by})
    while True:
        session = SessionLocal()
        try:
            # No per-row RLS tenant scoping applies here — the outbox is
            # a cross-tenant system table; the worker runs as the
            # unrestricted bureau_admin role, same convention as
            # app.reminders.tasks.
            session.execute(text("SELECT set_config('app.role', 'bureau_admin', true)"))
            result = run_once(session, claimed_by=claimed_by, clock=clock)
            if result.claimed:
                logger.info("outbox.batch", extra=result.__dict__)
        except Exception:
            session.rollback()
            logger.exception("outbox.worker_loop_error")
        finally:
            session.close()
        time.sleep(poll_interval_seconds)
