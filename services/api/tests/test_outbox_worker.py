"""Unit/integration tests for the outbox claim/process/retry machinery
(app.outbox.worker, app.outbox.producer, app.outbox.handlers).

BLOCKED-ON-MIGRATION NOTE: the real `outbox` table is owned by the
parallel Phase-1 workstream's Alembic migration, which has not landed
yet (see this phase's task brief/report). Per that brief's fallback
instruction ("unit-test the claim-and-process logic against a test DB
with a manually-created temp table if the real migration isn't there
yet"), this module creates the contracted `outbox` table itself with
raw DDL for the duration of this test module, against the same test
Postgres the rest of the suite uses, and drops it afterwards. Once the
real migration lands, delete the `_ensure_outbox_table` fixture below —
everything else in this file should keep working unchanged against the
real table.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.outbox.handlers import register_handler
from app.outbox.producer import enqueue_outbox_event
from app.outbox.worker import claim_batch, process_claimed_row, run_once

# fdr_app (the `engine`/`db_session` fixtures' role, same as production)
# has no CREATE privilege on the public schema by design (least
# privilege, see migration a821603301c6) — only the table-owning role
# can create the temp table this blocked-on-migration test needs. The
# table-owning role's `ALTER DEFAULT PRIVILEGES` grant (same migration)
# means fdr_app automatically gets SELECT/INSERT/UPDATE/DELETE on it
# once it exists, so only the CREATE/DROP TABLE DDL needs this engine.
_SUPERUSER_DATABASE_URL = os.environ.get(
    "SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)


from app.db import set_app_context


@pytest.fixture(autouse=True)
def _clean_outbox(db_session):
    set_app_context(db_session, role="platform_operator", is_local=False)
    db_session.execute(text("DELETE FROM outbox"))
    db_session.commit()
    set_app_context(db_session, role="platform_operator", is_local=False)
    yield
    set_app_context(db_session, role="platform_operator", is_local=False)
    db_session.execute(text("DELETE FROM outbox"))
    db_session.commit()
    set_app_context(db_session, role="", is_local=False)


def test_enqueue_is_idempotent_on_dedupe_key(db_session):
    aggregate_id = uuid.uuid4()
    first = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=aggregate_id,
        event_type="example.ping",
        payload={"a": 1},
        dedupe_key="dedupe-1",
    )
    second = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=aggregate_id,
        event_type="example.ping",
        payload={"a": 999},  # different payload, same key — ignored
        dedupe_key="dedupe-1",
    )
    db_session.commit()
    assert first.id == second.id

    count = db_session.execute(text("SELECT count(*) FROM outbox")).scalar_one()
    assert count == 1


def test_claim_batch_skips_future_backoff_rows(db_session, clock):
    enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="example.ping",
        payload={},
        dedupe_key="due-now",
    )
    future_row = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="example.ping",
        payload={},
        dedupe_key="backed-off",
    )
    future_row.claimed_at = datetime.now(UTC) + timedelta(hours=1)
    db_session.commit()

    claimed = claim_batch(db_session, claimed_by="test-worker", clock=clock)
    db_session.commit()

    claimed_keys = {row.dedupe_key for row in claimed}
    assert "due-now" in claimed_keys
    assert "backed-off" not in claimed_keys


def test_process_claimed_row_marks_processed_on_success(db_session, clock):
    calls: list[str] = []
    register_handler(
        "test.success", lambda session, event: calls.append(event.dedupe_key)
    )

    row = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="test.success",
        payload={},
        dedupe_key="success-1",
    )
    db_session.commit()

    ok = process_claimed_row(db_session, row, clock=clock)
    db_session.commit()

    assert ok is True
    assert row.processed_at is not None
    assert calls == ["success-1"]


def test_process_claimed_row_backs_off_on_handler_failure(db_session, clock):
    def _always_fails(session, event):
        raise RuntimeError("boom")

    register_handler("test.failure", _always_fails)

    row = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="test.failure",
        payload={},
        dedupe_key="failure-1",
    )
    db_session.commit()

    ok = process_claimed_row(db_session, row, clock=clock)
    db_session.commit()

    assert ok is False
    assert row.processed_at is None
    assert row.attempts == 1
    assert "boom" in row.last_error
    assert row.claimed_at > clock.now() - timedelta(seconds=1)  # pushed into the future


def test_process_claimed_row_without_handler_is_a_tracked_failure(db_session, clock):
    row = enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="test.unregistered-" + uuid.uuid4().hex[:8],
        payload={},
        dedupe_key="unregistered-1",
    )
    db_session.commit()

    ok = process_claimed_row(db_session, row, clock=clock)

    assert ok is False
    assert "no handler registered" in row.last_error


def test_run_once_end_to_end_with_example_handler(db_session, clock):
    enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="example.ping",
        payload={},
        dedupe_key="e2e-1",
    )
    db_session.commit()

    result = run_once(db_session, claimed_by="test-worker", clock=clock)

    assert result.claimed == 1
    assert result.processed == 1
    assert result.failed == 0

    processed_row = db_session.execute(
        text("SELECT processed_at FROM outbox WHERE dedupe_key = 'e2e-1'")
    ).scalar_one()
    assert processed_row is not None


def test_run_once_is_idempotent_second_pass_claims_nothing(db_session, clock):
    enqueue_outbox_event(
        db_session,
        aggregate_type="instrument",
        aggregate_id=uuid.uuid4(),
        event_type="example.ping",
        payload={},
        dedupe_key="e2e-2",
    )
    db_session.commit()

    first = run_once(db_session, claimed_by="test-worker", clock=clock)
    second = run_once(db_session, claimed_by="test-worker", clock=clock)

    assert first.processed == 1
    assert second.claimed == 0  # already processed_at, not reclaimed
