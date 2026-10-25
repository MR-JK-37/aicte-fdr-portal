"""Release workflow API router (F-12 / SPEC §2.3, §6.1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal, require_permission
from app.authz import (
    PermissionVerb,
    Principal,
    StepUpRequiredError,
    authorise_safe,
    mask_identifier,
)
from app.db import get_session
from app.models.core import AppUser, Institution, Instrument, ReleaseRequest
from app.models.workflow import Clearance, ReleaseChecklistItem
from app.problem_json import ForbiddenError, NotFoundError, UnprocessableEntityError
from app.release.service import (
    ChecklistIncompleteError,
    DelegationLimitExceededError,
    ExecutionReviewViolation,
    MakerCheckerViolation,
    ReleaseWorkflowError,
    create_release_request,
    decide_release,
    record_clearance_outcome,
    record_execution_evidence,
    submit_recommendation,
    update_checklist_item,
    verify_execution_and_discharge,
)

router = APIRouter(prefix="/v1/release-requests", tags=["release"])


class StepUpRequiredProblem(ForbiddenError):
    code = "step_up_required"
    title = "Step-up verification required"


class MakerCheckerProblem(ForbiddenError):
    code = "maker_checker_violation"
    title = "Maker-checker violation"


class DelegationLimitProblem(ForbiddenError):
    code = "delegation_limit_exceeded"
    title = "Delegation limit exceeded"


class ChecklistIncompleteProblem(UnprocessableEntityError):
    code = "checklist_incomplete"
    title = "Checklist incomplete"


class ReleaseRequestSummary(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    institution_name: str
    instrument_id: uuid.UUID
    instrument_number: str
    amount: Decimal
    status: str
    recommendation: str | None
    recommendation_reason: str | None
    recommended_at: datetime | None
    decision: str | None
    decision_reason: str | None
    created_at: datetime


class ReleaseChecklistItemOut(BaseModel):
    rule_id: str
    label: str
    status: str
    reason: str | None


class ClearanceOut(BaseModel):
    id: uuid.UUID
    cell: str
    source: str
    status: str
    outcome: str | None


class ReleaseRequestDetail(ReleaseRequestSummary):
    checklist: list[ReleaseChecklistItemOut]
    clearances: list[ClearanceOut]


class CreateReleaseRequestPayload(BaseModel):
    instrument_id: uuid.UUID
    reason: str


class UpdateChecklistItemPayload(BaseModel):
    status: str
    reason: str
    evidence_ref: str | None = None
    evidence_document_id: uuid.UUID | None = None


class RecordClearancePayload(BaseModel):
    status: str
    outcome: str
    notes: str | None = None
    evidence_document_id: uuid.UUID | None = None


class RecommendationPayload(BaseModel):
    recommendation: str
    reason: str


class DecisionPayload(BaseModel):
    decision: str
    reason: str
    step_up_token: str | None = None


class ExecutionEvidencePayload(BaseModel):
    execution_evidence_ref: str
    execution_document_id: uuid.UUID | None = None


def _build_summary(req: ReleaseRequest, inst: Instrument, institution: Institution, *, unmasked: bool) -> ReleaseRequestSummary:
    return ReleaseRequestSummary(
        id=req.id,
        institution_id=req.institution_id,
        institution_name=institution.name,
        instrument_id=req.instrument_id,
        instrument_number=inst.instrument_number if unmasked else mask_identifier(inst.instrument_number),
        amount=Decimal(str(inst.amount)).quantize(Decimal("0.01")),
        status=req.status,
        recommendation=req.recommendation,
        recommendation_reason=req.recommendation_reason,
        recommended_at=req.recommended_at,
        decision=req.decision,
        decision_reason=req.decision_reason,
        created_at=req.created_at,
    )


@router.get("", response_model=list[ReleaseRequestSummary])
def list_release_requests(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    session: Session = Depends(get_session),
) -> list[ReleaseRequestSummary]:
    """Lists release requests scoped to the caller's institution (or, for
    AICTE-staff roles with no institution_id, all institutions)."""
    stmt = select(ReleaseRequest)
    if principal.institution_id:
        stmt = stmt.where(ReleaseRequest.institution_id == principal.institution_id)
    if status_filter:
        stmt = stmt.where(ReleaseRequest.status == status_filter)
    stmt = stmt.order_by(desc(ReleaseRequest.created_at)).limit(limit).offset(offset)
    requests = session.execute(stmt).scalars().all()

    unmasked = authorise_safe(principal, PermissionVerb.VIEW_UNMASKED_IDENTIFIERS)

    out: list[ReleaseRequestSummary] = []
    for req in requests:
        inst = session.get(Instrument, req.instrument_id)
        institution = session.get(Institution, req.institution_id)
        if not inst or not institution:
            continue
        out.append(_build_summary(req, inst, institution, unmasked=unmasked))
    return out


@router.get("/{release_request_id}", response_model=ReleaseRequestDetail)
def get_release_request(
    release_request_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    session: Session = Depends(get_session),
) -> ReleaseRequestDetail:
    req = session.get(ReleaseRequest, release_request_id)
    # Cross-tenant ids return 404, never 403 (CLAUDE.md non-negotiable #6).
    if not req or (
        principal.institution_id and req.institution_id != principal.institution_id
    ):
        raise NotFoundError("Release request", release_request_id)

    inst = session.get(Instrument, req.instrument_id)
    institution = session.get(Institution, req.institution_id)
    if not inst or not institution:
        raise NotFoundError("Release request", release_request_id)

    unmasked = authorise_safe(principal, PermissionVerb.VIEW_UNMASKED_IDENTIFIERS)

    summary = _build_summary(req, inst, institution, unmasked=unmasked)

    checklist_items = (
        session.execute(
            select(ReleaseChecklistItem).where(
                ReleaseChecklistItem.release_request_id == release_request_id
            )
        )
        .scalars()
        .all()
    )
    clearances = (
        session.execute(
            select(Clearance).where(
                Clearance.release_request_id == release_request_id
            )
        )
        .scalars()
        .all()
    )

    return ReleaseRequestDetail(
        **summary.model_dump(),
        checklist=[
            ReleaseChecklistItemOut(
                rule_id=c.rule_id, label=c.label, status=c.status, reason=c.reason
            )
            for c in checklist_items
        ],
        clearances=[
            ClearanceOut(
                id=c.id, cell=c.cell, source=c.source, status=c.status, outcome=c.outcome
            )
            for c in clearances
        ],
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    payload: CreateReleaseRequestPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        req = create_release_request(
            session, payload.instrument_id, user, payload.reason
        )
        session.commit()
        return {
            "id": str(req.id),
            "status": req.status,
            "instrument_id": str(req.instrument_id),
        }
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{release_request_id}/checklist/{rule_id}")
def update_checklist(
    release_request_id: uuid.UUID,
    rule_id: str,
    payload: UpdateChecklistItemPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        item = update_checklist_item(
            session,
            release_request_id,
            rule_id,
            payload.status,
            user,
            reason=payload.reason,
            evidence_ref=payload.evidence_ref,
            evidence_document_id=payload.evidence_document_id,
        )
        session.commit()
        return {"id": str(item.id), "rule_id": item.rule_id, "status": item.status}
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/clearances/{clearance_id}")
def record_clearance(
    clearance_id: uuid.UUID,
    payload: RecordClearancePayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        c = record_clearance_outcome(
            session,
            clearance_id,
            payload.status,
            payload.outcome,
            user,
            evidence_document_id=payload.evidence_document_id,
            notes=payload.notes,
        )
        session.commit()
        return {
            "id": str(c.id),
            "cell": c.cell,
            "status": c.status,
            "outcome": c.outcome,
        }
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{release_request_id}/recommendation")
def submit_rec(
    release_request_id: uuid.UUID,
    payload: RecommendationPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        req = submit_recommendation(
            session, release_request_id, user, payload.recommendation, payload.reason
        )
        session.commit()
        return {
            "id": str(req.id),
            "status": req.status,
            "recommendation": req.recommendation,
        }
    except MakerCheckerViolation as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{release_request_id}/decision")
def decide(
    release_request_id: uuid.UUID,
    payload: DecisionPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        req = decide_release(
            session,
            release_request_id,
            user,
            payload.decision,
            payload.reason,
            step_up_token=payload.step_up_token,
        )
        session.commit()
        return {"id": str(req.id), "status": req.status, "decision": req.decision}
    except MakerCheckerViolation as e:
        raise MakerCheckerProblem(str(e))
    except DelegationLimitExceededError as e:
        raise DelegationLimitProblem(str(e))
    except StepUpRequiredError as e:
        raise StepUpRequiredProblem(str(e))
    except ChecklistIncompleteError as e:
        raise ChecklistIncompleteProblem(str(e))
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{release_request_id}/execution")
def record_execution(
    release_request_id: uuid.UUID,
    payload: ExecutionEvidencePayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        req = record_execution_evidence(
            session,
            release_request_id,
            user,
            execution_evidence_ref=payload.execution_evidence_ref,
            execution_document_id=payload.execution_document_id,
        )
        session.commit()
        return {
            "id": str(req.id),
            "status": req.status,
            "execution_evidence_ref": req.execution_evidence_ref,
        }
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{release_request_id}/discharge")
def discharge(
    release_request_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        req = verify_execution_and_discharge(session, release_request_id, user)
        session.commit()
        return {"id": str(req.id), "status": req.status}
    except ExecutionReviewViolation as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ReleaseWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
