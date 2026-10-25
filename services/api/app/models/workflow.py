import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class StateTransition(Base):
    __tablename__ = "state_transitions"

    id: Mapped[uuid.UUID] = uuid_pk()
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    from_state: Mapped[str] = mapped_column(String(64))
    to_state: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    reason_code: Mapped[str] = mapped_column(String(64))
    reason_text: Mapped[str] = mapped_column(Text)
    policy_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    evidence_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InstrumentVersion(Base):
    __tablename__ = "instrument_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="CASCADE")
    )
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))
    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InstitutionOnboardingRequest(Base):
    __tablename__ = "institution_onboarding_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    applicant_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    authority_letter_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    official_id_ref: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CaseComment(Base):
    __tablename__ = "case_comments"

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    entity_type: Mapped[str] = mapped_column(String(64))
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    comment: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id: Mapped[uuid.UUID] = uuid_pk()
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    queue_name: Mapped[str] = mapped_column(String(64))
    assigned_to: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    assigned_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BankConfirmationRequest(Base):
    __tablename__ = "bank_confirmation_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    bank_name: Mapped[str] = mapped_column(String(128))
    branch_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ifsc: Mapped[str | None] = mapped_column(String(16), nullable=True)
    account_number_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tracking_number: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="AWAITING_RESPONSE")
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    assigned_bank_verifier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    response_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    response_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    response_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StatementBatch(Base):
    __tablename__ = "statement_batches"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_filename: Mapped[str] = mapped_column(String(256))
    format: Mapped[str] = mapped_column(String(32))
    checksum: Mapped[str] = mapped_column(String(64))
    account_number_masked: Mapped[str] = mapped_column(String(64))
    opening_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    closing_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    matched_lines: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_lines: Mapped[int] = mapped_column(Integer, default=0)
    quarantined_lines: Mapped[int] = mapped_column(Integer, default=0)
    quarantined_summary: Mapped[list] = mapped_column(JSONB, default=list)
    imported_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StatementLine(Base):
    __tablename__ = "statement_lines"

    id: Mapped[uuid.UUID] = uuid_pk()
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("statement_batches.id", ondelete="CASCADE")
    )
    line_number: Mapped[int] = mapped_column(Integer)
    line_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    utr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    narration: Mapped[str] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(32), default="UNMATCHED")
    matched_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("instruments.id"), nullable=True
    )
    reconciliation_rule_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    quarantine_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ReconciliationException(Base):
    __tablename__ = "reconciliation_exceptions"

    id: Mapped[uuid.UUID] = uuid_pk()
    statement_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("statement_lines.id"), nullable=True
    )
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("instruments.id"), nullable=True
    )
    exception_type: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    candidate_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    reviewed_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    engine: Mapped[str] = mapped_column(String(64), default="tesseract-v5")
    status: Mapped[str] = mapped_column(String(32), default="CANDIDATE")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    policy_id: Mapped[str] = mapped_column(String(64))
    document: Mapped[str] = mapped_column(String(256))
    clause: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effective_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    effective_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    config_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    blocked_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    step_up_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SchedulerRun(Base):
    __tablename__ = "scheduler_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    scheduler_id: Mapped[str] = mapped_column(String(64))
    leased_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    leased_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="IDLE")
    metadata_payload: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InstrumentLineage(Base):
    __tablename__ = "instrument_lineage"

    id: Mapped[uuid.UUID] = uuid_pk()
    predecessor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    successor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    relationship_type: Mapped[str] = mapped_column(String(32), default="RENEWAL")
    gap_days: Mapped[int] = mapped_column(Integer, default=0)
    overlap_days: Mapped[int] = mapped_column(Integer, default=0)
    policy_allowed_gap_days: Mapped[int] = mapped_column(Integer, default=0)
    is_gap_discrepancy: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Clearance(Base):
    __tablename__ = "clearances"

    id: Mapped[uuid.UUID] = uuid_pk()
    release_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_requests.id", ondelete="CASCADE")
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    cell: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="PENDING_SOURCE")
    received_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReleaseChecklistItem(Base):
    __tablename__ = "release_checklist_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    release_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_requests.id", ondelete="CASCADE")
    )
    rule_id: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="PENDING_SOURCE")
    deciding_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    evidence_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    evidence_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    policy_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("policy_versions.id"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserNotification(Base):
    __tablename__ = "user_notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE"), nullable=True
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(64), default="critical_workflow")
    channel: Mapped[str] = mapped_column(String(32), default="in_app")
    template_key: Mapped[str] = mapped_column(String(128))
    template_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    locale: Mapped[str] = mapped_column(String(16), default="en")
    status: Mapped[str] = mapped_column(String(32), default="CREATED")
    title: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text)
    deep_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    lock_screen_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    lock_screen_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actioned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    provider_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    device_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class NotificationAttempt(Base):
    __tablename__ = "notification_attempts"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_notification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_notifications.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(32))
    provider_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    result_code: Mapped[str] = mapped_column(String(64))
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DeviceInstallation(Base):
    __tablename__ = "device_installations"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE")
    )
    platform: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(32))
    push_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    auth_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    p256dh_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "category", "channel", name="uq_user_notif_pref"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_users.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    locale: Mapped[str] = mapped_column(String(16), default="en")
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(8), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(8), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SSEEvent(Base):
    __tablename__ = "sse_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    sequence_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, cycle=False))
    event_type: Mapped[str] = mapped_column(String(64))
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class NotificationDLQ(Base):
    __tablename__ = "notification_dlq"

    id: Mapped[uuid.UUID] = uuid_pk()
    outbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    user_notification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(64))
    error_reason: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="DEAD_LETTER")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    replayed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
