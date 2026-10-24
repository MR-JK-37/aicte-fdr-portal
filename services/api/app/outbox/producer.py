"""Producer-side helper for the Postgres-outbox pattern (MASTER_PROMPT
§10.2 step 1): "Business transaction commits domain change **and** an
`outbox` row (same transaction)."

THE RULE every future phase must follow: call `enqueue_outbox_event`
with the *same* `Session` already used for the business write, and do
not `session.commit()` until both are done. Postgres only guarantees the
business row and the event row become visible together if they are in
the same transaction — a crash between "write business row" and "write
event row" must be impossible, not just unlikely. That atomicity is the
entire reason this pattern exists instead of "write the row, then
separately publish an event."

Worked usage pattern (every phase that triggers a notification/outbox
event from here on should follow this exact shape):

    def submit_instrument(session: Session, instrument: Instrument, ...) -> None:
        instrument.status = InstrumentStatus.SUBMITTED
        session.flush()                                  # business write, same txn

        enqueue_outbox_event(
            session,
            aggregate_type="instrument",
            aggregate_id=instrument.id,
            event_type="instrument.submitted",
            payload={"institution_id": str(instrument.institution_id)},
            dedupe_key=f"instrument.submitted:{instrument.id}",
        )

        session.commit()                                 # single commit, both rows together

Do NOT call `session.commit()` inside this helper — the caller owns the
transaction boundary so the business write and the event write live or
die together. `dedupe_key` should be derived from something that makes
a retried business operation produce the exact same key (e.g.
`f"{event_type}:{aggregate_id}"`, or include a version/step discriminator
for events that legitimately recur, like a reminder ladder step) — a
second insert with the same key is a silent no-op, not an error,
because callers that re-run the same logical operation (a retried
request, an idempotency-key replay) should not need their own
existence check first.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.outbox.models import OutboxEvent


def enqueue_outbox_event(
    session: Session,
    *,
    aggregate_type: str,
    aggregate_id: uuid.UUID | str,
    event_type: str,
    payload: dict,
    dedupe_key: str,
) -> OutboxEvent:
    """Inserts an outbox row in the caller's current transaction.
    Returns the row whether it was just inserted or already existed
    (idempotent re-enqueue of the same `dedupe_key`)."""
    stmt = (
        pg_insert(OutboxEvent.__table__)
        .values(
            id=uuid.uuid4(),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            dedupe_key=dedupe_key,
            created_at=datetime.now(UTC),
            attempts=0,
        )
        .on_conflict_do_nothing(index_elements=["dedupe_key"])
    )
    session.execute(stmt)
    session.flush()
    return session.execute(
        select(OutboxEvent).where(OutboxEvent.dedupe_key == dedupe_key)
    ).scalar_one()
