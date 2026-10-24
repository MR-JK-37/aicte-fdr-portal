"""ORM models for `feature_registry` and `connector_health_checks`
(MASTER_PROMPT §3 reality matrix, §19 F-19 admin/operations).

Migration owned by the parallel Phase-1 workstream (role/RLS rewrite),
not landed yet — see this phase's task brief's contract:

    feature_registry: id UUID PK, key text UNIQUE, state text
    ('disabled'|'sandbox-only'|'production-enabled'|'degraded'),
    description text, acceptance_evidence_ref text NULL, updated_by
    UUID NULL, updated_at timestamptz

    connector_health_checks: id UUID PK, feature_key text, checked_at
    timestamptz, status text, detail JSONB NULL
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

FEATURE_STATES = ("disabled", "sandbox-only", "production-enabled", "degraded")


class FeatureRegistryEntry(Base):
    __tablename__ = "feature_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(String(128), unique=True)
    state: Mapped[str] = mapped_column(String(32), default="disabled")
    description: Mapped[str] = mapped_column(Text)
    # MASTER_PROMPT §3: state='production-enabled' is only valid once an
    # acceptance-evidence attachment exists — enforced in
    # app.registry.router, not here (an ORM-level CHECK constraint would
    # need a migration, which isn't this phase's to add).
    acceptance_evidence_ref: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConnectorHealthCheck(Base):
    __tablename__ = "connector_health_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    feature_key: Mapped[str] = mapped_column(String(128))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
