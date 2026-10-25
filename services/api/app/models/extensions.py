from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    report_key: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    scope_filter: Mapped[dict] = mapped_column(JSONB, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING"
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_content: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # In-memory stored sanitized CSV
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id: Mapped[uuid.UUID] = uuid_pk()
    report_key: Mapped[str] = mapped_column(String(64))
    cron_expression: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditVerificationJob(Base):
    __tablename__ = "audit_verification_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    triggered_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    status: Mapped[str] = mapped_column(
        String(32)
    )  # IN_PROGRESS, VERIFIED, BROKEN, ERROR
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    broken_at_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    entries_verified: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserInvitation(Base):
    __tablename__ = "user_invitations"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(256), index=True)
    role: Mapped[str] = mapped_column(String(64))
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING"
    )  # PENDING, ACCEPTED, EXPIRED, REVOKED
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RoleAssignmentRequest(Base):
    __tablename__ = "role_assignment_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    requested_role: Mapped[str] = mapped_column(String(64))
    requested_scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING"
    )  # PENDING, APPROVED, REJECTED
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RecertificationCampaign(Base):
    __tablename__ = "recertification_campaigns"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(256))
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE"
    )  # ACTIVE, COMPLETED, CANCELLED
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SavedView(Base):
    __tablename__ = "saved_views"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    name: Mapped[str] = mapped_column(String(128))
    entity_type: Mapped[str] = mapped_column(
        String(64)
    )  # instrument, observation, etc.
    filter_criteria: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReminderSchedule(Base):
    __tablename__ = "reminder_schedules"

    id: Mapped[uuid.UUID] = uuid_pk()
    version: Mapped[int] = mapped_column(Integer, unique=True)
    rules: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT"
    )  # DRAFT, APPROVED, ACTIVE, SUPERSEDED
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CalendarFeedToken(Base):
    __tablename__ = "calendar_feed_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128), default="Calendar Feed")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SupportRequest(Base):
    __tablename__ = "support_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    category: Mapped[str] = mapped_column(
        String(64)
    )  # compliance, technical, data_issue
    subject: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN"
    )  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RightsRequest(Base):
    __tablename__ = "rights_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    request_type: Mapped[str] = mapped_column(
        String(64)
    )  # ACCESS, RECTIFICATION, ERASURE, OBJECTION
    details: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="PENDING_VERIFICATION")
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RetentionClass(Base):
    __tablename__ = "retention_classes"

    id: Mapped[uuid.UUID] = uuid_pk()
    class_key: Mapped[str] = mapped_column(String(64), unique=True)
    retention_years: Mapped[int] = mapped_column(Integer, default=8)
    disposal_action: Mapped[str] = mapped_column(String(64), default="ARCHIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LegalHold(Base):
    __tablename__ = "legal_holds"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(256))
    matter_id: Mapped[str] = mapped_column(String(128))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(64))
    applied_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    reason: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    lifted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
