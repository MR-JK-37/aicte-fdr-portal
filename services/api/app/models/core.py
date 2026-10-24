import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = uuid_pk()
    aicte_code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Trust(Base):
    __tablename__ = "trusts"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    name: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = uuid_pk()
    bank_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("banks.id"))
    ifsc: Mapped[str] = mapped_column(String(11), unique=True)
    name: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    trust_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trusts.id"), nullable=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True
    )
    type: Mapped[InstrumentType] = mapped_column(
        Enum(InstrumentType, name="instrument_type")
    )
    status: Mapped[InstrumentStatus] = mapped_column(
        Enum(InstrumentStatus, name="instrument_status"),
        default=InstrumentStatus.SUBMITTED,
    )
    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        Enum(EvidenceLevel, name="evidence_level"), default=EvidenceLevel.L0_DECLARED
    )
    instrument_number: Mapped[str] = mapped_column(String(64))
    blind_index: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    # Declared UTR for ONLINE_SD instruments, used by the AICTE
    # bank-statement reconciliation (ledger -> L3) matcher.
    utr: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # timezone=True: these are compared directly against clock.now()
    # (timezone-aware) in app/reminders/scheduler.py — a naive/aware
    # mismatch raises TypeError, caught by a cross-session reload test
    # (in-process ladder tests never round-tripped through the DB, so
    # they didn't surface it).
    issue_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    maturity_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tenor_months: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    storage_key: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    phash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="quarantined")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    level: Mapped[EvidenceLevel] = mapped_column(
        Enum(EvidenceLevel, name="evidence_level_vr")
    )
    source: Mapped[str] = mapped_column(String(64))
    confirmed_amount: Mapped[float | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    field: Mapped[str] = mapped_column(String(128))
    declared_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    extracted_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ScrutinyObservation(Base):
    __tablename__ = "scrutiny_observations"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    officer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    observation: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id", "window", name="uq_reminder_instrument_window"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    window: Mapped[str] = mapped_column(String(16))
    channel: Mapped[str] = mapped_column(String(32))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # Escalation ladder state (app/reminders/ladder.py): ladder_step indexes
    # app.reminders.ladder.LADDER_STEPS; last_step_at is the injected
    # Clock's time at the last step, so tests can time-travel their own
    # clock fixture without any production code depending on that.
    ladder_step: Mapped[int] = mapped_column(default=0)
    last_step_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    level: Mapped[str] = mapped_column(String(32))
    escalated_to: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ReleaseRequest(Base):
    __tablename__ = "release_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    maker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    checker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    # The scrutiny officer who handled this instrument's file — the maker-
    # checker rule forbids this same person from approving its release.
    scrutiny_officer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)


class Penalty(Base):
    __tablename__ = "penalties"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    type: Mapped[str] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    reason: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="unpaid")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    keycloak_sub: Mapped[str] = mapped_column(String(128), unique=True)
    email: Mapped[str] = mapped_column(String(256), unique=True)
    full_name: Mapped[str] = mapped_column(String(256))
    role: Mapped[AppRole] = mapped_column(Enum(AppRole, name="app_role"))
    is_active: Mapped[bool] = mapped_column(default=True)
    mfa_enrolled: Mapped[bool] = mapped_column(default=False)
    step_up_valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delegation_limit: Mapped[float | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    region_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Phase 7: localised notification text and quiet-hours suppression.
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")
    quiet_hours_start: Mapped[int] = mapped_column(
        default=21
    )  # 24h local hour, inclusive
    quiet_hours_end: Mapped[int] = mapped_column(default=8)  # 24h local hour, exclusive
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    app_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    token: Mapped[str] = mapped_column(String(512))
    platform: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    app_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"))
    consent_type: Mapped[str] = mapped_column(String(64))
    granted_at: Mapped[datetime] = mapped_column(server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    app_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_users.id"), nullable=True
    )
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("instruments.id"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(32))
    template: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
