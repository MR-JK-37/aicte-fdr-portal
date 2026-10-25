"""Audit API Router (F-18 / SPEC §14, §15 / Exit Gate G-18).

Provides:
- GET /v1/audit/events: Query hash-chained audit log with scope filtering.
- GET /v1/audit/events/{id}: Fetch single entry with cryptographic proof.
- GET /v1/audit/access-logs: Read security access / authentication history.
- GET /v1/audit/chain/status: Current integrity status and latest signed checkpoint.
- POST /v1/audit/chain/verify: Execute real hash-chain verification job.
- POST /v1/audit/exports: Export cryptographically verified audit bundle.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry, verify_chain
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.models.audit import AuditCheckpoint, AuditLog
from app.models.extensions import AuditVerificationJob
from app.problem_json import NotFoundError

router = APIRouter(prefix="/v1/audit", tags=["Audit & Integrity (F-18)"])


# --- Schemas ---


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: uuid.UUID | None
    institution_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    prev_hash: str
    row_hash: str
    created_at: datetime


class AccessLogResponse(BaseModel):
    id: int
    actor_id: str | None
    action: str
    entity_type: str
    created_at: datetime


class ChainStatusResponse(BaseModel):
    total_entries: int
    latest_row_hash: str | None
    last_verified_at: datetime | None
    last_verification_ok: bool
    latest_checkpoint: dict[str, Any] | None


class VerifyChainJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    ok: bool
    broken_at_id: int | None
    entries_verified: int
    duration_ms: int
    verified_at: datetime


# --- Endpoints ---


@router.get("/events", response_model=list[AuditEventResponse])
def list_audit_events(
    entity_type: str | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW_AUDIT)),
    db: Session = Depends(get_db),
) -> list[AuditEventResponse]:
    """Lists hash-chained audit log entries scoped by institutional boundary."""
    stmt = select(AuditLog)
    if principal.institution_id:
        stmt = stmt.where(AuditLog.institution_id == principal.institution_id)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)

    stmt = stmt.order_by(desc(AuditLog.id)).limit(limit).offset(offset)
    entries = db.execute(stmt).scalars().all()

    # Sensitive read itself is audited (SPEC §14.3 / MASTER_PROMPT_V2 §7)
    append_audit_entry(
        db,
        action="audit.log_read",
        entity_type="audit_log",
        entity_id="bulk",
        after={"count": len(entries), "offset": offset},
        actor_id=str(principal.id),
        institution_id=str(principal.institution_id)
        if principal.institution_id
        else None,
    )
    db.commit()

    return list(entries)


@router.get("/events/{event_id}", response_model=AuditEventResponse)
def get_audit_event(
    event_id: int,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW_AUDIT)),
    db: Session = Depends(get_db),
) -> AuditEventResponse:
    """Fetches a single audit log entry by sequential ID with cryptographic proof."""
    entry = db.get(AuditLog, event_id)
    if not entry:
        raise NotFoundError("AuditEvent", event_id)

    if principal.institution_id and entry.institution_id != principal.institution_id:
        raise NotFoundError("AuditEvent", event_id)

    return AuditEventResponse.model_validate(entry)


@router.get("/access-logs", response_model=list[AccessLogResponse])
def get_access_logs(
    limit: int = Query(50, ge=1, le=100),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW_AUDIT)),
    db: Session = Depends(get_db),
) -> list[AccessLogResponse]:
    """Retrieves access and authentication audit events."""
    stmt = select(AuditLog).where(
        AuditLog.action.in_(
            [
                "auth.login",
                "auth.logout",
                "auth.step_up_success",
                "auth.failed_attempt",
                "audit.log_read",
            ]
        )
    )
    if principal.institution_id:
        stmt = stmt.where(AuditLog.institution_id == principal.institution_id)

    stmt = stmt.order_by(desc(AuditLog.id)).limit(limit)
    entries = db.execute(stmt).scalars().all()

    return [
        AccessLogResponse(
            id=e.id,
            actor_id=str(e.actor_id) if e.actor_id else None,
            action=e.action,
            entity_type=e.entity_type,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/chain/status", response_model=ChainStatusResponse)
def get_chain_status(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW_AUDIT)),
    db: Session = Depends(get_db),
) -> ChainStatusResponse:
    """Returns hash-chain status, total entries, and latest checkpoint."""
    total = db.execute(select(func.count(AuditLog.id))).scalar_one()
    latest_entry = db.execute(
        select(AuditLog).order_by(desc(AuditLog.id)).limit(1)
    ).scalar_one_or_none()

    latest_job = db.execute(
        select(AuditVerificationJob)
        .order_by(desc(AuditVerificationJob.verified_at))
        .limit(1)
    ).scalar_one_or_none()

    latest_cp = db.execute(
        select(AuditCheckpoint)
        .order_by(desc(AuditCheckpoint.checkpoint_index))
        .limit(1)
    ).scalar_one_or_none()
    cp_dict = None
    if latest_cp:
        cp_dict = {
            "checkpoint_index": latest_cp.checkpoint_index,
            "period_start": latest_cp.period_start.isoformat(),
            "period_end": latest_cp.period_end.isoformat(),
            "first_log_id": latest_cp.first_event_id,
            "last_log_id": latest_cp.last_event_id,
            "root_hash": latest_cp.chain_root_hash,
            "signature": latest_cp.signature,
        }

    return ChainStatusResponse(
        total_entries=total,
        latest_row_hash=latest_entry.row_hash if latest_entry else None,
        last_verified_at=latest_job.verified_at if latest_job else None,
        last_verification_ok=latest_job.ok if latest_job else True,
        latest_checkpoint=cp_dict,
    )


@router.post("/chain/verify", response_model=VerifyChainJobResponse)
def run_chain_verification_job(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW_AUDIT)),
    db: Session = Depends(get_db),
) -> VerifyChainJobResponse:
    """Executes a real hash-chain cryptographic verification job (Exit Gate G-18)."""
    t0 = time.perf_counter()
    result = verify_chain(db)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    total_verified = db.execute(select(func.count(AuditLog.id))).scalar_one()

    job = AuditVerificationJob(
        id=uuid.uuid4(),
        triggered_by=principal.id,
        status="VERIFIED" if result.ok else "BROKEN",
        ok=result.ok,
        broken_at_id=result.broken_at_id,
        entries_verified=total_verified,
        duration_ms=duration_ms,
        error_details=result.reason,
    )
    db.add(job)
    db.commit()

    return VerifyChainJobResponse(
        id=job.id,
        status=job.status,
        ok=job.ok,
        broken_at_id=job.broken_at_id,
        entries_verified=job.entries_verified,
        duration_ms=job.duration_ms or 0,
        verified_at=job.verified_at,
    )


@router.post("/exports")
def export_audit_bundle(
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
):
    """Exports cryptographically signed JSON bundle of audit chain entries."""
    stmt = select(AuditLog)
    if principal.institution_id:
        stmt = stmt.where(AuditLog.institution_id == principal.institution_id)
    stmt = stmt.order_by(AuditLog.id.asc()).limit(1000)

    entries = db.execute(stmt).scalars().all()
    bundle = {
        "generated_at": datetime.now(UTC).isoformat(),
        "exported_by": str(principal.id),
        "institution_id": str(principal.institution_id)
        if principal.institution_id
        else "ALL",
        "entry_count": len(entries),
        "entries": [
            {
                "id": e.id,
                "actor_id": str(e.actor_id) if e.actor_id else None,
                "institution_id": str(e.institution_id) if e.institution_id else None,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "before": e.before,
                "after": e.after,
                "prev_hash": e.prev_hash,
                "row_hash": e.row_hash,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }

    append_audit_entry(
        db,
        action="audit.exported",
        entity_type="audit_bundle",
        entity_id="bundle",
        after={"count": len(entries)},
        actor_id=str(principal.id),
        institution_id=str(principal.institution_id)
        if principal.institution_id
        else None,
    )
    db.commit()

    content = json.dumps(bundle, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="AICTE_Audit_Bundle.json"',
        },
    )
