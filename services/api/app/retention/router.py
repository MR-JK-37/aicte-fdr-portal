"""Data Retention & Legal Holds Router (F-22).

Enforces:
- Statutory retention schedules (default 8 years for financial deposit records per Indian regulations).
- No disposal executed until specifically configured.
- Legal Holds freeze records: held entities are permanently immune to automated disposal.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.models.extensions import LegalHold, RetentionClass

router = APIRouter(prefix="/v1/retention", tags=["Retention & Legal Holds (F-22)"])


# --- Schemas ---


class RetentionClassPayload(BaseModel):
    class_key: str = Field(..., min_length=3, max_length=64)
    retention_years: int = Field(8, ge=1, le=50)
    disposal_action: str = Field("ARCHIVE", description="ARCHIVE or PERMANENT_DELETE")


class RetentionClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_key: str
    retention_years: int
    disposal_action: str
    created_at: datetime


class LegalHoldPayload(BaseModel):
    name: str = Field(..., min_length=3, max_length=256)
    matter_id: str = Field(..., min_length=3, max_length=128)
    entity_type: str = Field(..., description="instrument, institution, or observation")
    entity_id: str = Field(...)
    reason: str = Field(..., min_length=10)


class LegalHoldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    matter_id: str
    entity_type: str
    entity_id: str
    applied_by: uuid.UUID
    reason: str
    active: bool
    created_at: datetime
    lifted_at: datetime | None


# --- Endpoints ---


@router.get("/classes", response_model=list[RetentionClassResponse])
def list_retention_classes(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[RetentionClassResponse]:
    """Lists configured data retention schedules."""
    stmt = select(RetentionClass).order_by(RetentionClass.class_key)
    classes = db.execute(stmt).scalars().all()
    return [RetentionClassResponse.model_validate(c) for c in classes]


@router.post(
    "/classes",
    response_model=RetentionClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_retention_class(
    payload: RetentionClassPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_POLICY)),
    db: Session = Depends(get_db),
) -> RetentionClassResponse:
    """Configures a retention classification schedule."""
    existing = db.execute(
        select(RetentionClass).where(
            RetentionClass.class_key == payload.class_key.upper().strip()
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retention class '{payload.class_key}' already exists",
        )

    rc = RetentionClass(
        id=uuid.uuid4(),
        class_key=payload.class_key.upper().strip(),
        retention_years=payload.retention_years,
        disposal_action=payload.disposal_action.upper().strip(),
    )
    db.add(rc)
    db.flush()

    append_audit_entry(
        db,
        action="retention_class.created",
        entity_type="retention_class",
        entity_id=str(rc.id),
        after={"class_key": rc.class_key, "years": rc.retention_years},
        actor_id=str(principal.id),
    )
    db.commit()

    return RetentionClassResponse.model_validate(rc)


@router.get("/legal-holds", response_model=list[LegalHoldResponse])
def list_legal_holds(
    active_only: bool = Query(True),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[LegalHoldResponse]:
    """Lists legal holds active across the system."""
    stmt = select(LegalHold)
    if active_only:
        stmt = stmt.where(LegalHold.active.is_(True))
    stmt = stmt.order_by(desc(LegalHold.created_at))

    holds = db.execute(stmt).scalars().all()
    return [LegalHoldResponse.model_validate(h) for h in holds]


@router.post(
    "/legal-holds",
    response_model=LegalHoldResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_legal_hold(
    payload: LegalHoldPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_POLICY)),
    db: Session = Depends(get_db),
) -> LegalHoldResponse:
    """Applies a legal hold freezing an entity from disposal or expungement."""
    hold = LegalHold(
        id=uuid.uuid4(),
        name=payload.name,
        matter_id=payload.matter_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        applied_by=principal.id,
        reason=payload.reason,
        active=True,
    )
    db.add(hold)
    db.flush()

    append_audit_entry(
        db,
        action="legal_hold.applied",
        entity_type="legal_hold",
        entity_id=str(hold.id),
        after={
            "entity": f"{hold.entity_type}:{hold.entity_id}",
            "matter": hold.matter_id,
        },
        actor_id=str(principal.id),
    )
    db.commit()

    return LegalHoldResponse.model_validate(hold)
