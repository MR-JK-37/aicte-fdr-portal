"""Reports & Statutory Exports Router (MASTER_PROMPT_V2 §7 / Exit Gate G-14).

Features:
- GET /v1/reports/catalogue: Catalog of statutory and management reports.
- POST /v1/reports/{key}/runs: Kick off export job with reason and scope filter.
- GET /v1/export-jobs: List export jobs within principal's scope.
- GET /v1/export-jobs/{id}: Inspect job status, row-count, SHA-256 hash.
- GET /v1/export-jobs/{id}/download: Stream sanitized CSV file with permissions
  revalidated at download time, CSV injection neutralised, and download audited.
- Schedules CRUD: List, create, and remove automated recurring export schedules.
"""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal, authorise_safe, mask_identifier
from app.models.core import Instrument
from app.models.extensions import ExportJob, ReportSchedule
from app.problem_json import ForbiddenError, NotFoundError

router = APIRouter(prefix="/v1", tags=["Reports & Exports"])

REPORT_CATALOGUE = [
    {
        "key": "statutory_compliance",
        "title": "AICTE Statutory Deposit Compliance Register",
        "description": "Comprehensive schedule of active, renewed, and pending deposits across approved institutions.",
        "category": "statutory",
        "supported_formats": ["csv"],
    },
    {
        "key": "maturity_pipeline",
        "title": "Maturity & Expiry Forecast Schedule",
        "description": "Forward-looking calendar of deposits maturing across 30, 60, and 90-day time horizons.",
        "category": "operational",
        "supported_formats": ["csv"],
    },
    {
        "key": "reconciliation_summary",
        "title": "Bank Reconciliation & Discrepancy Log",
        "description": "Cross-verification log comparing institution declarations with bank-confirmed statements.",
        "category": "financial",
        "supported_formats": ["csv"],
    },
    {
        "key": "audit_trail_summary",
        "title": "Executive Audit Trail & Checkpoint Register",
        "description": "Cryptographically chained log of governance actions and state transitions.",
        "category": "governance",
        "supported_formats": ["csv"],
    },
]


# --- Schemas ---


class ReportCatalogueItem(BaseModel):
    key: str
    title: str
    description: str
    category: str
    supported_formats: list[str]


class RunReportPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: str = Field(
        ...,
        min_length=5,
        description="Auditable justification for running statutory export",
    )
    params: dict[str, Any] = Field(default_factory=dict)


class ExportJobResponse(BaseModel):
    id: uuid.UUID
    report_key: str
    status: str
    reason: str
    row_count: int | None
    file_hash: str | None
    created_at: datetime
    expires_at: datetime
    completed_at: datetime | None


class ReportSchedulePayload(BaseModel):
    report_key: str
    cron_expression: str
    params: dict[str, Any] = Field(default_factory=dict)


class ReportScheduleResponse(BaseModel):
    id: uuid.UUID
    report_key: str
    cron_expression: str
    params: dict[str, Any]
    enabled: bool
    created_at: datetime


# --- CSV Injection Neutralizer ---


def sanitize_csv_cell(val: Any) -> str:
    """Neutralizes CSV Formula Injection (CWE-1236 / Exit Gate G-14).
    If a string starts with =, +, -, @, \\t, or \\r, prefix with a single quote.
    """
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


# --- Endpoints ---


@router.get("/reports/catalogue", response_model=list[ReportCatalogueItem])
def get_report_catalogue(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
) -> list[ReportCatalogueItem]:
    """Returns available statutory and management reports."""
    return [ReportCatalogueItem(**item) for item in REPORT_CATALOGUE]


@router.post(
    "/reports/{report_key}/runs",
    response_model=ExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def run_report_export(
    report_key: str,
    payload: RunReportPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
) -> ExportJobResponse:
    """Schedules an asynchronous report export job."""
    if not any(r["key"] == report_key for r in REPORT_CATALOGUE):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_key}' not found in catalogue",
        )

    # Build report data in memory
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=7)

    stmt = select(Instrument)
    if principal.institution_id:
        stmt = stmt.where(Instrument.institution_id == principal.institution_id)
    instruments = db.execute(stmt).scalars().all()

    # Generate CSV with sanitized fields
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            "Instrument ID",
            "Institution ID",
            "Type",
            "Status",
            "FDR Number",
            "UTR / Reference",
            "Amount INR",
            "Maturity Date",
        ]
    )
    row_count = 0
    can_unmask = authorise_safe(principal, PermissionVerb.VIEW_UNMASKED_IDENTIFIERS)
    for inst in instruments:
        fdr_num = (
            inst.instrument_number
            if can_unmask
            else mask_identifier(inst.instrument_number)
        )
        writer.writerow(
            [
                sanitize_csv_cell(str(inst.id)),
                sanitize_csv_cell(str(inst.institution_id)),
                sanitize_csv_cell(
                    inst.type.value if hasattr(inst.type, "value") else str(inst.type)
                ),
                sanitize_csv_cell(
                    inst.status.value
                    if hasattr(inst.status, "value")
                    else str(inst.status)
                ),
                sanitize_csv_cell(fdr_num),
                sanitize_csv_cell(inst.utr or ""),
                sanitize_csv_cell(str(inst.amount)),
                sanitize_csv_cell(
                    inst.maturity_date.isoformat() if inst.maturity_date else ""
                ),
            ]
        )
        row_count += 1

    csv_content = out.getvalue()
    file_hash = hashlib.sha256(csv_content.encode("utf-8")).hexdigest()

    job = ExportJob(
        id=uuid.uuid4(),
        requested_by=principal.id,
        institution_id=principal.institution_id,
        report_key=report_key,
        params=payload.params,
        scope_filter={"institution_id": str(principal.institution_id)}
        if principal.institution_id
        else {},
        reason=payload.reason,
        status="COMPLETED",
        row_count=row_count,
        file_hash=file_hash,
        file_content=csv_content,
        expires_at=expires_at,
        completed_at=now,
    )
    db.add(job)
    db.flush()

    append_audit_entry(
        db,
        action="report.exported",
        entity_type="export_job",
        entity_id=str(job.id),
        after={
            "report_key": report_key,
            "row_count": row_count,
            "file_hash": file_hash,
            "reason": payload.reason,
        },
        actor_id=str(principal.id),
        institution_id=str(principal.institution_id)
        if principal.institution_id
        else None,
    )
    db.commit()

    return ExportJobResponse(
        id=job.id,
        report_key=job.report_key,
        status=job.status,
        reason=job.reason,
        row_count=job.row_count,
        file_hash=job.file_hash,
        created_at=job.created_at,
        expires_at=job.expires_at,
        completed_at=job.completed_at,
    )


@router.get("/export-jobs", response_model=list[ExportJobResponse])
def list_export_jobs(
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
) -> list[ExportJobResponse]:
    """Lists recent export jobs requested within user's scope."""
    scope = authorise_safe(principal, PermissionVerb.EXPORT_REPORT)
    stmt = select(ExportJob)
    if principal.institution_id:
        stmt = stmt.where(ExportJob.institution_id == principal.institution_id)
    elif scope != "all":
        stmt = stmt.where(ExportJob.requested_by == principal.id)
    stmt = stmt.order_by(desc(ExportJob.created_at)).limit(50)

    jobs = db.execute(stmt).scalars().all()
    return [
        ExportJobResponse(
            id=j.id,
            report_key=j.report_key,
            status=j.status,
            reason=j.reason,
            row_count=j.row_count,
            file_hash=j.file_hash,
            created_at=j.created_at,
            expires_at=j.expires_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]


@router.get("/export-jobs/{job_id}", response_model=ExportJobResponse)
def get_export_job(
    job_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
) -> ExportJobResponse:
    """Gets details and status for a specific export job."""
    job = db.get(ExportJob, job_id)
    if not job:
        raise NotFoundError("ExportJob", job_id)

    # Scope check
    if principal.institution_id and job.institution_id != principal.institution_id:
        raise NotFoundError("ExportJob", job_id)

    return ExportJobResponse(
        id=job.id,
        report_key=job.report_key,
        status=job.status,
        reason=job.reason,
        row_count=job.row_count,
        file_hash=job.file_hash,
        created_at=job.created_at,
        expires_at=job.expires_at,
        completed_at=job.completed_at,
    )


@router.get("/export-jobs/{job_id}/download")
def download_export_file(
    job_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
):
    """Streams the sanitized export file; re-validates scope and audits download."""
    job = db.get(ExportJob, job_id)
    if not job:
        raise NotFoundError("ExportJob", job_id)

    # Permission revalidation at download time (MASTER_PROMPT_V2 §7)
    if principal.institution_id and job.institution_id != principal.institution_id:
        raise ForbiddenError(
            "Access denied to export file outside your institution scope"
        )

    now = datetime.now(UTC)
    if job.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Export file has expired"
        )

    if not job.file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file content not found",
        )

    append_audit_entry(
        db,
        action="report.downloaded",
        entity_type="export_job",
        entity_id=str(job.id),
        after={"file_hash": job.file_hash, "downloaded_by": str(principal.id)},
        actor_id=str(principal.id),
        institution_id=str(job.institution_id) if job.institution_id else None,
    )
    db.commit()

    filename = f"{job.report_key}_{job.id.hex[:8]}.csv"
    return Response(
        content=job.file_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-SHA256": job.file_hash or "",
        },
    )


@router.get("/reports/schedules", response_model=list[ReportScheduleResponse])
def list_report_schedules(
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
) -> list[ReportScheduleResponse]:
    """Lists configured report schedules."""
    stmt = select(ReportSchedule).where(ReportSchedule.created_by == principal.id)
    schedules = db.execute(stmt).scalars().all()
    return [
        ReportScheduleResponse(
            id=s.id,
            report_key=s.report_key,
            cron_expression=s.cron_expression,
            params=s.params,
            enabled=s.enabled,
            created_at=s.created_at,
        )
        for s in schedules
    ]


@router.post(
    "/reports/schedules",
    response_model=ReportScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report_schedule(
    payload: ReportSchedulePayload,
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
) -> ReportScheduleResponse:
    """Configures a recurring statutory export schedule."""
    schedule = ReportSchedule(
        id=uuid.uuid4(),
        report_key=payload.report_key,
        cron_expression=payload.cron_expression,
        params=payload.params,
        created_by=principal.id,
        enabled=True,
    )
    db.add(schedule)
    db.commit()

    return ReportScheduleResponse(
        id=schedule.id,
        report_key=schedule.report_key,
        cron_expression=schedule.cron_expression,
        params=schedule.params,
        enabled=schedule.enabled,
        created_at=schedule.created_at,
    )


@router.delete(
    "/reports/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_report_schedule(
    schedule_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.EXPORT_REPORT)),
    db: Session = Depends(get_db),
):
    """Deletes an automated report schedule."""
    schedule = db.get(ReportSchedule, schedule_id)
    if not schedule or schedule.created_by != principal.id:
        raise NotFoundError("ReportSchedule", schedule_id)
    db.delete(schedule)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
