"""Statement Import & Deterministic Reconciliation Router (F-07 / SPEC §18.1 Scenario 5).

Key invariants:
1. Idempotent import: Identical file SHA-256 returns existing batch without duplicating rows.
2. Malformed row quarantine: Unparseable amounts or dates are quarantined with reasons, allowing valid rows to proceed.
3. Exact UTR + Amount reconciliation: Promotes ONLINE_SD instruments to L3_LEDGER_RECONCILED.
4. FDR scans can NEVER produce L3_LEDGER_RECONCILED.
5. Ambiguous matches (multiple candidates, amount divergence) route to ReconciliationException and NEVER auto-confirm.
"""

import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.models.core import Instrument, VerificationRecord
from app.models.enums import (
    BUREAU_SIDE_ROLES,
    AppRole,
    EvidenceLevel,
    InstrumentType,
)
from app.models.workflow import (
    ReconciliationException,
    StatementBatch,
    StatementLine,
)
from app.problem_json import ForbiddenError, NotFoundError
from app.statements.parser import parse_statement

router = APIRouter(prefix="/v1/statements", tags=["Statement Reconciliation"])

AMOUNT_TOLERANCE = Decimal("0.01")


# --- Schemas ---
class StatementBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_filename: str
    format: str
    checksum: str
    account_number_masked: str
    total_lines: int
    matched_lines: int
    unmatched_lines: int
    quarantined_lines: int
    imported_by: uuid.UUID
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    quarantined_rows: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("metadata", mode="before")
    @classmethod
    def check_metadata(cls, v: Any) -> dict[str, Any]:
        if not isinstance(v, dict):
            return {}
        return v

    @computed_field
    @property
    def filename(self) -> str:
        return self.source_filename

    @computed_field
    @property
    def file_format(self) -> str:
        return self.format

    @computed_field
    @property
    def line_count(self) -> int:
        return self.total_lines

    @computed_field
    @property
    def matched_count(self) -> int:
        return self.matched_lines

    exception_count: int = 0

    @computed_field
    @property
    def quarantined_count(self) -> int:
        return self.quarantined_lines

    @computed_field
    @property
    def status(self) -> str:
        return "PROCESSED"


class StatementLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID
    line_number: int
    line_date: Any | None = None
    amount: float
    utr: str | None = None
    narration: str
    matched_instrument_id: uuid.UUID | None = None
    status: str
    reconciliation_rule_version: str | None = None
    quarantine_reason: str | None = None
    created_at: datetime


class ReconciliationExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    statement_line_id: uuid.UUID | None = None
    instrument_id: uuid.UUID | None = None
    exception_type: str
    details: dict[str, Any]
    status: str
    resolved_by: uuid.UUID | None = None
    resolution_notes: str | None = None
    created_at: datetime


class ResolveExceptionRequest(BaseModel):
    resolution_notes: str
    matched_instrument_id: uuid.UUID | None = None


# --- Endpoints ---
@router.post(
    "/import",
    response_model=StatementBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_bank_statement(
    file: UploadFile = File(...),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> StatementBatchResponse:
    """Imports bank statement (MT940, CAMT.053, CSV).
    Enforces idempotency via SHA-256 checksum, quarantines malformed rows,
    and runs deterministic reconciliation on ONLINE_SD deposits (F-07 / SPEC §18.1 Scenario 5).
    """
    if principal.role not in BUREAU_SIDE_ROLES and principal.role != AppRole.ORG_ADMIN:
        raise ForbiddenError("Only bureau finance officers may import bank statements")

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty statement file"
        )

    checksum = hashlib.sha256(file_bytes).hexdigest()

    # 1. Idempotency Check: Return existing batch without duplication
    existing_batch = db.execute(
        select(StatementBatch).where(StatementBatch.checksum == checksum)
    ).scalar_one_or_none()
    if existing_batch:
        exc_count = (
            db.execute(
                select(func.count(ReconciliationException.id))
                .join(
                    StatementLine,
                    StatementLine.id == ReconciliationException.statement_line_id,
                )
                .where(StatementLine.batch_id == existing_batch.id)
            ).scalar()
            or 0
        )
        res = StatementBatchResponse.model_validate(existing_batch)
        res.exception_count = exc_count
        res.metadata = {"quarantined_rows": existing_batch.quarantined_summary or []}
        res.quarantined_rows = res.metadata["quarantined_rows"]
        return res

    # 2. Parse statement lines and quarantine malformed entries
    parse_result = parse_statement(file_bytes, file.filename or "statement.csv")

    batch_id = uuid.uuid4()
    quarantined_summary = [
        {
            "line": q.line_number,
            "reason": q.reason,
            "raw": q.raw_content[:200],
        }
        for q in parse_result.quarantined
    ]

    batch = StatementBatch(
        id=batch_id,
        source_filename=file.filename or "statement.csv",
        format=parse_result.file_format,
        checksum=checksum,
        account_number_masked="XX-AICTE-COLLECTION",
        total_lines=len(parse_result.lines),
        matched_lines=0,
        unmatched_lines=len(parse_result.lines),
        quarantined_lines=len(parse_result.quarantined),
        quarantined_summary=quarantined_summary,
        imported_by=principal.id,
    )
    db.add(batch)
    db.flush()

    # 3. Deterministic reconciliation against ONLINE_SD instruments
    # Only instruments of type ONLINE_SD can be reconciled by statement import (FDR scans CANNOT)
    online_sd_candidates = list(
        db.execute(
            select(Instrument).where(Instrument.type == InstrumentType.ONLINE_SD)
        )
        .scalars()
        .all()
    )

    matched_count = 0
    exception_count = 0

    for parsed_line in parse_result.lines:
        line_id = uuid.uuid4()

        st_line = StatementLine(
            id=line_id,
            batch_id=batch.id,
            line_number=parsed_line.line_number,
            line_date=parsed_line.booking_date,
            amount=parsed_line.amount,
            utr=parsed_line.utr or None,
            narration=parsed_line.narration or "Deposit",
            status="UNMATCHED",
        )
        db.add(st_line)
        db.flush()

        if parsed_line.utr:
            # Match by exact UTR
            matching_insts = [
                inst
                for inst in online_sd_candidates
                if inst.utr
                and inst.utr.strip().upper() == parsed_line.utr.strip().upper()
            ]

            if len(matching_insts) == 1:
                inst = matching_insts[0]
                if (
                    abs(Decimal(str(inst.amount)) - parsed_line.amount)
                    <= AMOUNT_TOLERANCE
                ):
                    # EXACT MATCH -> Promote to L3_LEDGER_RECONCILED
                    st_line.status = "MATCHED"
                    st_line.matched_instrument_id = inst.id
                    st_line.reconciliation_rule_version = "v1-exact-utr-amount"

                    before_level = inst.evidence_level
                    inst.evidence_level = EvidenceLevel.L3_LEDGER_RECONCILED
                    matched_count += 1

                    # Record verification evidence
                    v_record = VerificationRecord(
                        id=uuid.uuid4(),
                        institution_id=inst.institution_id,
                        instrument_id=inst.id,
                        level=EvidenceLevel.L3_LEDGER_RECONCILED,
                        source="statement_import",
                        confirmed_amount=float(parsed_line.amount),
                        raw_payload={
                            "batch_id": str(batch.id),
                            "utr": parsed_line.utr,
                            "line_number": parsed_line.line_number,
                            "reconciliation_type": "EXACT_UTR_AMOUNT",
                        },
                    )
                    db.add(v_record)

                    append_audit_entry(
                        db,
                        action="instrument.evidence_level_confirmed",
                        entity_type="instrument",
                        entity_id=str(inst.id),
                        before={"evidence_level": before_level.value},
                        after={
                            "evidence_level": EvidenceLevel.L3_LEDGER_RECONCILED.value,
                            "source": "statement_import",
                            "utr": parsed_line.utr,
                            "amount": str(parsed_line.amount),
                        },
                        actor_id=str(principal.id),
                        institution_id=str(inst.institution_id),
                    )
                else:
                    # UTR matches but amount differs -> Ambiguous exception (NEVER auto-confirm!)
                    st_line.status = "AMBIGUOUS"
                    st_line.reconciliation_rule_version = "v1-amount-mismatch"
                    exception_count += 1

                    exc = ReconciliationException(
                        id=uuid.uuid4(),
                        statement_line_id=st_line.id,
                        instrument_id=inst.id,
                        exception_type="AMOUNT_MISMATCH",
                        details={
                            "declared_amount": str(inst.amount),
                            "statement_amount": str(parsed_line.amount),
                            "utr": parsed_line.utr,
                            "line_number": parsed_line.line_number,
                        },
                        status="OPEN",
                    )
                    db.add(exc)
            elif len(matching_insts) > 1:
                # Multiple instruments match same UTR -> Ambiguous exception (NEVER auto-confirm!)
                st_line.status = "AMBIGUOUS"
                st_line.reconciliation_rule_version = "v1-multiple-candidates"
                exception_count += 1

                exc = ReconciliationException(
                    id=uuid.uuid4(),
                    statement_line_id=st_line.id,
                    exception_type="MULTIPLE_MATCHES",
                    details={
                        "utr": parsed_line.utr,
                        "matched_instrument_ids": [str(m.id) for m in matching_insts],
                        "line_number": parsed_line.line_number,
                    },
                    status="OPEN",
                )
                db.add(exc)

    batch.matched_lines = matched_count
    batch.unmatched_lines = len(parse_result.lines) - matched_count

    append_audit_entry(
        db,
        action="statement.batch_imported",
        entity_type="statement_batch",
        entity_id=str(batch.id),
        after={
            "source_filename": batch.source_filename,
            "total_lines": batch.total_lines,
            "matched_lines": batch.matched_lines,
            "unmatched_lines": batch.unmatched_lines,
            "quarantined_lines": batch.quarantined_lines,
            "checksum": checksum,
        },
        actor_id=str(principal.id),
    )

    res = StatementBatchResponse.model_validate(batch)
    res.exception_count = exception_count
    res.metadata = {"quarantined_rows": quarantined_summary}
    res.quarantined_rows = quarantined_summary
    db.commit()
    return res


@router.get("/batches", response_model=list[StatementBatchResponse])
def list_statement_batches(
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[StatementBatchResponse]:
    """Lists imported statement batches."""
    stmt = select(StatementBatch).order_by(StatementBatch.created_at.desc())
    batches = list(db.execute(stmt).scalars().all())
    return [StatementBatchResponse.model_validate(b) for b in batches]


@router.get("/batches/{batch_id}", response_model=StatementBatchResponse)
def get_statement_batch(
    batch_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> StatementBatchResponse:
    """Gets statement batch details including quarantined rows report."""
    batch = db.execute(
        select(StatementBatch).where(StatementBatch.id == batch_id)
    ).scalar_one_or_none()
    if not batch:
        raise NotFoundError("StatementBatch", batch_id)
    exc_count = (
        db.execute(
            select(func.count(ReconciliationException.id))
            .join(
                StatementLine,
                StatementLine.id == ReconciliationException.statement_line_id,
            )
            .where(StatementLine.batch_id == batch.id)
        ).scalar()
        or 0
    )
    res = StatementBatchResponse.model_validate(batch)
    res.exception_count = exc_count
    res.metadata = {"quarantined_rows": batch.quarantined_summary or []}
    res.quarantined_rows = res.metadata["quarantined_rows"]
    return res


@router.get(
    "/batches/{batch_id}/lines",
    response_model=list[StatementLineResponse],
)
def list_batch_lines(
    batch_id: uuid.UUID,
    status_filter: str | None = Query(None, alias="status"),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[StatementLineResponse]:
    """Lists individual parsed lines for a statement batch."""
    stmt = select(StatementLine).where(StatementLine.batch_id == batch_id)
    if status_filter:
        stmt = stmt.where(StatementLine.status == status_filter)
    stmt = stmt.order_by(StatementLine.line_number.asc())
    lines = list(db.execute(stmt).scalars().all())
    return [StatementLineResponse.model_validate(l) for l in lines]


@router.get(
    "/exceptions",
    response_model=list[ReconciliationExceptionResponse],
)
def list_reconciliation_exceptions(
    status_filter: str | None = Query(None, alias="status"),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[ReconciliationExceptionResponse]:
    """Lists reconciliation exceptions."""
    stmt = select(ReconciliationException)
    if status_filter:
        stmt = stmt.where(ReconciliationException.status == status_filter)
    stmt = stmt.order_by(ReconciliationException.created_at.desc())
    rows = list(db.execute(stmt).scalars().all())
    return [ReconciliationExceptionResponse.model_validate(r) for r in rows]


@router.post(
    "/exceptions/{exception_id}/resolve",
    response_model=ReconciliationExceptionResponse,
)
def resolve_reconciliation_exception(
    exception_id: uuid.UUID,
    payload: ResolveExceptionRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.RESOLVE_EXCEPTION)
    ),
    db: Session = Depends(get_db),
) -> ReconciliationExceptionResponse:
    """Finance officer resolves a reconciliation exception with notes (F-07)."""
    exc = db.execute(
        select(ReconciliationException).where(
            ReconciliationException.id == exception_id
        )
    ).scalar_one_or_none()
    if not exc:
        raise NotFoundError("ReconciliationException", exception_id)

    exc.status = "RESOLVED"
    exc.resolved_by = principal.id
    exc.resolution_notes = payload.resolution_notes

    if payload.matched_instrument_id:
        exc.instrument_id = payload.matched_instrument_id

    append_audit_entry(
        db,
        action="verification.reconciliation_exception_resolved",
        entity_type="reconciliation_exception",
        entity_id=str(exc.id),
        after={
            "status": "RESOLVED",
            "resolution_notes": payload.resolution_notes,
            "matched_instrument_id": str(payload.matched_instrument_id)
            if payload.matched_instrument_id
            else None,
        },
        actor_id=str(principal.id),
    )

    res = ReconciliationExceptionResponse.model_validate(exc)
    db.commit()
    return res
