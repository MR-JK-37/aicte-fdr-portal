"""Verification workflow orchestration.

Hard rule from the brief, enforced here structurally rather than just by
convention: "The evidence level is never raised by AI. Only human actions
with uploaded evidence move L1->L2->L3." So every *_check/request/import
function below only ever creates a VerificationRecord (evidence) — never
touches instrument.evidence_level. Only the confirm_* functions, which
are role-gated and require a human actor, change evidence_level, and each
one writes an audit entry.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.models.core import Document, Instrument, VerificationRecord
from app.models.enums import EvidenceLevel
from app.verification import mock_bank_api
from app.verification.bank_statement import MatchResult

VERIFIER_ROLES = frozenset({"verifier"})


def request_bank_confirmation(
    session: Session, instrument: Instrument, *, requested_by: str | None
) -> VerificationRecord:
    """Calls the SIMULATED bank-confirmation API and records the (signed,
    simulated) response as evidence. Does not change evidence_level."""
    response = mock_bank_api.request_confirmation(
        instrument.instrument_number, ifsc=None, declared_amount=Decimal(instrument.amount)
    )
    record = VerificationRecord(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        level=EvidenceLevel.L2_BANK_CONFIRMED,
        source="mock_bank_api",
        confirmed_amount=response.confirmed_amount,
        raw_payload={
            "simulated": True,
            "confirmed": response.confirmed,
            "bank_reference": response.bank_reference,
            "signature": response.signature,
            "payload": response.payload,
            "latency_ms": response.latency_ms,
        },
    )
    session.add(record)
    session.flush()
    append_audit_entry(
        session,
        action="verification.bank_confirmation_requested",
        entity_type="instrument",
        entity_id=str(instrument.id),
        after={"source": "mock_bank_api", "confirmed": response.confirmed, "simulated": True},
        actor_id=requested_by,
        institution_id=str(instrument.institution_id),
    )
    return record


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
        raise ValueError("verification record has no confirmed amount — the mock bank reply was not a confirmation")

    evidence = session.get(Document, evidence_document_id)
    if evidence is None or evidence.instrument_id != instrument.id:
        raise ValueError("evidence document not found for this instrument — upload the bank reply first")

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


def record_ledger_match(session: Session, instrument: Instrument, match: MatchResult) -> VerificationRecord:
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
        raise PermissionError(f"role '{actor_role}' may not confirm ledger reconciliation")
    if not reason or not reason.strip():
        raise ValueError("a non-empty reason is required to confirm ledger reconciliation")
    if verification_record.instrument_id != instrument.id:
        raise ValueError("verification record does not belong to this instrument")
    if verification_record.source != "aicte_bank_statement_csv":
        raise ValueError("ledger reconciliation requires a verification record sourced from the AICTE statement CSV")

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

    return list(session.execute(select(Instrument).where(Instrument.type == InstrumentType.ONLINE_SD)).scalars().all())
