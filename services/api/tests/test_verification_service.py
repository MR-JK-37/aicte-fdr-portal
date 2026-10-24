import uuid

import pytest

from app.models import Document, Institution, Instrument
from app.models.enums import EvidenceLevel, InstrumentType
from app.verification.bank_statement import MatchResult, StatementLine
from app.verification.service import (
    confirm_bank_verification,
    confirm_ledger_reconciliation,
    record_ledger_match,
    request_bank_confirmation,
)


def _make_instrument(db_session):
    inst = Institution(
        aicte_code=f"V-{uuid.uuid4().hex[:8]}", name="Verification Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-V-{uuid.uuid4().hex[:6]}",
        amount=500000,
    )
    db_session.add(instrument)
    db_session.flush()
    return instrument


def test_request_bank_confirmation_is_not_implemented(db_session):
    """There is no real bank-confirmation integration yet. This must
    raise — never fabricate a "confirmed" response (CLAUDE.md #1/#3)."""
    instrument = _make_instrument(db_session)
    assert instrument.evidence_level == EvidenceLevel.L0_DECLARED

    with pytest.raises(NotImplementedError):
        request_bank_confirmation(db_session, instrument, requested_by=None)

    assert instrument.evidence_level == EvidenceLevel.L0_DECLARED


def test_confirm_bank_verification_requires_verifier_role(db_session):
    instrument = _make_instrument(db_session)
    from app.models.core import VerificationRecord

    record = VerificationRecord(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        level=EvidenceLevel.L2_BANK_CONFIRMED,
        source="bank_verifier_reply",
        confirmed_amount=500000,
        raw_payload={},
    )
    db_session.add(record)
    doc = Document(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        storage_key="x",
        sha256="a" * 64,
        mime_type="application/pdf",
    )
    db_session.add(doc)
    db_session.flush()

    with pytest.raises(PermissionError):
        confirm_bank_verification(
            db_session,
            instrument,
            record,
            evidence_document_id=str(doc.id),
            actor_role="scrutiny_officer",
            actor_id=None,
            reason="trying to self-approve",
        )


def test_confirm_bank_verification_requires_evidence_document(db_session):
    instrument = _make_instrument(db_session)
    # Force a confirmed record regardless of the simulated failure chance.
    from app.models.core import VerificationRecord

    record = VerificationRecord(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        level=EvidenceLevel.L2_BANK_CONFIRMED,
        source="bank_verifier_reply",
        confirmed_amount=500000,
        raw_payload={},
    )
    db_session.add(record)
    db_session.flush()

    with pytest.raises(ValueError, match="evidence"):
        confirm_bank_verification(
            db_session,
            instrument,
            record,
            evidence_document_id=str(uuid.uuid4()),
            actor_role="verifier",
            actor_id=None,
            reason="no evidence uploaded",
        )


def test_confirm_bank_verification_succeeds_and_promotes_to_l2(db_session):
    instrument = _make_instrument(db_session)
    from app.models.core import VerificationRecord

    record = VerificationRecord(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        level=EvidenceLevel.L2_BANK_CONFIRMED,
        source="bank_verifier_reply",
        confirmed_amount=500000,
        raw_payload={},
    )
    db_session.add(record)
    doc = Document(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        storage_key="x",
        sha256="b" * 64,
        mime_type="application/pdf",
    )
    db_session.add(doc)
    db_session.flush()

    confirm_bank_verification(
        db_session,
        instrument,
        record,
        evidence_document_id=str(doc.id),
        actor_role="verifier",
        actor_id=None,
        reason="Bank reply matches declared amount",
    )
    assert instrument.evidence_level == EvidenceLevel.L2_BANK_CONFIRMED


def test_confirm_ledger_reconciliation_requires_csv_source(db_session):
    instrument = _make_instrument(db_session)
    from app.models.core import VerificationRecord

    wrong_source_record = VerificationRecord(
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        level=EvidenceLevel.L3_LEDGER_RECONCILED,
        source="bank_verifier_reply",
        confirmed_amount=500000,
        raw_payload={},
    )
    db_session.add(wrong_source_record)
    db_session.flush()

    with pytest.raises(ValueError, match="AICTE statement CSV"):
        confirm_ledger_reconciliation(
            db_session,
            instrument,
            wrong_source_record,
            actor_role="verifier",
            actor_id=None,
            reason="wrong source",
        )


def test_record_ledger_match_and_confirm_promotes_to_l3(db_session):
    instrument = _make_instrument(db_session)
    match = MatchResult(
        statement_line=StatementLine(
            row_number=2, date=None, utr="UTR1", narration="n", amount=500000
        ),
        instrument_id=str(instrument.id),
        confidence="exact_utr_amount",
        reason="matched",
    )
    record = record_ledger_match(db_session, instrument, match)
    assert instrument.evidence_level == EvidenceLevel.L0_DECLARED  # not raised yet

    confirm_ledger_reconciliation(
        db_session,
        instrument,
        record,
        actor_role="verifier",
        actor_id=None,
        reason="CSV line matches",
    )
    assert instrument.evidence_level == EvidenceLevel.L3_LEDGER_RECONCILED


def test_confirm_requires_nonempty_reason(db_session):
    instrument = _make_instrument(db_session)
    match = MatchResult(
        statement_line=StatementLine(
            row_number=2, date=None, utr="UTR1", narration="n", amount=500000
        ),
        instrument_id=str(instrument.id),
        confidence="exact_utr_amount",
        reason="matched",
    )
    record = record_ledger_match(db_session, instrument, match)
    with pytest.raises(ValueError, match="reason"):
        confirm_ledger_reconciliation(
            db_session,
            instrument,
            record,
            actor_role="verifier",
            actor_id=None,
            reason="",
        )
