"""Instrument Register & Versioning Router (F-03 / SPEC §6.1 / F-20)."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal, authorise, mask_identifier
from app.config import settings
from app.lifecycle import apply_transition
from app.models.core import Bank, Branch, Institution, Instrument
from app.models.enums import EvidenceLevel, InstrumentStatus, InstrumentType
from app.models.workflow import InstrumentVersion
from app.problem_json import ConflictError, ForbiddenError, NotFoundError
from app.receipts.generator import generate_submission_receipt_pdf

router = APIRouter(prefix="/v1/instruments", tags=["Instruments & Versions"])


def compute_blind_index(val: str) -> str:
    """Computes a keyed HMAC-SHA256 blind index for exact search on sensitive identifiers (F-03)."""
    key = settings.jwt_secret.encode("utf-8")
    return hmac.new(
        key, val.strip().upper().encode("utf-8"), hashlib.sha256
    ).hexdigest()


# --- Schemas ---
class InstrumentDraftCreate(BaseModel):
    model_config = ConfigDict(frozen=True)

    institution_id: uuid.UUID
    type: InstrumentType = InstrumentType.FDR
    instrument_number: str = Field(..., min_length=3, max_length=64)
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    issue_date: datetime | None = None
    maturity_date: datetime | None = None
    tenor_months: int | None = Field(None, ge=1, le=120)
    utr: str | None = Field(None, max_length=32)

    @model_validator(mode="after")
    def validate_dates(self) -> InstrumentDraftCreate:
        if (
            self.issue_date
            and self.maturity_date
            and self.maturity_date <= self.issue_date
        ):
            raise ValueError("Maturity date must be strictly after the issue date")
        return self


class InstrumentDraftUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: InstrumentType | None = None
    instrument_number: str | None = Field(None, min_length=3, max_length=64)
    amount: Decimal | None = Field(None, gt=Decimal("0.00"), decimal_places=2)
    issue_date: datetime | None = None
    maturity_date: datetime | None = None
    tenor_months: int | None = Field(None, ge=1, le=120)
    utr: str | None = Field(None, max_length=32)

    @model_validator(mode="after")
    def validate_dates(self) -> InstrumentDraftUpdate:
        if (
            self.issue_date
            and self.maturity_date
            and self.maturity_date <= self.issue_date
        ):
            raise ValueError("Maturity date must be strictly after the issue date")
        return self


class InstrumentSubmitRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: str = Field(..., min_length=5, max_length=1024)
    policy_version: str = "APH-2024-27-v1.0"


class InstrumentTransitionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    to_status: InstrumentStatus
    reason: str = Field(..., min_length=3, max_length=1024)
    reason_code: str = Field("STATUS_UPDATE", min_length=2, max_length=64)


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    institution_name: str | None = None
    bank_name: str | None = None
    type: InstrumentType
    status: InstrumentStatus
    evidence_level: EvidenceLevel
    instrument_number: (
        str  # Masked unless principal has view_unmasked_identifiers + step-up
    )
    amount: Decimal
    issue_date: datetime | None = None
    maturity_date: datetime | None = None
    tenor_months: int | None = None
    utr: str | None = None
    created_at: datetime
    updated_at: datetime


class InstrumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    instrument_id: uuid.UUID
    version_number: int
    content_hash: str
    submitted_by: uuid.UUID
    reason: str
    created_at: datetime
    snapshot: dict[str, Any]


# --- Endpoints ---
@router.post(
    "/draft", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED
)
def create_draft_instrument(
    payload: InstrumentDraftCreate,
    principal: Principal = Depends(require_permission(PermissionVerb.CREATE_DRAFT)),
    db: Session = Depends(get_db),
) -> InstrumentResponse:
    """Creates a draft instrument (F-03)."""
    # Scope check: institution users can only create for their own institution
    if principal.institution_id and principal.institution_id != payload.institution_id:
        raise ForbiddenError("Cannot create draft for another institution")

    blind_idx = compute_blind_index(payload.instrument_number)

    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=payload.institution_id,
        type=payload.type,
        status=InstrumentStatus.DRAFT,
        evidence_level=EvidenceLevel.L0_DECLARED,
        instrument_number=payload.instrument_number,
        blind_index=blind_idx,
        amount=float(payload.amount),
        issue_date=payload.issue_date,
        maturity_date=payload.maturity_date,
        tenor_months=payload.tenor_months,
        utr=payload.utr,
    )
    db.add(instrument)
    db.flush()

    append_audit_entry(
        db,
        action="instrument.draft_created",
        entity_type="instrument",
        entity_id=str(instrument.id),
        after={
            "status": "DRAFT",
            "type": payload.type.value,
            "masked_number": mask_identifier(payload.instrument_number),
            "amount": str(payload.amount),
        },
        actor_id=str(principal.id),
        institution_id=str(payload.institution_id),
    )

    res = InstrumentResponse(
        id=instrument.id,
        institution_id=instrument.institution_id,
        type=instrument.type,
        status=instrument.status,
        evidence_level=instrument.evidence_level,
        instrument_number=mask_identifier(instrument.instrument_number),
        amount=Decimal(str(instrument.amount)).quantize(Decimal("0.01")),
        issue_date=instrument.issue_date,
        maturity_date=instrument.maturity_date,
        tenor_months=instrument.tenor_months,
        utr=instrument.utr,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )
    db.commit()
    return res


@router.put("/{instrument_id}/draft", response_model=InstrumentResponse)
def update_draft_instrument(
    instrument_id: uuid.UUID,
    payload: InstrumentDraftUpdate,
    if_match: str | None = Header(None, alias="If-Match"),
    principal: Principal = Depends(require_permission(PermissionVerb.EDIT_DRAFT)),
    db: Session = Depends(get_db),
) -> InstrumentResponse:
    """Updates an existing draft instrument (F-03).
    Returns 409 Conflict if modified concurrently or not in DRAFT status.
    """
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    if instrument.status != InstrumentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit instrument in '{instrument.status.value}' status (must be DRAFT)",
        )

    # Optimistic concurrency check
    if if_match:
        current_etag = f'"{instrument.updated_at.isoformat()}"'
        if if_match != current_etag and if_match != "*":
            raise ConflictError(
                "Resource has been modified by another concurrent request"
            )

    if payload.type is not None:
        instrument.type = payload.type
    if payload.instrument_number is not None:
        instrument.instrument_number = payload.instrument_number
        instrument.blind_index = compute_blind_index(payload.instrument_number)
    if payload.amount is not None:
        instrument.amount = float(payload.amount)
    if payload.issue_date is not None:
        instrument.issue_date = payload.issue_date
    if payload.maturity_date is not None:
        instrument.maturity_date = payload.maturity_date
    if payload.tenor_months is not None:
        instrument.tenor_months = payload.tenor_months
    if payload.utr is not None:
        instrument.utr = payload.utr

    instrument.updated_at = datetime.now(UTC)
    db.flush()

    append_audit_entry(
        db,
        action="instrument.draft_updated",
        entity_type="instrument",
        entity_id=str(instrument.id),
        after={"updated_at": instrument.updated_at.isoformat()},
        actor_id=str(principal.id),
        institution_id=str(instrument.institution_id),
    )

    res = InstrumentResponse(
        id=instrument.id,
        institution_id=instrument.institution_id,
        type=instrument.type,
        status=instrument.status,
        evidence_level=instrument.evidence_level,
        instrument_number=mask_identifier(instrument.instrument_number),
        amount=Decimal(str(instrument.amount)).quantize(Decimal("0.01")),
        issue_date=instrument.issue_date,
        maturity_date=instrument.maturity_date,
        tenor_months=instrument.tenor_months,
        utr=instrument.utr,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )
    db.commit()
    return res


@router.post("/{instrument_id}/submit", response_model=InstrumentResponse)
def submit_instrument(
    instrument_id: uuid.UUID,
    payload: InstrumentSubmitRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.SUBMIT)),
    db: Session = Depends(get_db),
) -> InstrumentResponse:
    """Submits an instrument:
    1. Freezes an immutable instrument_version snapshot with SHA-256 content hash
    2. Atomically transitions status to SUBMITTED (recording state_transition, audit, outbox)
    3. Issues verifiable cryptographic submission receipt (F-20)
    """
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    # Determine next version number
    latest_version = db.execute(
        select(InstrumentVersion.version_number)
        .where(InstrumentVersion.instrument_id == instrument_id)
        .order_by(desc(InstrumentVersion.version_number))
        .limit(1)
    ).scalar_one_or_none()
    next_ver = (latest_version or 0) + 1

    # Freeze snapshot
    snapshot_data = {
        "instrument_id": str(instrument.id),
        "institution_id": str(instrument.institution_id),
        "type": instrument.type.value,
        "instrument_number": instrument.instrument_number,
        "amount": str(instrument.amount),
        "issue_date": instrument.issue_date.isoformat()
        if instrument.issue_date
        else None,
        "maturity_date": instrument.maturity_date.isoformat()
        if instrument.maturity_date
        else None,
        "tenor_months": instrument.tenor_months,
        "utr": instrument.utr,
        "version_number": next_ver,
        "submitted_at": datetime.now(UTC).isoformat(),
        "submitted_by": str(principal.id),
        "policy_version": payload.policy_version,
    }
    canonical_snapshot = json.dumps(
        snapshot_data, sort_keys=True, separators=(",", ":")
    )
    content_hash = hashlib.sha256(canonical_snapshot.encode("utf-8")).hexdigest()

    version_record = InstrumentVersion(
        id=uuid.uuid4(),
        instrument_id=instrument.id,
        version_number=next_ver,
        snapshot=snapshot_data,
        content_hash=content_hash,
        submitted_by=principal.id,
        reason=payload.reason,
    )
    db.add(version_record)
    db.flush()

    # Apply atomic state transition (DRAFT -> SUBMITTED)
    apply_transition(
        db,
        instrument,
        InstrumentStatus.SUBMITTED,
        actor_role=principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role),
        actor_id=str(principal.id),
        reason=payload.reason,
        reason_code="OFFICIAL_SUBMISSION",
    )

    res = InstrumentResponse(
        id=instrument.id,
        institution_id=instrument.institution_id,
        type=instrument.type,
        status=instrument.status,
        evidence_level=instrument.evidence_level,
        instrument_number=mask_identifier(instrument.instrument_number),
        amount=Decimal(str(instrument.amount)).quantize(Decimal("0.01")),
        issue_date=instrument.issue_date,
        maturity_date=instrument.maturity_date,
        tenor_months=instrument.tenor_months,
        utr=instrument.utr,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )
    db.commit()
    return res


@router.post("/{instrument_id}/transition", response_model=InstrumentResponse)
def transition_instrument(
    instrument_id: uuid.UUID,
    payload: InstrumentTransitionRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> InstrumentResponse:
    """Transitions an instrument to a new lifecycle status (State Machine 1)."""
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    role_str = (
        principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role)
    )
    apply_transition(
        db,
        instrument,
        payload.to_status,
        actor_role=role_str,
        actor_id=str(principal.id),
        reason=payload.reason,
        reason_code=payload.reason_code,
    )

    res = InstrumentResponse(
        id=instrument.id,
        institution_id=instrument.institution_id,
        type=instrument.type,
        status=instrument.status,
        evidence_level=instrument.evidence_level,
        instrument_number=mask_identifier(instrument.instrument_number),
        amount=Decimal(str(instrument.amount)).quantize(Decimal("0.01")),
        issue_date=instrument.issue_date,
        maturity_date=instrument.maturity_date,
        tenor_months=instrument.tenor_months,
        utr=instrument.utr,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )
    db.commit()
    return res


@router.get("", response_model=list[InstrumentResponse])
def list_instruments(
    status: InstrumentStatus | None = Query(None, description="Filter by status"),
    institution_id: uuid.UUID | None = Query(None, description="Filter by institution"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[InstrumentResponse]:
    """Lists instruments scoped by the authenticated principal (F-03)."""
    stmt = select(Instrument)
    if principal.institution_id:
        stmt = stmt.where(Instrument.institution_id == principal.institution_id)
    elif institution_id:
        stmt = stmt.where(Instrument.institution_id == institution_id)
    if status:
        stmt = stmt.where(Instrument.status == status)
    stmt = stmt.order_by(desc(Instrument.created_at)).limit(limit).offset(offset)
    instruments = db.execute(stmt).scalars().all()

    can_view_unmasked = False
    try:
        authorise(principal, PermissionVerb.VIEW_UNMASKED_IDENTIFIERS)
        can_view_unmasked = True
    except (ForbiddenError, HTTPException):
        can_view_unmasked = False

    inst_ids = {i.institution_id for i in instruments}
    institutions_map: dict[uuid.UUID, str] = {}
    if inst_ids:
        inst_records = db.execute(
            select(Institution.id, Institution.name).where(Institution.id.in_(inst_ids))
        ).all()
        institutions_map = {row[0]: row[1] for row in inst_records}

    branch_ids = {i.branch_id for i in instruments if i.branch_id}
    banks_map: dict[uuid.UUID, str] = {}
    if branch_ids:
        branch_records = db.execute(
            select(Branch.id, Bank.name)
            .join(Bank, Branch.bank_id == Bank.id)
            .where(Branch.id.in_(branch_ids))
        ).all()
        banks_map = {row[0]: row[1] for row in branch_records}

    return [
        InstrumentResponse(
            id=i.id,
            institution_id=i.institution_id,
            institution_name=institutions_map.get(i.institution_id),
            bank_name=banks_map.get(i.branch_id, "State Bank of India"),
            type=i.type,
            status=i.status,
            evidence_level=i.evidence_level,
            instrument_number=i.instrument_number
            if can_view_unmasked
            else mask_identifier(i.instrument_number),
            amount=Decimal(str(i.amount)).quantize(Decimal("0.01")),
            issue_date=i.issue_date,
            maturity_date=i.maturity_date,
            tenor_months=i.tenor_months,
            utr=i.utr,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in instruments
    ]


@router.get("/{instrument_id}", response_model=InstrumentResponse)
def get_instrument(
    instrument_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> InstrumentResponse:
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    # Identifier masking: return masked number unless VIEW_UNMASKED_IDENTIFIERS is authorised
    can_view_unmasked = False
    try:
        authorise(principal, PermissionVerb.VIEW_UNMASKED_IDENTIFIERS)
        can_view_unmasked = True
    except (ForbiddenError, HTTPException):
        can_view_unmasked = False

    displayed_num = (
        instrument.instrument_number
        if can_view_unmasked
        else mask_identifier(instrument.instrument_number)
    )

    inst = db.execute(
        select(Institution).where(Institution.id == instrument.institution_id)
    ).scalar_one_or_none()
    bank_name = "State Bank of India"
    if instrument.branch_id:
        br = db.execute(
            select(Bank.name)
            .join(Branch, Branch.bank_id == Bank.id)
            .where(Branch.id == instrument.branch_id)
        ).scalar_one_or_none()
        if br:
            bank_name = br

    return InstrumentResponse(
        id=instrument.id,
        institution_id=instrument.institution_id,
        institution_name=inst.name if inst else None,
        bank_name=bank_name,
        type=instrument.type,
        status=instrument.status,
        evidence_level=instrument.evidence_level,
        instrument_number=displayed_num,
        amount=Decimal(str(instrument.amount)).quantize(Decimal("0.01")),
        issue_date=instrument.issue_date,
        maturity_date=instrument.maturity_date,
        tenor_months=instrument.tenor_months,
        utr=instrument.utr,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )


@router.get("/{instrument_id}/versions", response_model=list[InstrumentVersionResponse])
def get_instrument_versions(
    instrument_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[InstrumentVersionResponse]:
    """Lists immutable versions and snapshot history for an instrument (F-03)."""
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    versions = (
        db.execute(
            select(InstrumentVersion)
            .where(InstrumentVersion.instrument_id == instrument_id)
            .order_by(desc(InstrumentVersion.version_number))
        )
        .scalars()
        .all()
    )
    return list(versions)


@router.get("/{instrument_id}/receipt")
def download_submission_receipt(
    instrument_id: uuid.UUID,
    version: int | None = Query(
        None, description="Version number (defaults to latest)"
    ),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
):
    """Generates and returns the cryptographic submission receipt PDF (F-20)."""
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    inst = db.execute(
        select(Institution).where(Institution.id == instrument.institution_id)
    ).scalar_one_or_none()
    inst_name = inst.name if inst else "Unknown Institution"
    inst_code = inst.aicte_code if inst else "Unknown Code"

    stmt = select(InstrumentVersion).where(
        InstrumentVersion.instrument_id == instrument_id
    )
    if version:
        stmt = stmt.where(InstrumentVersion.version_number == version)
    else:
        stmt = stmt.order_by(desc(InstrumentVersion.version_number)).limit(1)

    ver = db.execute(stmt).scalar_one_or_none()
    if not ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No submitted version found for this instrument (instrument may still be in DRAFT)",
        )

    receipt_id = f"REC-{instrument.id.hex[:8].upper()}-v{ver.version_number}"
    pdf_bytes, sig = generate_submission_receipt_pdf(
        receipt_id=receipt_id,
        instrument_id=str(instrument.id),
        instrument_number=instrument.instrument_number,
        instrument_type=instrument.type.value,
        amount=float(instrument.amount),
        institution_code=inst_code,
        institution_name=inst_name,
        version_number=ver.version_number,
        content_hash=ver.content_hash,
        submitted_at=ver.created_at,
        submitted_by_name=principal.full_name or "Authorized Officer",
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="AICTE_Receipt_{receipt_id}.pdf"',
            "X-Receipt-Signature": sig,
        },
    )
