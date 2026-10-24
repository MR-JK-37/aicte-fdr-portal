"""Verification workflow orchestration.

Hard rule from the brief, enforced here structurally rather than just by
convention: "The evidence level is never raised by AI. Only human actions
with uploaded evidence move L1->L2->L3." So every *_check/request/import
function below only ever creates a VerificationRecord (evidence) — never
touches instrument.evidence_level. Only the confirm_* functions, which
are role-gated and require a human actor, change evidence_level, and each
one writes an audit entry.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.models.core import Document, Instrument, VerificationRecord
from app.models.enums import AppRole, EvidenceLevel
from app.verification.bank_statement import MatchResult

VERIFIER_ROLES = frozenset(
    {AppRole.FINANCE_VERIFIER.value, "finance_verifier", "verifier"}
)


def request_bank_confirmation(
    session: Session, instrument: Instrument, *, requested_by: str | None
) -> VerificationRecord:
    """Requests a real bank confirmation for this instrument.

    There is no real bank-confirmation integration yet (Phase 3 builds
    the real bank-verifier-portal + statement-import workflow). Per
    CLAUDE.md non-negotiable #1/#3, this must never fabricate a
    "confirmed" response — so until that integration exists, this raises
    rather than returning a fake success. Callers should instead route
    institutions/verifiers to the manual bank-statement import path
    (app.verification.bank_statement) or the real portal once it ships.
    """
    raise NotImplementedError(
        "Real bank-confirmation integration is not implemented. Use the "
        "bank-statement import workflow (app.verification.bank_statement) "
        "or the bank-verifier portal once it is built — never a simulated "
        "confirmation."
    )


def confirm_bank_verification(
    session: Session,
    instrument: Instrument,
    verification_record: VerificationRecord,
    *,
    evidence_document_id: str,
    actor_role: str,
    actor_id: str | None,
    reason: str,
) -> None:
    """The human step that actually raises evidence_level to L2. Requires
    a verifier, a non-empty reason, and an uploaded Document (the bank
    reply evidence) already attached to this instrument."""
    if actor_role not in VERIFIER_ROLES:
        raise PermissionError(f"role '{actor_role}' may not confirm bank verification")
    if not reason or not reason.strip():
        raise ValueError("a non-empty reason is required to confirm bank verification")
    if verification_record.instrument_id != instrument.id:
        raise ValueError("verification record does not belong to this instrument")
    if verification_record.confirmed_amount is None:
        raise ValueError(
            "verification record has no confirmed amount — the bank reply was not a confirmation"
        )

    evidence = session.get(Document, evidence_document_id)
    if evidence is None or evidence.instrument_id != instrument.id:
        raise ValueError(
            "evidence document not found for this instrument — upload the bank reply first"
        )

    before_level = instrument.evidence_level
    instrument.evidence_level = EvidenceLevel.L2_BANK_CONFIRMED
    session.flush()
    append_audit_entry(
        session,
        action="instrument.evidence_level_confirmed",
        entity_type="instrument",
        entity_id=str(instrument.id),
        before={"evidence_level": before_level.value},
        after={
            "evidence_level": EvidenceLevel.L2_BANK_CONFIRMED.value,
            "reason": reason,
            "actor_role": actor_role,
            "evidence_document_id": str(evidence.id),
            "verification_record_id": str(verification_record.id),
        },
        actor_id=actor_id,
        institution_id=str(instrument.institution_id),
    )


def record_ledger_match(
    session: Session, instrument: Instrument, match: MatchResult
) -> VerificationRecord:
    """Records a CSV-reconciliation match as evidence. Real (non-simulated)
    data — the AICTE bank statement itself — but still just evidence until
    a verifier confirms it; see confirm_ledger_reconciliation."""
    record = VerificationRecord(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        level=EvidenceLevel.L3_LEDGER_RECONCILED,
        source="aicte_bank_statement_csv",
        confirmed_amount=match.statement_line.amount,
        raw_payload={
            "confidence": match.confidence,
            "reason": match.reason,
            "statement_row": match.statement_line.row_number,
            "utr": match.statement_line.utr,
            "narration": match.statement_line.narration,
        },
    )
    session.add(record)
    session.flush()
    append_audit_entry(
        session,
        action="verification.ledger_match_recorded",
        entity_type="instrument",
        entity_id=str(instrument.id),
        after={"source": "aicte_bank_statement_csv", "confidence": match.confidence},
        actor_id=None,
        institution_id=str(instrument.institution_id),
    )
    return record


def confirm_ledger_reconciliation(
    session: Session,
    instrument: Instrument,
    verification_record: VerificationRecord,
    *,
    actor_role: str,
    actor_id: str | None,
    reason: str,
) -> None:
    if actor_role not in VERIFIER_ROLES:
        raise PermissionError(
            f"role '{actor_role}' may not confirm ledger reconciliation"
        )
    if not reason or not reason.strip():
        raise ValueError(
            "a non-empty reason is required to confirm ledger reconciliation"
        )
    if verification_record.instrument_id != instrument.id:
        raise ValueError("verification record does not belong to this instrument")
    if verification_record.source != "aicte_bank_statement_csv":
        raise ValueError(
            "ledger reconciliation requires a verification record sourced from the AICTE statement CSV"
        )

    before_level = instrument.evidence_level
    instrument.evidence_level = EvidenceLevel.L3_LEDGER_RECONCILED
    session.flush()
    append_audit_entry(
        session,
        action="instrument.evidence_level_confirmed",
        entity_type="instrument",
        entity_id=str(instrument.id),
        before={"evidence_level": before_level.value},
        after={
            "evidence_level": EvidenceLevel.L3_LEDGER_RECONCILED.value,
            "reason": reason,
            "actor_role": actor_role,
            "verification_record_id": str(verification_record.id),
        },
        actor_id=actor_id,
        institution_id=str(instrument.institution_id),
    )


def list_online_sd_instruments(session: Session) -> list[Instrument]:
    from app.models.enums import InstrumentType

    return list(
        session.execute(
            select(Instrument).where(Instrument.type == InstrumentType.ONLINE_SD)
        )
        .scalars()
        .all()
    )
