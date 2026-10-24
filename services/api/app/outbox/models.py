"""ORM model for the `outbox` table (Postgres-outbox pattern, MASTER_PROMPT
§4.2 / §10.2).

This table is created by the Alembic migration the parallel Phase-1
workstream (role/RLS rewrite) owns, per the contract fixed in this
phase's task brief:

    outbox: id UUID PK, aggregate_type text, aggregate_id UUID,
    event_type text, payload JSONB, dedupe_key text UNIQUE,
    created_at timestamptz, claimed_at timestamptz NULL,
    claimed_by text NULL, processed_at timestamptz NULL, attempts int,
    last_error text NULL

This module defines the SQLAlchemy mapping this phase's code (producer
+ worker, app.outbox.producer / app.outbox.worker) needs against that
contract. That migration has not landed yet, so every query against
this model will fail with "relation outbox does not exist" until it
does — that is the single thing blocking this module from working
end-to-end (see this phase's report). If the landed migration's actual
column names/types differ slightly, reconcile here.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OutboxEvent(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    aggregate_type: Mapped[str] = mapped_column(String(64))
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    dedupe_key: Mapped[str] = mapped_column(String(256), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # claimed_at doubles as a "not claimable again until" marker after a
    # failed attempt (app.outbox.worker's backoff) as well as "currently
    # being processed" while a claim is in flight — see claim_batch.
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    claimed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
