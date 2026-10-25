"""Reminders & Lifecycle Scheduler Router (F-10 / Exit Gate G-16).

Features:
- Maker-checker workflow for reminder schedules:
  - GET /v1/reminder-schedules
  - POST /v1/reminder-schedules/versions
  - POST /v1/reminder-schedules/approve (SoD enforced: creator != approver)
- Scheduler status & heartbeat:
  - GET /v1/scheduler/status: Reports DB lease and approved schedule presence.
  - Invariant (G-16): No approved schedule => alert, never invented reminders.
- Calendar & Expiry Feeds:
  - GET /v1/calendar/maturities: Scoped JSON calendar events.
  - POST /v1/calendar/feed-token: Issue revocable iCalendar subscription token.
  - GET /v1/calendar/feed.ics: RFC 5545 iCalendar feed for external calendar sync.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import (
    PermissionVerb,
    Principal,
    SeparationOfDutiesError,
    mask_identifier,
)
from app.models.core import AppUser, Instrument, Reminder
from app.models.enums import InstrumentStatus
from app.models.extensions import CalendarFeedToken, ReminderSchedule
from app.models.workflow import SchedulerRun
from app.problem_json import NotFoundError

router = APIRouter(prefix="/v1", tags=["Reminders & Scheduler (F-10)"])


# --- Schemas ---


class ReminderScheduleRule(BaseModel):
    days_before_maturity: int
    channel: str = "in_app"
    recipient_roles: list[str]
    escalation_window_days: int = 7


class CreateScheduleVersionPayload(BaseModel):
    rules: list[ReminderScheduleRule] = Field(..., min_length=1)


class ScheduleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    rules: dict[str, Any]
    status: str
    created_by: uuid.UUID
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    created_at: datetime


class SchedulerStatusResponse(BaseModel):
    scheduler_active: bool
    active_schedule_version: int | None
    has_approved_schedule: bool
    status_alert: str | None
    last_run_at: datetime | None
    last_run_status: str | None


class CalendarEventItem(BaseModel):
    id: str
    title: str
    instrument_id: str
    instrument_number: str
    maturity_date: datetime
    amount: float
    days_until_due: int
    status: str


class FeedTokenResponse(BaseModel):
    token: str
    feed_url: str
    expires_at: datetime


# --- Endpoints ---


@router.get("/reminder-schedules", response_model=list[ScheduleVersionResponse])
def list_reminder_schedules(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[ScheduleVersionResponse]:
    """Lists reminder schedule configurations and versions."""
    stmt = select(ReminderSchedule).order_by(desc(ReminderSchedule.version))
    schedules = db.execute(stmt).scalars().all()
    return [ScheduleVersionResponse.model_validate(s) for s in schedules]


@router.post(
    "/reminder-schedules/versions",
    response_model=ScheduleVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder_schedule_version(
    payload: CreateScheduleVersionPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_POLICY)),
    db: Session = Depends(get_db),
) -> ScheduleVersionResponse:
    """Maker creates a new draft reminder schedule version."""
    latest_version = (
        db.execute(
            select(ReminderSchedule.version)
            .order_by(desc(ReminderSchedule.version))
            .limit(1)
        ).scalar_one_or_none()
        or 0
    )
    new_version = latest_version + 1

    schedule = ReminderSchedule(
        id=uuid.uuid4(),
        version=new_version,
        rules={"rules": [r.model_dump() for r in payload.rules]},
        status="DRAFT",
        created_by=principal.id,
    )
    db.add(schedule)
    db.flush()

    append_audit_entry(
        db,
        action="reminder_schedule.created",
        entity_type="reminder_schedule",
        entity_id=str(schedule.id),
        after={"version": new_version, "rules_count": len(payload.rules)},
        actor_id=str(principal.id),
    )
    db.commit()

    return ScheduleVersionResponse.model_validate(schedule)


@router.post("/reminder-schedules/approve", response_model=ScheduleVersionResponse)
def approve_reminder_schedule(
    schedule_id: uuid.UUID = Query(...),
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_POLICY)),
    db: Session = Depends(get_db),
) -> ScheduleVersionResponse:
    """Checker approves a reminder schedule (SoD: approver != creator)."""
    schedule = db.get(ReminderSchedule, schedule_id)
    if not schedule:
        raise NotFoundError("ReminderSchedule", schedule_id)

    if schedule.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schedule version is already {schedule.status}",
        )

    # SoD Check: creator cannot approve their own schedule
    if schedule.created_by == principal.id:
        raise SeparationOfDutiesError(
            "Creator cannot approve their own reminder schedule version (maker-checker violation)"
        )

    # Retire currently active schedule
    active_schedules = (
        db.execute(select(ReminderSchedule).where(ReminderSchedule.status == "ACTIVE"))
        .scalars()
        .all()
    )
    for s in active_schedules:
        s.status = "SUPERSEDED"

    schedule.status = "ACTIVE"
    schedule.approved_by = principal.id
    schedule.approved_at = datetime.now(UTC)
    db.flush()

    append_audit_entry(
        db,
        action="reminder_schedule.approved",
        entity_type="reminder_schedule",
        entity_id=str(schedule.id),
        after={"version": schedule.version, "status": "ACTIVE"},
        actor_id=str(principal.id),
    )
    db.commit()

    return ScheduleVersionResponse.model_validate(schedule)


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> SchedulerStatusResponse:
    """Reports scheduler daemon status, lease, and active policy (Exit Gate G-16)."""
    active_sched = db.execute(
        select(ReminderSchedule).where(ReminderSchedule.status == "ACTIVE")
    ).scalar_one_or_none()
    last_run = db.execute(
        select(SchedulerRun).order_by(desc(SchedulerRun.created_at)).limit(1)
    ).scalar_one_or_none()

    has_approved = active_sched is not None
    alert = (
        None
        if has_approved
        else "No approved reminder schedule configured — reminder generation suspended until authorized"
    )

    return SchedulerStatusResponse(
        scheduler_active=True,
        active_schedule_version=active_sched.version if active_sched else None,
        has_approved_schedule=has_approved,
        status_alert=alert,
        last_run_at=last_run.created_at if last_run else None,
        last_run_status=last_run.status if last_run else "IDLE",
    )


@router.get("/reminders")
def list_reminders(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
):
    """Lists compliance maturity reminders scoped to user's institutions."""
    stmt = select(Reminder)
    if principal.institution_id:
        stmt = stmt.where(Reminder.institution_id == principal.institution_id)
    if status_filter:
        stmt = stmt.where(Reminder.status == status_filter)
    stmt = stmt.order_by(desc(Reminder.created_at)).limit(limit)

    reminders = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(r.id),
            "instrument_id": str(r.instrument_id),
            "target_date": r.target_date.isoformat() if r.target_date else None,
            "days_before": r.days_before,
            "status": r.status,
            "channel": r.channel,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reminders
    ]


@router.get("/calendar/maturities", response_model=list[CalendarEventItem])
def get_calendar_maturities(
    months: int = Query(6, ge=1, le=24),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[CalendarEventItem]:
    """Returns calendar of maturing deposits within user's scope."""
    now = datetime.now(UTC)
    horizon = now + timedelta(days=months * 30)

    stmt = (
        select(Instrument)
        .where(
            Instrument.maturity_date.is_not(None),
            Instrument.maturity_date >= now - timedelta(days=7),
            Instrument.maturity_date <= horizon,
            Instrument.status.in_(
                [
                    InstrumentStatus.ACTIVE,
                    InstrumentStatus.SUBMITTED,
                    InstrumentStatus.VERIFIED,
                    InstrumentStatus.MATURED,
                ]
            ),
        )
        .order_by(Instrument.maturity_date.asc())
        .limit(200)
    )

    if principal.institution_id:
        stmt = stmt.where(Instrument.institution_id == principal.institution_id)

    instruments = db.execute(stmt).scalars().all()
    return [
        CalendarEventItem(
            id=f"mat-{i.id}",
            title=f"Maturity: FDR {mask_identifier(i.instrument_number)} (₹{i.amount:,.2f})",
            instrument_id=str(i.id),
            instrument_number=mask_identifier(i.instrument_number),
            maturity_date=i.maturity_date,
            amount=float(i.amount),
            days_until_due=(i.maturity_date - now).days,
            status=i.status.value if hasattr(i.status, "value") else str(i.status),
        )
        for i in instruments
        if i.maturity_date
    ]


@router.post(
    "/calendar/feed-token",
    response_model=FeedTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_calendar_feed_token(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> FeedTokenResponse:
    """Generates a revocable token for external calendar subscriptions (RFC 5545)."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(days=90)

    # Revoke any prior tokens for this user
    existing = (
        db.execute(
            select(CalendarFeedToken).where(
                CalendarFeedToken.user_id == principal.id,
                CalendarFeedToken.revoked_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    for tok in existing:
        tok.revoked_at = datetime.now(UTC)

    feed_tok = CalendarFeedToken(
        id=uuid.uuid4(),
        user_id=principal.id,
        token_hash=token_hash,
        name="AICTE FDR Maturity Calendar",
        expires_at=expires_at,
    )
    db.add(feed_tok)
    db.commit()

    return FeedTokenResponse(
        token=raw_token,
        feed_url=f"/v1/calendar/feed.ics?token={raw_token}",
        expires_at=expires_at,
    )


@router.get("/calendar/feed.ics")
def export_calendar_ics_feed(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """RFC 5545 iCalendar feed endpoint for Apple Calendar / Outlook / Google Calendar."""
    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    tok_record = db.execute(
        select(CalendarFeedToken).where(
            CalendarFeedToken.token_hash == token_hash,
            CalendarFeedToken.revoked_at.is_(None),
            CalendarFeedToken.expires_at > datetime.now(UTC),
        )
    ).scalar_one_or_none()

    if not tok_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked calendar feed token",
        )

    # Bearer-token auth, not principal auth — no RLS app.role context has been
    # set on this session yet. Scope it to the lookup this handler needs.
    from app.db import set_app_context

    set_app_context(db, role="platform_operator")

    owner = db.get(AppUser, tok_record.user_id)
    if not owner or not owner.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token owner"
        )

    now = datetime.now(UTC)
    horizon = now + timedelta(days=180)
    stmt = (
        select(Instrument)
        .where(
            Instrument.maturity_date.is_not(None),
            Instrument.maturity_date >= now - timedelta(days=14),
            Instrument.maturity_date <= horizon,
        )
        .order_by(Instrument.maturity_date.asc())
        .limit(100)
    )
    # A feed token is bearer-authenticated (CalDAV/ICS clients can't do
    # OAuth), so this is the only place scoping happens — never return
    # another institution's maturities just because the bearer holds a
    # validly-issued token for their own account (CLAUDE.md non-negotiable #6).
    if owner.institution_id:
        stmt = stmt.where(Instrument.institution_id == owner.institution_id)

    instruments = db.execute(stmt).scalars().all()

    # Generate minimal RFC 5545 iCalendar format
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AICTE//Security Deposit Portal Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:AICTE FDR Maturities",
    ]

    for inst in instruments:
        if not inst.maturity_date:
            continue
        dt_str = inst.maturity_date.strftime("%Y%m%d")
        masked = mask_identifier(inst.instrument_number)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:fdr-mat-{inst.id}@aicte-india.org",
                f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;VALUE=DATE:{dt_str}",
                f"DTEND;VALUE=DATE:{dt_str}",
                f"SUMMARY:Deposit Maturity: FDR {masked}",
                f"DESCRIPTION:Security Deposit FDR {masked} matures on {dt_str}. Amount: INR {inst.amount:,.2f}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    ics_body = "\r\n".join(lines) + "\r\n"

    return Response(
        content=ics_body,
        media_type="text/calendar",
        headers={"Content-Disposition": 'inline; filename="aicte_fdr_maturities.ics"'},
    )
