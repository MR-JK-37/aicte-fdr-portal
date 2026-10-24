"""Bank Confirmation & Evidence Decision Router (F-06 / SPEC §18.1 Scenario 4).

Features:
1. Bank confirmation request issuance with tracking numbers.
2. Participating Bank Verifier role isolation (assigned bank only, sender identity verification).
3. Evidence decision with Separation of Duties (requester cannot decide).
4. Inconclusive responses automatically open ReconciliationException (never fraud label).
5. Overdue escalation notifications without automatic rejection.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal, SeparationOfDutiesError
from app.models.core import Instrument, VerificationRecord
from app.models.enums import BUREAU_SIDE_ROLES, AppRole, EvidenceLevel
from app.models.workflow import BankConfirmationRequest, ReconciliationException
from app.problem_json import ForbiddenError, NotFoundError

router = APIRouter(prefix="/v1/verification", tags=["Bank Verification"])


# --- Schemas ---
class CreateBankConfirmationRequest(BaseModel):
    instrument_id: uuid.UUID
    bank_name: str
    branch_name: str | None = None
    ifsc: str | None = None
    account_number_ref: str | None = None
    assigned_bank_verifier_id: uuid.UUID | None = None
    notes: str | None = None


class BankConfirmationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    instrument_id: uuid.UUID
    bank_name: str
    branch_name: str | None = None
    ifsc: str | None = None
    account_number_ref: str | None = None
    tracking_number: str
    status: str
    requested_by: uuid.UUID
    requested_at: datetime
    assigned_bank_verifier_id: uuid.UUID | None = None
    response_document_id: uuid.UUID | None = None
    response_payload: dict
    response_notes: str | None = None
    responded_at: datetime | None = None
    decided_by: uuid.UUID | None = None
    decision: str | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BankResponseSubmission(BaseModel):
    confirmed_fields: dict[str, Any] = Field(default_factory=dict)
    response_document_id: uuid.UUID | None = None
    notes: str | None = None


class EvidenceDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPT|REJECT|INCONCLUSIVE)$")
    reason: str = Field(..., min_length=1)


class EscalateRequest(BaseModel):
    reason: str = "Bank confirmation request overdue"


# --- Endpoints ---
@router.post(
    "/bank-requests",
    response_model=BankConfirmationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bank_confirmation_request(
    payload: CreateBankConfirmationRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> BankConfirmationResponse:
    """Finance or Scrutiny officer issues a bank confirmation request (F-06)."""
    if principal.role not in BUREAU_SIDE_ROLES and principal.role != AppRole.ORG_ADMIN:
        raise ForbiddenError(
            "Only bureau officials can issue bank confirmation requests"
        )

    instrument = db.execute(
        select(Instrument).where(Instrument.id == payload.instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", payload.instrument_id)

    req_id = uuid.uuid4()
    tracking_number = f"BCR-2026-{uuid.uuid4().hex[:8].upper()}"

    request = BankConfirmationRequest(
        id=req_id,
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        bank_name=payload.bank_name,
        branch_name=payload.branch_name,
        ifsc=payload.ifsc,
        account_number_ref=payload.account_number_ref,
        tracking_number=tracking_number,
        status="AWAITING_RESPONSE",
        requested_by=principal.id,
        assigned_bank_verifier_id=payload.assigned_bank_verifier_id,
        response_payload={},
        response_notes=payload.notes,
    )
    db.add(request)
    db.flush()

    append_audit_entry(
        db,
        action="verification.bank_confirmation_requested",
        entity_type="bank_confirmation_request",
        entity_id=str(req_id),
        after={
            "tracking_number": tracking_number,
            "bank_name": payload.bank_name,
            "instrument_id": str(instrument.id),
        },
        actor_id=str(principal.id),
        institution_id=str(instrument.institution_id),
    )

    res = BankConfirmationResponse.model_validate(request)
    db.commit()
    return res


@router.get("/bank-requests", response_model=list[BankConfirmationResponse])
def list_bank_confirmation_requests(
    instrument_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[BankConfirmationResponse]:
    """Lists bank confirmation requests with strict role and tenant isolation (F-06)."""
    stmt = select(BankConfirmationRequest)

    if instrument_id:
        stmt = stmt.where(BankConfirmationRequest.instrument_id == instrument_id)
    if status_filter:
        stmt = stmt.where(BankConfirmationRequest.status == status_filter)

    if principal.role == AppRole.BANK_VERIFIER:
        bank_scope = (principal.role_scope or {}).get("bank_name")
        if bank_scope:
            stmt = stmt.where(
                (BankConfirmationRequest.assigned_bank_verifier_id == principal.id)
                | (BankConfirmationRequest.bank_name == bank_scope)
            )
        else:
            stmt = stmt.where(
                BankConfirmationRequest.assigned_bank_verifier_id == principal.id
            )
    elif principal.institution_id:
        stmt = stmt.where(
            BankConfirmationRequest.institution_id == principal.institution_id
        )

    stmt = stmt.order_by(BankConfirmationRequest.created_at.desc())
    rows = list(db.execute(stmt).scalars().all())
    return [BankConfirmationResponse.model_validate(r) for r in rows]


@router.get(
    "/bank-requests/{request_id}",
    response_model=BankConfirmationResponse,
)
def get_bank_confirmation_request(
    request_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> BankConfirmationResponse:
    """Fetches single bank confirmation request with isolation enforcement."""
    req = db.execute(
        select(BankConfirmationRequest).where(BankConfirmationRequest.id == request_id)
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("BankConfirmationRequest", request_id)

    if principal.role == AppRole.BANK_VERIFIER:
        bank_scope = (principal.role_scope or {}).get("bank_name")
        is_assigned = req.assigned_bank_verifier_id == principal.id
        is_matching_bank = bank_scope and req.bank_name == bank_scope
        if not (is_assigned or is_matching_bank):
            raise ForbiddenError("Bank verifier cannot access requests for other banks")
    elif principal.institution_id:
        if req.institution_id != principal.institution_id:
            raise ForbiddenError("Cannot access requests of another institution")

    return BankConfirmationResponse.model_validate(req)


@router.post(
    "/bank-requests/{request_id}/respond",
    response_model=BankConfirmationResponse,
)
def respond_to_bank_request(
    request_id: uuid.UUID,
    payload: BankResponseSubmission,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> BankConfirmationResponse:
    """Submits response from bank verifier or records official bank reply (F-06).
    Rejects response if sender identity cannot be verified.
    """
    req = db.execute(
        select(BankConfirmationRequest).where(BankConfirmationRequest.id == request_id)
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("BankConfirmationRequest", request_id)

    if principal.role == AppRole.BANK_VERIFIER:
        bank_scope = (principal.role_scope or {}).get("bank_name")
        is_assigned = req.assigned_bank_verifier_id == principal.id
        is_matching_bank = bank_scope and req.bank_name == bank_scope
        if not (is_assigned or is_matching_bank):
            raise ForbiddenError(
                "Response rejected: sender identity is not authorized for this bank request"
            )
    elif principal.role not in BUREAU_SIDE_ROLES:
        raise ForbiddenError(
            "Only assigned bank verifiers or bureau officers can submit bank replies"
        )

    req.status = "UNDER_REVIEW"
    req.response_payload = payload.confirmed_fields
    req.response_document_id = payload.response_document_id
    req.response_notes = payload.notes
    req.responded_at = datetime.now(UTC)

    append_audit_entry(
        db,
        action="verification.bank_confirmation_responded",
        entity_type="bank_confirmation_request",
        entity_id=str(req.id),
        after={
            "status": req.status,
            "response_document_id": str(payload.response_document_id)
            if payload.response_document_id
            else None,
            "confirmed_fields": list(payload.confirmed_fields.keys()),
        },
        actor_id=str(principal.id),
        institution_id=str(req.institution_id),
    )

    res = BankConfirmationResponse.model_validate(req)
    db.commit()
    return res


@router.post(
    "/bank-requests/{request_id}/decision",
    response_model=BankConfirmationResponse,
)
def decide_bank_evidence(
    request_id: uuid.UUID,
    payload: EvidenceDecisionRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.VERIFY_BANK_EVIDENCE)
    ),
    db: Session = Depends(get_db),
) -> BankConfirmationResponse:
    """Independent reviewer decision on bank evidence (F-06 / SPEC §18.1 Scenario 4).
    Enforces Separation of Duties: requester != decider.
    ACCEPT -> L2_BANK_CONFIRMED.
    REJECT -> REJECTED.
    INCONCLUSIVE -> INCONCLUSIVE (opens ReconciliationException, never fraud).
    """
    req = db.execute(
        select(BankConfirmationRequest).where(BankConfirmationRequest.id == request_id)
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("BankConfirmationRequest", request_id)

    # Separation of Duties: Requester cannot decide on their own confirmation request
    if str(req.requested_by) == str(principal.id):
        raise SeparationOfDutiesError(
            "Requester cannot decide on their own bank confirmation request"
        )

    instrument = db.execute(
        select(Instrument).where(Instrument.id == req.instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", req.instrument_id)

    req.decision = payload.decision
    req.decision_reason = payload.reason
    req.decided_by = principal.id
    req.decided_at = datetime.now(UTC)

    if payload.decision == "ACCEPT":
        req.status = "ACCEPTED"
        before_level = instrument.evidence_level
        instrument.evidence_level = EvidenceLevel.L2_BANK_CONFIRMED

        confirmed_amount = None
        if "amount" in req.response_payload:
            try:
                confirmed_amount = float(req.response_payload["amount"])
            except (ValueError, TypeError):
                confirmed_amount = float(instrument.amount)
        else:
            confirmed_amount = float(instrument.amount)

        v_record = VerificationRecord(
            id=uuid.uuid4(),
            institution_id=instrument.institution_id,
            instrument_id=instrument.id,
            level=EvidenceLevel.L2_BANK_CONFIRMED,
            source="bank_confirmation",
            confirmed_amount=confirmed_amount,
            raw_payload={
                "bank_name": req.bank_name,
                "tracking_number": req.tracking_number,
                "response_payload": req.response_payload,
                "decision_reason": payload.reason,
            },
        )
        db.add(v_record)

        append_audit_entry(
            db,
            action="instrument.evidence_level_confirmed",
            entity_type="instrument",
            entity_id=str(instrument.id),
            before={"evidence_level": before_level.value},
            after={
                "evidence_level": EvidenceLevel.L2_BANK_CONFIRMED.value,
                "reason": payload.reason,
                "tracking_number": req.tracking_number,
                "bank_name": req.bank_name,
            },
            actor_id=str(principal.id),
            institution_id=str(instrument.institution_id),
        )

    elif payload.decision == "REJECT":
        req.status = "REJECTED"

    elif payload.decision == "INCONCLUSIVE":
        req.status = "INCONCLUSIVE"
        # INCONCLUSIVE opens a reconciliation/verification exception, NOT a fraud label
        exc_id = uuid.uuid4()
        exception = ReconciliationException(
            id=exc_id,
            instrument_id=instrument.id,
            exception_type="INCONCLUSIVE_BANK_CONFIRMATION",
            details={
                "request_id": str(req.id),
                "tracking_number": req.tracking_number,
                "bank_name": req.bank_name,
                "reason": payload.reason,
                "response_payload": req.response_payload,
            },
            status="OPEN",
        )
        db.add(exception)

        append_audit_entry(
            db,
            action="verification.reconciliation_exception_opened",
            entity_type="reconciliation_exception",
            entity_id=str(exc_id),
            after={
                "exception_type": "INCONCLUSIVE_BANK_CONFIRMATION",
                "instrument_id": str(instrument.id),
                "tracking_number": req.tracking_number,
                "reason": payload.reason,
            },
            actor_id=str(principal.id),
            institution_id=str(instrument.institution_id),
        )

    append_audit_entry(
        db,
        action="verification.bank_confirmation_decided",
        entity_type="bank_confirmation_request",
        entity_id=str(req.id),
        after={
            "status": req.status,
            "decision": req.decision,
            "decision_reason": payload.reason,
        },
        actor_id=str(principal.id),
        institution_id=str(req.institution_id),
    )

    res = BankConfirmationResponse.model_validate(req)
    db.commit()
    return res


@router.post(
    "/bank-requests/{request_id}/escalate",
    response_model=BankConfirmationResponse,
)
def escalate_overdue_bank_request(
    request_id: uuid.UUID,
    payload: EscalateRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> BankConfirmationResponse:
    """Overdue bank confirmation escalation (MASTER_PROMPT §F-06).
    Emits an escalation audit notification.
    CRITICAL: Does NOT change status to REJECTED. Request remains AWAITING_RESPONSE.
    """
    req = db.execute(
        select(BankConfirmationRequest).where(BankConfirmationRequest.id == request_id)
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("BankConfirmationRequest", request_id)

    append_audit_entry(
        db,
        action="verification.bank_confirmation_escalated",
        entity_type="bank_confirmation_request",
        entity_id=str(req.id),
        after={
            "tracking_number": req.tracking_number,
            "reason": payload.reason,
            "status": req.status,  # Stays AWAITING_RESPONSE
        },
        actor_id=str(principal.id),
        institution_id=str(req.institution_id),
    )

    res = BankConfirmationResponse.model_validate(req)
    db.commit()
    return res
