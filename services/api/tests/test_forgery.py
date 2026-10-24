import uuid

from app.documents.forgery import (
    check_duplicate_instrument_number,
    check_duplicate_phash,
    check_pdf_producer_metadata,
)
from app.models import Document, Institution, Instrument
from app.models.enums import InstrumentType
from tests.fixtures import random_fdr_fields, render_fdr_pdf


def test_duplicate_instrument_number_across_institutions_detected(db_session):
    inst_a = Institution(aicte_code=f"FA-{uuid.uuid4().hex[:8]}", name="Forgery Test A")
    inst_b = Institution(aicte_code=f"FB-{uuid.uuid4().hex[:8]}", name="Forgery Test B")
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    shared_number = f"FDR-DUP-{uuid.uuid4().hex[:6]}"
    existing = Instrument(
        institution_id=inst_a.id,
        type=InstrumentType.FDR,
        instrument_number=shared_number,
        amount=1,
    )
    db_session.add(existing)
    db_session.flush()

    signal = check_duplicate_instrument_number(
        db_session, inst_b.id, shared_number, exclude_instrument_id=None
    )
    assert signal is not None
    assert signal.signal == "duplicate_instrument_number"


def test_same_institution_reusing_number_is_not_flagged_as_cross_institution_duplicate(
    db_session,
):
    inst = Institution(aicte_code=f"FC-{uuid.uuid4().hex[:8]}", name="Forgery Test C")
    db_session.add(inst)
    db_session.flush()
    number = f"FDR-SAME-{uuid.uuid4().hex[:6]}"
    existing = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=number,
        amount=1,
    )
    db_session.add(existing)
    db_session.flush()

    signal = check_duplicate_instrument_number(
        db_session, inst.id, number, exclude_instrument_id=None
    )
    assert signal is None


def test_duplicate_phash_detected(db_session):
    inst = Institution(aicte_code=f"FD-{uuid.uuid4().hex[:8]}", name="Forgery Test D")
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-PHASH-1",
        amount=1,
    )
    db_session.add(instrument)
    db_session.flush()
    existing_doc = Document(
        institution_id=inst.id,
        instrument_id=instrument.id,
        storage_key="x",
        sha256="a" * 64,
        phash="deadbeefdeadbeef",
        mime_type="application/pdf",
    )
    db_session.add(existing_doc)
    db_session.flush()

    signal = check_duplicate_phash(
        db_session, "deadbeefdeadbeef", exclude_document_id=None
    )
    assert signal is not None
    assert signal.signal == "duplicate_phash"


def test_no_phash_match_returns_none(db_session):
    signal = check_duplicate_phash(
        db_session, "ffffffffffffffff", exclude_document_id=None
    )
    assert signal is None


def test_pdf_producer_metadata_clean_for_reportlab_output():
    data = render_fdr_pdf(random_fdr_fields(seed=3), 0)
    signal = check_pdf_producer_metadata(data)
    # reportlab's own producer string isn't in the suspicious-tools list.
    assert signal is None
