"""Help, Support & Data Principal Rights Router (F-21 / F-22).

Features:
- GET /v1/help/articles: Regulatory guidelines and user manuals.
- Support Requests CRUD: Ticket lifecycle with correlation ID tracing.
- Data Principal Rights (DPDP Act): Statutory access, rectification, and erasure requests with tracking.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.models.extensions import RightsRequest, SupportRequest

router = APIRouter(prefix="/v1", tags=["Help, Support & Rights (F-21/F-22)"])

HELP_ARTICLES = [
    {
        "id": "art-01",
        "title": "Security Deposit Submission Guidelines for Approved Institutions",
        "category": "compliance",
        "summary": "Mandatory checklist for submitting FDR, Bank Guarantee, and Joint Account instruments under AICTE APH.",
        "content": "Institutions must ensure all FDR instruments are drawn in favour of Member Secretary, AICTE, with a minimum tenor of 10 years or as prescribed.",
    },
    {
        "id": "art-02",
        "title": "Tripartite Bank Confirmation & L2/L3 Evidence Verification",
        "category": "verification",
        "summary": "Explaining evidence levels: L0 Declared, L1 Document Verified, L2 Statement Confirmed, L3 Realtime API.",
        "content": "L2 evidence requires automated SFTP statement confirmation from designated nodal banks. L3 provides direct API verification.",
    },
    {
        "id": "art-03",
        "title": "Release & Refund Procedure: Clearances and Step-Up Authorization",
        "category": "release",
        "summary": "Step-by-step procedure for institutional deposit release upon completion of mandatory tenure.",
        "content": "Release requires clearance from regional officer, scrutiny verification, and approval by Competent Authority with biometric step-up MFA.",
    },
    {
        "id": "art-04",
        "title": "Data Principal Rights under Digital Personal Data Protection Act (DPDP)",
        "category": "privacy",
        "summary": "Information on accessing, correcting, or requesting erasure of personal registration data.",
        "content": "Users can exercise their statutory rights through the Rights Gateway. Processing timeline is bounded by statutory regulations.",
    },
]


# --- Schemas ---


class HelpArticleItem(BaseModel):
    id: str
    title: str
    category: str
    summary: str
    content: str


class CreateSupportRequestPayload(BaseModel):
    category: str = Field(..., description="compliance, technical, or data_issue")
    subject: str = Field(..., min_length=5, max_length=256)
    description: str = Field(..., min_length=10)


class SupportRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    subject: str
    description: str
    status: str
    correlation_id: str | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime


class CreateRightsRequestPayload(BaseModel):
    request_type: str = Field(
        ..., description="ACCESS, RECTIFICATION, ERASURE, or OBJECTION"
    )
    details: str = Field(..., min_length=10)


class RightsRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_type: str
    details: str
    status: str
    due_date: datetime
    decision_reason: str | None
    created_at: datetime


# --- Endpoints ---


@router.get("/help/articles", response_model=list[HelpArticleItem])
def list_help_articles(
    category: str | None = Query(None),
) -> list[HelpArticleItem]:
    """Returns knowledge base guidance articles."""
    if category:
        return [
            HelpArticleItem(**a) for a in HELP_ARTICLES if a["category"] == category
        ]
    return [HelpArticleItem(**a) for a in HELP_ARTICLES]


@router.get("/support-requests", response_model=list[SupportRequestResponse])
def list_support_requests(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[SupportRequestResponse]:
    """Lists support tickets raised by current user."""
    stmt = (
        select(SupportRequest)
        .where(SupportRequest.user_id == principal.id)
        .order_by(desc(SupportRequest.created_at))
    )
    reqs = db.execute(stmt).scalars().all()
    return [SupportRequestResponse.model_validate(r) for r in reqs]


@router.post(
    "/support-requests",
    response_model=SupportRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_support_request(
    payload: CreateSupportRequestPayload,
    x_correlation_id: str | None = Header(None, alias="X-Correlation-ID"),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """Submits a support ticket with auto-attached correlation ID."""
    now = datetime.now(UTC)
    req = SupportRequest(
        id=uuid.uuid4(),
        user_id=principal.id,
        category=payload.category,
        subject=payload.subject,
        description=payload.description,
        status="OPEN",
        correlation_id=x_correlation_id,
        due_date=now + timedelta(days=3),
    )
    db.add(req)
    db.flush()

    append_audit_entry(
        db,
        action="support_request.created",
        entity_type="support_request",
        entity_id=str(req.id),
        after={"subject": req.subject, "category": req.category},
        actor_id=str(principal.id),
    )
    db.commit()

    return SupportRequestResponse.model_validate(req)


@router.get("/rights-requests", response_model=list[RightsRequestResponse])
def list_rights_requests(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[RightsRequestResponse]:
    """Lists DPDP statutory rights requests submitted by current user."""
    stmt = (
        select(RightsRequest)
        .where(RightsRequest.user_id == principal.id)
        .order_by(desc(RightsRequest.created_at))
    )
    reqs = db.execute(stmt).scalars().all()
    return [RightsRequestResponse.model_validate(r) for r in reqs]


@router.post(
    "/rights-requests",
    response_model=RightsRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rights_request(
    payload: CreateRightsRequestPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> RightsRequestResponse:
    """Submits a DPDP statutory data principal request."""
    now = datetime.now(UTC)
    req = RightsRequest(
        id=uuid.uuid4(),
        user_id=principal.id,
        request_type=payload.request_type.upper(),
        details=payload.details,
        status="PENDING_VERIFICATION",
        due_date=now + timedelta(days=30),  # Statutory 30-day resolution window
    )
    db.add(req)
    db.flush()

    append_audit_entry(
        db,
        action="rights_request.created",
        entity_type="rights_request",
        entity_id=str(req.id),
        after={"type": req.request_type},
        actor_id=str(principal.id),
    )
    db.commit()

    return RightsRequestResponse.model_validate(req)
