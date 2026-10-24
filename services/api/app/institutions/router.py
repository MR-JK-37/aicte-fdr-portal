"""Institution Registry & Onboarding Router (F-02 / SPEC §8.2 / F-19)."""

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_current_principal, get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.models.core import AppUser, Institution
from app.models.workflow import InstitutionOnboardingRequest
from app.outbox.producer import enqueue_outbox_event
from app.problem_json import ForbiddenError, NotFoundError

router = APIRouter(prefix="/v1/institutions", tags=["Institutions & Onboarding"])


# --- Schemas ---
class OnboardingApplyRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    institution_id: uuid.UUID
    official_id_ref: str = Field(..., min_length=3, max_length=128)
    authority_letter_doc_id: uuid.UUID | None = None


class OnboardingReviewRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: str = Field(..., pattern="^(APPROVE|REJECT)$")
    reason: str = Field(..., min_length=5, max_length=1024)


class OnboardingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    applicant_user_id: uuid.UUID
    official_id_ref: str
    status: str
    authority_letter_doc_id: uuid.UUID | None = None
    reviewed_by: uuid.UUID | None = None
    rejection_reason: str | None = None
    created_at: datetime
    decided_at: datetime | None = None


class InstitutionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aicte_code: str
    name: str
    created_at: datetime


class InstitutionBatchRow(BaseModel):
    aicte_code: str = Field(..., min_length=3, max_length=32)
    name: str = Field(..., min_length=2, max_length=256)


class BatchImportRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_owner: str = Field(..., min_length=2, max_length=128)
    mapping_version: str = Field(..., min_length=1, max_length=32)
    rows: list[InstitutionBatchRow]


class BatchImportResponse(BaseModel):
    file_hash: str
    mapping_version: str
    source_owner: str
    imported_count: int
    duplicates_skipped: int
    imported_ids: list[uuid.UUID]


# --- Endpoints ---
@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_onboarding(
    payload: OnboardingApplyRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> OnboardingResponse:
    """Institution representative applies for onboarding (F-02)."""
    # Check institution exists
    inst = db.execute(
        select(Institution).where(Institution.id == payload.institution_id)
    ).scalar_one_or_none()
    if not inst:
        raise NotFoundError("Institution", payload.institution_id)

    # Check for duplicate pending request for this user & institution
    existing = db.execute(
        select(InstitutionOnboardingRequest).where(
            InstitutionOnboardingRequest.institution_id == payload.institution_id,
            InstitutionOnboardingRequest.applicant_user_id == principal.id,
            InstitutionOnboardingRequest.status == "PENDING",
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending onboarding request already exists for this institution and applicant.",
        )

    req = InstitutionOnboardingRequest(
        id=uuid.uuid4(),
        institution_id=payload.institution_id,
        applicant_user_id=principal.id,
        authority_letter_doc_id=payload.authority_letter_doc_id,
        official_id_ref=payload.official_id_ref,
        status="PENDING",
    )
    db.add(req)
    db.flush()

    append_audit_entry(
        db,
        action="institution.onboarding_requested",
        entity_type="institution_onboarding_request",
        entity_id=str(req.id),
        after={
            "institution_id": str(payload.institution_id),
            "official_id_ref": payload.official_id_ref,
            "status": "PENDING",
        },
        actor_id=str(principal.id),
        institution_id=str(payload.institution_id),
    )

    enqueue_outbox_event(
        db,
        aggregate_type="institution_onboarding_request",
        aggregate_id=req.id,
        event_type="institution_onboarding.requested",
        payload={
            "institution_id": str(payload.institution_id),
            "applicant_id": str(principal.id),
            "official_id_ref": payload.official_id_ref,
        },
        dedupe_key=f"onboarding.requested:{req.id}",
    )

    res = OnboardingResponse.model_validate(req)
    db.commit()
    return res


@router.get("/onboarding", response_model=list[OnboardingResponse])
def list_onboarding_requests(
    status_filter: str | None = Query(None, alias="status"),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[OnboardingResponse]:
    """Lists onboarding requests (filtered by status and scoped by RLS)."""
    stmt = select(InstitutionOnboardingRequest)
    if status_filter:
        stmt = stmt.where(InstitutionOnboardingRequest.status == status_filter.upper())
    stmt = stmt.order_by(InstitutionOnboardingRequest.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.post("/onboarding/{request_id}/review", response_model=OnboardingResponse)
def review_onboarding_request(
    request_id: uuid.UUID,
    payload: OnboardingReviewRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.MANAGE_INSTITUTION_USERS)
    ),
    db: Session = Depends(get_db),
) -> OnboardingResponse:
    """Intake / Registry Officer reviews representative onboarding application (F-02).
    Enforces separation-of-duties: applicant cannot approve their own application.
    """
    req = db.execute(
        select(InstitutionOnboardingRequest).where(
            InstitutionOnboardingRequest.id == request_id
        )
    ).scalar_one_or_none()
    if not req:
        raise NotFoundError("InstitutionOnboardingRequest", request_id)

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review request in '{req.status}' state",
        )

    # Separation of duties (CLAUDE.md non-negotiable #5 & MASTER_PROMPT §8.3)
    if req.applicant_user_id == principal.id:
        raise ForbiddenError(
            "Separation of duties: applicant cannot review or approve own onboarding application"
        )

    now = datetime.now(UTC)
    req.reviewed_by = principal.id
    req.decided_at = now

    if payload.decision == "APPROVE":
        req.status = "APPROVED"
        # Activate applicant user account
        applicant = db.execute(
            select(AppUser).where(AppUser.id == req.applicant_user_id)
        ).scalar_one_or_none()
        if applicant:
            applicant.is_active = True
            applicant.institution_id = req.institution_id
    else:
        req.status = "REJECTED"
        req.rejection_reason = payload.reason

    db.flush()

    append_audit_entry(
        db,
        action=f"institution.onboarding_{payload.decision.lower()}d",
        entity_type="institution_onboarding_request",
        entity_id=str(req.id),
        before={"status": "PENDING"},
        after={
            "status": req.status,
            "decision": payload.decision,
            "reason": payload.reason,
            "reviewed_by": str(principal.id),
        },
        actor_id=str(principal.id),
        institution_id=str(req.institution_id),
    )

    enqueue_outbox_event(
        db,
        aggregate_type="institution_onboarding_request",
        aggregate_id=req.id,
        event_type=f"institution_onboarding.{payload.decision.lower()}d",
        payload={
            "institution_id": str(req.institution_id),
            "applicant_id": str(req.applicant_user_id),
            "status": req.status,
            "decision": payload.decision,
            "reason": payload.reason,
        },
        dedupe_key=f"onboarding.decision:{req.id}:{payload.decision}",
    )

    res = OnboardingResponse.model_validate(req)
    db.commit()
    return res


@router.post("/batch-import", response_model=BatchImportResponse)
def batch_import_institutions(
    payload: BatchImportRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.ADMINISTER_PLATFORM)
    ),
    db: Session = Depends(get_db),
) -> BatchImportResponse:
    """Authorised CSV/XLSX batch import with provenance (F-02).
    Tracks file hash, importer, source owner, mapping version. Rejects duplicate AICTE codes.
    """
    raw_content = f"{payload.source_owner}:{payload.mapping_version}:" + ",".join(
        f"{r.aicte_code}={r.name}" for r in payload.rows
    )
    file_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

    imported_ids: list[uuid.UUID] = []
    duplicates = 0

    for row in payload.rows:
        existing = db.execute(
            select(Institution).where(Institution.aicte_code == row.aicte_code)
        ).scalar_one_or_none()
        if existing:
            duplicates += 1
            continue

        inst = Institution(
            id=uuid.uuid4(),
            aicte_code=row.aicte_code,
            name=row.name,
        )
        db.add(inst)
        imported_ids.append(inst.id)

    db.flush()

    append_audit_entry(
        db,
        action="institution.batch_import",
        entity_type="institution_batch",
        entity_id=file_hash[:32],
        after={
            "file_hash": file_hash,
            "source_owner": payload.source_owner,
            "mapping_version": payload.mapping_version,
            "imported_count": len(imported_ids),
            "duplicates_skipped": duplicates,
        },
        actor_id=str(principal.id),
    )

    db.commit()

    return BatchImportResponse(
        file_hash=file_hash,
        mapping_version=payload.mapping_version,
        source_owner=payload.source_owner,
        imported_count=len(imported_ids),
        duplicates_skipped=duplicates,
        imported_ids=imported_ids,
    )


@router.get("", response_model=list[InstitutionItem])
def list_institutions(
    search: str | None = None,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[InstitutionItem]:
    stmt = select(Institution)
    if search:
        stmt = stmt.where(
            Institution.name.ilike(f"%{search}%")
            | Institution.aicte_code.ilike(f"%{search}%")
        )
    stmt = stmt.order_by(Institution.name)
    return list(db.execute(stmt).scalars().all())


@router.get("/{institution_id}", response_model=InstitutionItem)
def get_institution(
    institution_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> InstitutionItem:
    inst = db.execute(
        select(Institution).where(Institution.id == institution_id)
    ).scalar_one_or_none()
    if not inst:
        raise NotFoundError("Institution", institution_id)
    return inst
