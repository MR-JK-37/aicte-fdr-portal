"""Release workflow API router (F-12 / SPEC §2.3, §6.1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.authz import Principal, StepUpRequiredError
from app.db import get_session
from app.models.core import AppUser
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    payload: CreateReleaseRequestPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        req = create_release_request(session, payload.instrument_id, user, payload.reason)
        session.commit()
        return {"id": str(req.id), "status": req.status, "instrument_id": str(req.instrument_id)}
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
        return {"id": str(c.id), "cell": c.cell, "status": c.status, "outcome": c.outcome}
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
        req = submit_recommendation(session, release_request_id, user, payload.recommendation, payload.reason)
        session.commit()
        return {"id": str(req.id), "status": req.status, "recommendation": req.recommendation}
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DelegationLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StepUpRequiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ChecklistIncompleteError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        return {"id": str(req.id), "status": req.status, "execution_evidence_ref": req.execution_evidence_ref}
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
