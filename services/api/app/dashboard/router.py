"""Dashboard API Router (F-16 / SPEC §20 / MASTER_PROMPT_V2 §7).

Provides:
- GET /v1/dashboard/summary: Scope-filtered counts for all operational categories,
  each with a drilldown filter object; counts equal list totals; no composite score.
- GET /v1/dashboard/my-work: Role- and scope-filtered work items requiring user action.
- GET /v1/dashboard/due-soon: Instruments nearing maturity (<= 30 days).
- GET /v1/dashboard/activity: Recent auditable events within user's scope.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal, mask_identifier
from app.models.audit import AuditLog
from app.models.core import Discrepancy, Instrument, ReleaseRequest, ScrutinyObservation
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus
from app.models.workflow import BankConfirmationRequest

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard (F-16)"])


# --- Schemas ---


class DrilldownCount(BaseModel):
    model_config = ConfigDict(frozen=True)

    count: int
    drilldown: dict[str, Any]


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    active: DrilldownCount
    expiring_30d: DrilldownCount
    expiring_60d: DrilldownCount
    expiring_90d: DrilldownCount
    matured: DrilldownCount
    renewed: DrilldownCount
    released: DrilldownCount
    pending_verification: DrilldownCount
    open_observations: DrilldownCount
    awaiting_institution: DrilldownCount
    reconciliation_exceptions: DrilldownCount
    release_by_stage: dict[str, DrilldownCount]
    overdue_and_ageing: dict[str, DrilldownCount]
    evidence_distribution: dict[str, DrilldownCount]


class WorkItem(BaseModel):
    id: str
    item_type: str  # instrument, observation, release_request, bank_confirmation
    title: str
    reference_id: str
    status: str
    priority: str  # high, medium, low
    created_at: datetime
    due_date: datetime | None = None
    deep_link: str


class DueSoonItem(BaseModel):
    id: str
    instrument_number: str
    institution_id: str
    amount: float
    maturity_date: datetime
    days_remaining: int
    status: str


class ActivityItem(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    actor_id: str | None
    created_at: datetime


# --- Helpers ---


def _scope_instrument_stmt(stmt, principal: Principal):
    if principal.institution_id:
        return stmt.where(Instrument.institution_id == principal.institution_id)
    return stmt


# --- Endpoints ---


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Returns honest, scope-filtered operational counts with drilldown parameters."""
    now = datetime.now(UTC)
    t30 = now + timedelta(days=30)
    t60 = now + timedelta(days=60)
    t90 = now + timedelta(days=90)

    # Base query for instruments
    inst_stmt = select(Instrument)
    inst_stmt = _scope_instrument_stmt(inst_stmt, principal)
    instruments = db.execute(inst_stmt).scalars().all()

    # Active
    active_items = [
        i
        for i in instruments
        if i.status
        in (
            InstrumentStatus.ACTIVE,
            InstrumentStatus.SUBMITTED,
            InstrumentStatus.VERIFIED,
        )
    ]

    # Expiring by horizon (only active instruments)
    exp_30 = [
        i for i in active_items if i.maturity_date and now <= i.maturity_date <= t30
    ]
    exp_60 = [
        i for i in active_items if i.maturity_date and now <= i.maturity_date <= t60
    ]
    exp_90 = [
        i for i in active_items if i.maturity_date and now <= i.maturity_date <= t90
    ]

    # Matured / Overdue
    matured = [
        i
        for i in instruments
        if i.status == InstrumentStatus.MATURED
        or (
            i.maturity_date
            and i.maturity_date < now
            and i.status == InstrumentStatus.ACTIVE
        )
    ]
    renewed = [
        i
        for i in instruments
        if i.status
        in (InstrumentStatus.SUPERSEDED, InstrumentStatus.RENEWAL_REQUESTED)
    ]
    released = [i for i in instruments if i.status == InstrumentStatus.RELEASED]
    pending_ver = [
        i
        for i in instruments
        if i.status
        in (
            InstrumentStatus.SUBMITTED,
            InstrumentStatus.INTAKE_REVIEW,
            InstrumentStatus.UNDER_SCRUTINY,
            InstrumentStatus.SCRUTINY,
        )
    ]

    # Observations
    obs_stmt = select(ScrutinyObservation)
    if principal.institution_id:
        obs_stmt = obs_stmt.join(
            Instrument, ScrutinyObservation.instrument_id == Instrument.id
        ).where(Instrument.institution_id == principal.institution_id)
    observations = db.execute(obs_stmt).scalars().all()
    open_obs = [o for o in observations if o.status not in ("RESOLVED", "CLOSED")]
    awaiting_inst = [o for o in open_obs if o.status in ("OPEN", "ACTION_REQUIRED")]

    # Reconciliation exceptions
    rec_stmt = select(Discrepancy)
    if principal.institution_id:
        rec_stmt = rec_stmt.join(
            Instrument, Discrepancy.instrument_id == Instrument.id
        ).where(Instrument.institution_id == principal.institution_id)
    reconciliations = db.execute(rec_stmt).scalars().all()
    open_rec = [r for r in reconciliations if r.status not in ("RESOLVED", "CLOSED")]

    # Release by stage
    rel_stmt = select(ReleaseRequest)
    if principal.institution_id:
        rel_stmt = rel_stmt.where(
            ReleaseRequest.institution_id == principal.institution_id
        )
    releases = db.execute(rel_stmt).scalars().all()

    stages = [
        "REQUESTED",
        "CLEARANCES_PENDING",
        "RECOMMENDED",
        "APPROVED",
        "EXECUTION_PENDING",
        "COMPLETED",
        "REJECTED",
    ]
    release_by_stage = {
        stage.lower(): DrilldownCount(
            count=len(
                [
                    r
                    for r in releases
                    if (r.status.value if hasattr(r.status, "value") else str(r.status))
                    == stage
                ]
            ),
            drilldown={"entity": "release_request", "status": stage.lower()},
        )
        for stage in stages
    }

    # Overdue and ageing buckets (matured > 0 days)
    overdue_items = [
        i
        for i in instruments
        if i.maturity_date
        and i.maturity_date < now
        and i.status != InstrumentStatus.RELEASED
    ]
    age_30 = [i for i in overdue_items if (now - i.maturity_date).days <= 30]
    age_60 = [i for i in overdue_items if 30 < (now - i.maturity_date).days <= 60]
    age_90 = [i for i in overdue_items if 60 < (now - i.maturity_date).days <= 90]
    age_90_plus = [i for i in overdue_items if (now - i.maturity_date).days > 90]

    overdue_and_ageing = {
        "less_than_30d": DrilldownCount(
            count=len(age_30), drilldown={"overdue_max_days": 30}
        ),
        "between_31_and_60d": DrilldownCount(
            count=len(age_60),
            drilldown={"overdue_min_days": 31, "overdue_max_days": 60},
        ),
        "between_61_and_90d": DrilldownCount(
            count=len(age_90),
            drilldown={"overdue_min_days": 61, "overdue_max_days": 90},
        ),
        "greater_than_90d": DrilldownCount(
            count=len(age_90_plus), drilldown={"overdue_min_days": 91}
        ),
    }

    # Evidence distribution
    evidence_distribution = {
        "L0_DECLARED": DrilldownCount(
            count=len(
                [
                    i
                    for i in instruments
                    if i.evidence_level == EvidenceLevel.L0_DECLARED
                ]
            ),
            drilldown={"evidence_level": "L0_DECLARED"},
        ),
        "L1_EXTRACTED": DrilldownCount(
            count=len(
                [
                    i
                    for i in instruments
                    if i.evidence_level == EvidenceLevel.L1_EXTRACTED
                ]
            ),
            drilldown={"evidence_level": "L1_EXTRACTED"},
        ),
        "L2_BANK_CONFIRMED": DrilldownCount(
            count=len(
                [
                    i
                    for i in instruments
                    if i.evidence_level == EvidenceLevel.L2_BANK_CONFIRMED
                ]
            ),
            drilldown={"evidence_level": "L2_BANK_CONFIRMED"},
        ),
        "L3_LEDGER_RECONCILED": DrilldownCount(
            count=len(
                [
                    i
                    for i in instruments
                    if i.evidence_level == EvidenceLevel.L3_LEDGER_RECONCILED
                ]
            ),
            drilldown={"evidence_level": "L3_LEDGER_RECONCILED"},
        ),
    }

    return DashboardSummaryResponse(
        active=DrilldownCount(count=len(active_items), drilldown={"status": "active"}),
        expiring_30d=DrilldownCount(count=len(exp_30), drilldown={"expiring_days": 30}),
        expiring_60d=DrilldownCount(count=len(exp_60), drilldown={"expiring_days": 60}),
        expiring_90d=DrilldownCount(count=len(exp_90), drilldown={"expiring_days": 90}),
        matured=DrilldownCount(count=len(matured), drilldown={"status": "matured"}),
        renewed=DrilldownCount(count=len(renewed), drilldown={"status": "renewed"}),
        released=DrilldownCount(count=len(released), drilldown={"status": "released"}),
        pending_verification=DrilldownCount(
            count=len(pending_ver), drilldown={"status": "pending_verification"}
        ),
        open_observations=DrilldownCount(
            count=len(open_obs), drilldown={"status": "open"}
        ),
        awaiting_institution=DrilldownCount(
            count=len(awaiting_inst), drilldown={"status": "awaiting_institution"}
        ),
        reconciliation_exceptions=DrilldownCount(
            count=len(open_rec), drilldown={"status": "open"}
        ),
        release_by_stage=release_by_stage,
        overdue_and_ageing=overdue_and_ageing,
        evidence_distribution=evidence_distribution,
    )


@router.get("/my-work", response_model=list[WorkItem])
def get_my_work(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[WorkItem]:
    """Returns work items requiring current user/role action."""
    work_items: list[WorkItem] = []

    # 1. Scrutiny / Intake Queue items
    if principal.role in (
        AppRole.INTAKE_OFFICER,
        AppRole.SCRUTINY_OFFICER,
        AppRole.REGIONAL_SUPERVISOR,
    ):
        stmt = (
            select(Instrument)
            .where(Instrument.status == InstrumentStatus.SUBMITTED)
            .order_by(Instrument.created_at.desc())
            .limit(20)
        )
        items = db.execute(stmt).scalars().all()
        for i in items:
            work_items.append(
                WorkItem(
                    id=str(i.id),
                    item_type="instrument",
                    title=f"Review Deposit Submission {mask_identifier(i.instrument_number)}",
                    reference_id=mask_identifier(i.instrument_number),
                    status=i.status.value
                    if hasattr(i.status, "value")
                    else str(i.status),
                    priority="high" if i.amount > 5000000 else "medium",
                    created_at=i.created_at,
                    due_date=i.created_at + timedelta(days=7),
                    deep_link=f"/instruments/{i.id}",
                )
            )

    # 2. Bank confirmation requests
    if principal.role == AppRole.BANK_VERIFIER:
        stmt = (
            select(BankConfirmationRequest)
            .where(BankConfirmationRequest.status == "PENDING")
            .limit(20)
        )
        reqs = db.execute(stmt).scalars().all()
        for r in reqs:
            work_items.append(
                WorkItem(
                    id=str(r.id),
                    item_type="bank_confirmation",
                    title=f"Verify FDR Confirmation Request {r.reference_number}",
                    reference_id=r.reference_number,
                    status=r.status,
                    priority="high",
                    created_at=r.created_at,
                    due_date=r.expires_at,
                    deep_link=f"/verification/{r.id}",
                )
            )

    # 3. Release approvals
    if principal.role == AppRole.COMPETENT_AUTHORITY:
        stmt = (
            select(ReleaseRequest)
            .where(ReleaseRequest.status == "RECOMMENDED")
            .limit(20)
        )
        rels = db.execute(stmt).scalars().all()
        for rel in rels:
            work_items.append(
                WorkItem(
                    id=str(rel.id),
                    item_type="release_request",
                    title=f"Authorize Release Request {rel.id.hex[:8]}",
                    reference_id=str(rel.id.hex[:8]),
                    status="RECOMMENDED",
                    priority="high",
                    created_at=rel.created_at,
                    due_date=rel.created_at + timedelta(days=3),
                    deep_link=f"/release/{rel.id}",
                )
            )

    # 4. Org Admin / Submitter items: Drafts and open observations
    if (
        principal.role in (AppRole.ORG_ADMIN, AppRole.INSTITUTION_SUBMITTER)
        and principal.institution_id
    ):
        drafts = (
            db.execute(
                select(Instrument)
                .where(
                    Instrument.institution_id == principal.institution_id,
                    Instrument.status == InstrumentStatus.DRAFT,
                )
                .limit(10)
            )
            .scalars()
            .all()
        )
        for d in drafts:
            work_items.append(
                WorkItem(
                    id=str(d.id),
                    item_type="instrument_draft",
                    title=f"Complete Draft Submission {mask_identifier(d.instrument_number)}",
                    reference_id=mask_identifier(d.instrument_number),
                    status="DRAFT",
                    priority="medium",
                    created_at=d.created_at,
                    deep_link=f"/instruments/{d.id}/edit",
                )
            )

    return work_items


@router.get("/due-soon", response_model=list[DueSoonItem])
def get_due_soon(
    horizon_days: int = Query(30, ge=1, le=180),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[DueSoonItem]:
    """Returns instruments approaching maturity within specified horizon."""
    now = datetime.now(UTC)
    cutoff = now + timedelta(days=horizon_days)

    stmt = (
        select(Instrument)
        .where(
            Instrument.maturity_date.is_not(None),
            Instrument.maturity_date >= now,
            Instrument.maturity_date <= cutoff,
            Instrument.status.in_(
                [
                    InstrumentStatus.ACTIVE,
                    InstrumentStatus.SUBMITTED,
                    InstrumentStatus.VERIFIED,
                ]
            ),
        )
        .order_by(Instrument.maturity_date.asc())
        .limit(50)
    )

    stmt = _scope_instrument_stmt(stmt, principal)
    instruments = db.execute(stmt).scalars().all()

    return [
        DueSoonItem(
            id=str(i.id),
            instrument_number=mask_identifier(i.instrument_number),
            institution_id=str(i.institution_id),
            amount=float(i.amount),
            maturity_date=i.maturity_date,
            days_remaining=max(0, (i.maturity_date - now).days),
            status=i.status.value if hasattr(i.status, "value") else str(i.status),
        )
        for i in instruments
        if i.maturity_date
    ]


@router.get("/activity", response_model=list[ActivityItem])
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[ActivityItem]:
    """Returns recent audit events filtered by user scope."""
    stmt = select(AuditLog)
    if principal.institution_id:
        stmt = stmt.where(AuditLog.institution_id == principal.institution_id)
    stmt = stmt.order_by(desc(AuditLog.id)).limit(limit)

    entries = db.execute(stmt).scalars().all()
    return [
        ActivityItem(
            id=e.id,
            action=e.action,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            actor_id=str(e.actor_id) if e.actor_id else None,
            created_at=e.created_at,
        )
        for e in entries
    ]
