"""Workload Queues and Case Assignment Router (F-24)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal, mask_identifier
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import InstrumentStatus
from app.models.workflow import CaseAssignment, InstitutionOnboardingRequest
from app.outbox.producer import enqueue_outbox_event
from app.problem_json import NotFoundError

router = APIRouter(prefix="/v1/queues", tags=["Queues & Workload"])


# --- Schemas ---
class AssignCaseRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: uuid.UUID
    queue_name: str = Field(..., min_length=2, max_length=64)
    assigned_to_user_id: uuid.UUID
    notes: str | None = Field(None, max_length=1024)


class CaseAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    queue_name: str
    assigned_to: uuid.UUID
    assigned_by: uuid.UUID
    status: str
    notes: str | None = None
    created_at: datetime


class QueueItem(BaseModel):
    case_id: uuid.UUID
    entity_type: str
    title: str
    institution_id: uuid.UUID
    institution_name: str
    status: str
    created_at: datetime
    assigned_to_user_id: uuid.UUID | None = None


# --- Endpoints ---
@router.get("/intake", response_model=list[QueueItem])
def get_intake_queue(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[QueueItem]:
    """Intake Queue: Pending onboarding requests and new submissions awaiting intake review."""
    items: list[QueueItem] = []

    # 1. Onboarding requests
    onboarding_reqs = db.execute(
        select(InstitutionOnboardingRequest, Institution)
        .join(
            Institution, Institution.id == InstitutionOnboardingRequest.institution_id
        )
        .where(InstitutionOnboardingRequest.status == "PENDING")
        .order_by(InstitutionOnboardingRequest.created_at.asc())
    ).all()

    for req, inst in onboarding_reqs:
        items.append(
            QueueItem(
                case_id=req.id,
                entity_type="onboarding_request",
                title=f"Onboarding: {inst.name} ({inst.aicte_code})",
                institution_id=inst.id,
                institution_name=inst.name,
                status=req.status,
                created_at=req.created_at,
            )
        )

    # 2. Submitted instruments awaiting intake review
    instruments = db.execute(
        select(Instrument, Institution)
        .join(Institution, Institution.id == Instrument.institution_id)
        .where(
            Instrument.status.in_(
                [InstrumentStatus.SUBMITTED, InstrumentStatus.INTAKE_REVIEW]
            )
        )
        .order_by(Instrument.created_at.asc())
    ).all()

    for inst_record, inst in instruments:
        # Check active assignment
        assignment = db.execute(
            select(CaseAssignment)
            .where(
                CaseAssignment.case_id == inst_record.id,
                CaseAssignment.queue_name == "intake",
                CaseAssignment.status == "ACTIVE",
            )
            .limit(1)
        ).scalar_one_or_none()

        items.append(
            QueueItem(
                case_id=inst_record.id,
                entity_type="instrument",
                title=f"{inst_record.type.value} ({mask_identifier(inst_record.instrument_number)}) - ₹ {inst_record.amount:,.2f}",
                institution_id=inst.id,
                institution_name=inst.name,
                status=inst_record.status.value,
                created_at=inst_record.created_at,
                assigned_to_user_id=assignment.assigned_to if assignment else None,
            )
        )

    return items


@router.get("/scrutiny", response_model=list[QueueItem])
def get_scrutiny_queue(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[QueueItem]:
    """Scrutiny Queue: Instruments currently under scrutiny."""
    instruments = db.execute(
        select(Instrument, Institution)
        .join(Institution, Institution.id == Instrument.institution_id)
        .where(
            Instrument.status.in_(
                [InstrumentStatus.SCRUTINY, InstrumentStatus.UNDER_SCRUTINY]
            )
        )
        .order_by(Instrument.created_at.asc())
    ).all()

    items: list[QueueItem] = []
    for inst_record, inst in instruments:
        assignment = db.execute(
            select(CaseAssignment)
            .where(
                CaseAssignment.case_id == inst_record.id,
                CaseAssignment.queue_name == "scrutiny",
                CaseAssignment.status == "ACTIVE",
            )
            .limit(1)
        ).scalar_one_or_none()

        items.append(
            QueueItem(
                case_id=inst_record.id,
                entity_type="instrument",
                title=f"{inst_record.type.value} ({mask_identifier(inst_record.instrument_number)}) - ₹ {inst_record.amount:,.2f}",
                institution_id=inst.id,
                institution_name=inst.name,
                status=inst_record.status.value,
                created_at=inst_record.created_at,
                assigned_to_user_id=assignment.assigned_to if assignment else None,
            )
        )

    return items


@router.post(
    "/assign",
    response_model=CaseAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_case_to_officer(
    payload: AssignCaseRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.ASSIGN_CASE)),
    db: Session = Depends(get_db),
) -> CaseAssignmentResponse:
    """Assigns or reassigns a case to an officer (F-24)."""
    # Verify assignee exists and is active
    assignee = db.execute(
        select(AppUser).where(AppUser.id == payload.assigned_to_user_id)
    ).scalar_one_or_none()
    if not assignee or not assignee.is_active:
        raise NotFoundError("AppUser", payload.assigned_to_user_id)

    # Complete previous active assignment on this case & queue if any
    prev_assignments = (
        db.execute(
            select(CaseAssignment).where(
                CaseAssignment.case_id == payload.case_id,
                CaseAssignment.queue_name == payload.queue_name,
                CaseAssignment.status == "ACTIVE",
            )
        )
        .scalars()
        .all()
    )
    for prev in prev_assignments:
        prev.status = "REASSIGNED"
        prev.completed_at = datetime.now(UTC)

    new_assignment = CaseAssignment(
        id=uuid.uuid4(),
        case_id=payload.case_id,
        queue_name=payload.queue_name,
        assigned_to=payload.assigned_to_user_id,
        assigned_by=principal.id,
        status="ACTIVE",
        notes=payload.notes,
    )
    db.add(new_assignment)
    db.flush()

    append_audit_entry(
        db,
        action="case.assigned",
        entity_type="case",
        entity_id=str(payload.case_id),
        after={
            "queue_name": payload.queue_name,
            "assigned_to": str(payload.assigned_to_user_id),
            "assigned_by": str(principal.id),
            "notes": payload.notes,
        },
        actor_id=str(principal.id),
    )

    enqueue_outbox_event(
        db,
        aggregate_type="case_assignment",
        aggregate_id=new_assignment.id,
        event_type="case.assigned",
        payload={
            "case_id": str(payload.case_id),
            "queue_name": payload.queue_name,
            "assigned_to": str(payload.assigned_to_user_id),
        },
        dedupe_key=f"case.assigned:{new_assignment.id}",
    )

    res = CaseAssignmentResponse.model_validate(new_assignment)
    db.commit()
    return res
