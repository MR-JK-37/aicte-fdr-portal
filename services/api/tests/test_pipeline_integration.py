"""End-to-end pipeline test against the live Compose stack: real Garage
(S3), real ClamAV, real Tesseract OCR — only the LLM step is a stand-in
(RegexFDRExtractor), per the module docstrings in app/documents/.
"""

import uuid

import pytest

from app.db import set_app_context
from app.documents.pipeline import (
    DocumentRejectedError,
    confirm_extraction,
    run_pipeline,
)
from app.models import Institution, Instrument
from app.models.enums import EvidenceLevel, InstrumentStatus, InstrumentType
from app.storage import get_object
from tests.fixtures import random_fdr_fields, render_fdr_pdf


def _make_instrument(db_session):
    set_app_context(db_session, role="platform_operator")
    inst = Institution(
        aicte_code=f"P-{uuid.uuid4().hex[:8]}", name="Pipeline Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-P-{uuid.uuid4().hex[:6]}",
        amount=500000,
        status=InstrumentStatus.SUBMITTED,
    )
    db_session.add(instrument)
    db_session.flush()
    return instrument


def test_clean_document_passes_pipeline_and_stores_in_garage(db_session):
    instrument = _make_instrument(db_session)
    # A fixed seed would render byte-identical PDFs across test runs on
    # this shared, never-truncated dev DB — the second run would then
    # (correctly) flag its own document as a pHash duplicate of the first
    # run's leftover row. Seed from a fresh uuid instead so each run's
    # fixture document is actually unique, matching the no-pollution
    # assumption this test makes.
    fields = random_fdr_fields(seed=uuid.uuid4().int)
    pdf_bytes = render_fdr_pdf(fields, 0)

    result = run_pipeline(
        db_session,
        instrument,
        data=pdf_bytes,
        declared_mime_type="application/pdf",
        uploaded_by=None,
    )
    db_session.commit()
    set_app_context(db_session, role="platform_operator")

    assert result.document.sha256
    assert result.validation_flags == []
    assert result.forgery_signals == []
    # bank_name (letters, no digit-run) rather than instrument_number
    # (a long random digit string): Tesseract's digit misreads are
    # exactly the ~1.3% error rate test_extraction_accuracy.py measures
    # and documents — this pipeline-integration test's job is proving
    # the pipeline runs end-to-end (storage, scan, hash, extraction
    # wiring), not re-asserting OCR digit accuracy on every run.
    assert result.extracted.bank_name == fields["bank_name"]
    assert result.extracted.instrument_number is not None

    # Prove it actually landed in Garage, not just a DB row.
    stored = get_object(result.document.storage_key)
    assert stored.startswith(b"%PDF")


def test_pipeline_rejects_disguised_non_document(db_session):
    instrument = _make_instrument(db_session)
    with pytest.raises(DocumentRejectedError) as exc_info:
        run_pipeline(
            db_session,
            instrument,
            data=b"#!/bin/sh\necho pwned\n",
            declared_mime_type="application/pdf",
            uploaded_by=None,
        )
    assert exc_info.value.stage == "magic_byte_check"


def test_evidence_level_stays_l0_until_officer_confirms(db_session):
    instrument = _make_instrument(db_session)
    fields = random_fdr_fields(seed=43)
    pdf_bytes = render_fdr_pdf(fields, 1)

    run_pipeline(
        db_session,
        instrument,
        data=pdf_bytes,
        declared_mime_type="application/pdf",
        uploaded_by=None,
    )
    assert instrument.evidence_level == EvidenceLevel.L0_DECLARED

    confirm_extraction(
        db_session,
        instrument,
        actor_role="scrutiny_officer",
        actor_id=None,
        reason="Matches source document",
    )
    assert instrument.evidence_level == EvidenceLevel.L1_EXTRACTED


def test_confirm_extraction_rejects_unauthorized_role(db_session):
    instrument = _make_instrument(db_session)
    with pytest.raises(PermissionError):
        confirm_extraction(
            db_session,
            instrument,
            actor_role="institution",
            actor_id=None,
            reason="I confirm my own document",
        )
