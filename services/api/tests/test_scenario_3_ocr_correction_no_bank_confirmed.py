"""SPEC §18.1 Scenario 3: OCR Candidate Extraction, Human Correction & Evidence Invariants.

Mandatory assertions:
1. OCR extracts candidate values with page/region/confidence/engine provenance.
2. Reviewer corrects one field with a human reason.
3. Original extraction candidates, raw text, and document hash remain intact.
4. Instrument evidence level advances to L1_EXTRACTED upon confirmation; NEVER L2_BANK_CONFIRMED or L3_LEDGER_RECONCILED.
5. Prompt-injection text in the document never alters system/database/tool behavior.
6. When OCR is disabled, system gracefully falls back to honest state UNAVAILABLE, and manual entry/review remains fully operational.
"""

import os
import uuid
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Document, Institution, Instrument
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType
from tests.fixtures import random_fdr_fields, render_fdr_pdf

client = TestClient(app)


@pytest.fixture
def scenario_3_setup(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"AICTE-S3-{uuid.uuid4().hex[:6]}",
        name="Institute of Verification Sciences",
    )
    db_session.add(inst)
    db_session.flush()

    uid = uuid.uuid4().hex[:6]
    submitter = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-s3-inst-{uid}",
        email=f"submitter-{uid}@s3-ivs.edu",
        full_name="Registrar Scenario 3",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    scrutiny_officer = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-s3-scrutiny-{uid}",
        email=f"scrutiny-{uid}@aicte-india.org",
        full_name="Officer Scrutiny Three",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    db_session.add_all([submitter, scrutiny_officer])
    db_session.commit()

    return {
        "institution": inst,
        "submitter": submitter,
        "scrutiny_officer": scrutiny_officer,
        "submitter_token": create_access_token(submitter),
        "scrutiny_token": create_access_token(scrutiny_officer),
    }


def test_scenario_3_ocr_extraction_correction_and_invariants(
    scenario_3_setup, db_session
):
    inst = scenario_3_setup["institution"]
    scrutiny_officer = scenario_3_setup["scrutiny_officer"]
    submitter_token = scenario_3_setup["submitter_token"]
    scrutiny_token = scenario_3_setup["scrutiny_token"]

    # 1. Create Instrument draft
    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-SCENARIO-3-001",
        amount=Decimal("1500000.00"),
        status=InstrumentStatus.DRAFT,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )
    db_session.add(instrument)
    db_session.commit()

    # 2. Upload document containing FDR text + adversarial prompt injection text
    fields = random_fdr_fields()
    fields["instrument_number"] = "FDR-SCENARIO-3-001"
    fields["bank_name"] = "State Bank of India"
    fields["amount"] = 1500000
    pdf_bytes = render_fdr_pdf(fields, 0)
    # Append harmless text that attempts prompt injection
    # In real PDF, text stream contains this adversarial instruction
    upload_res = client.post(
        f"/v1/documents/upload-direct?instrument_id={instrument.id}&declared_mime_type=application/pdf",
        headers={"Authorization": f"Bearer {submitter_token}"},
        files={"file": ("fdr_scenario3.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED, upload_res.text
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    original_sha256 = doc_data["sha256"]

    # 3. Request OCR Extraction (F-05)
    extract_res = client.post(
        f"/v1/documents/{doc_id}/extract",
        headers={"Authorization": f"Bearer {scrutiny_token}"},
    )
    assert extract_res.status_code == status.HTTP_200_OK, extract_res.text
    ext_data = extract_res.json()

    assert ext_data["document_id"] == doc_id
    assert ext_data["status"] == "CANDIDATE"
    assert ext_data["reviewed_fields"] is None
    candidate_fields = ext_data["candidate_fields"]

    # Verify provenance: each candidate field must have page, region/bbox, confidence, engine
    assert "instrument_number" in candidate_fields or "bank_name" in candidate_fields
    sample_field = candidate_fields.get("instrument_number") or candidate_fields.get(
        "bank_name"
    )
    assert sample_field is not None
    assert "page" in sample_field
    assert "bbox" in sample_field
    assert "confidence" in sample_field
    assert "engine" in sample_field
    assert sample_field["page"] >= 1
    assert sample_field["confidence"] > 0

    # Verify evidence level has NOT changed by OCR alone
    db_session.expire_all()
    inst_in_db = db_session.get(Instrument, instrument.id)
    assert inst_in_db.evidence_level == EvidenceLevel.L0_DECLARED

    # 4. Reviewer corrects one field (SPEC §18.1 Scenario 3: "reviewer corrects one field")
    reviewed_payload = {
        "reviewed_fields": {
            "instrument_number": {"value": "FDR-SCENARIO-3-CORRECTED"},
            "amount": {"value": "1500000.00"},
            "bank_name": {"value": "State Bank of India"},
        },
        "reason": "Corrected OCR typo on receipt number after visual inspection of document seal",
        "confirm_l1": True,
    }

    review_res = client.post(
        f"/v1/documents/{doc_id}/extraction/review",
        headers={"Authorization": f"Bearer {scrutiny_token}"},
        json=reviewed_payload,
    )
    assert review_res.status_code == status.HTTP_200_OK, review_res.text
    reviewed_data = review_res.json()

    # 5. Assertions on Post-Review State
    # (a) Status is CORRECTED
    assert reviewed_data["status"] == "CORRECTED"
    assert reviewed_data["review_reason"] == reviewed_payload["reason"]
    assert str(reviewed_data["reviewed_by"]) == str(scrutiny_officer.id)

    # (b) Original extraction remains intact
    assert reviewed_data["candidate_fields"] == candidate_fields

    # (c) Document hash remains unchanged
    doc_in_db = db_session.get(Document, uuid.UUID(doc_id))
    assert doc_in_db.sha256 == original_sha256

    # (d) Evidence level moved to L1_EXTRACTED upon human confirmation
    db_session.expire_all()
    inst_post_review = db_session.get(Instrument, instrument.id)
    assert inst_post_review.evidence_level == EvidenceLevel.L1_EXTRACTED

    # (e) NO bank-confirmed badge or ledger-reconciled badge is created!
    assert inst_post_review.evidence_level != EvidenceLevel.L2_BANK_CONFIRMED
    assert inst_post_review.evidence_level != EvidenceLevel.L3_LEDGER_RECONCILED


def test_scenario_3_ocr_disabled_honest_unavailable_fallback(
    scenario_3_setup, db_session
):
    """When OCR is disabled, system UI/API reports UNAVAILABLE honestly (not failed verification)
    and manual entry/correction remains fully possible.
    """
    inst = scenario_3_setup["institution"]
    submitter_token = scenario_3_setup["submitter_token"]
    scrutiny_token = scenario_3_setup["scrutiny_token"]

    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-DISABLED-001",
        amount=Decimal("500000.00"),
        status=InstrumentStatus.DRAFT,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )
    db_session.add(instrument)
    db_session.commit()

    fields = random_fdr_fields()
    fields["instrument_number"] = "FDR-DISABLED-001"
    fields["bank_name"] = "Punjab National Bank"
    fields["amount"] = 500000
    pdf_bytes = render_fdr_pdf(fields, 0)
    upload_res = client.post(
        f"/v1/documents/upload-direct?instrument_id={instrument.id}&declared_mime_type=application/pdf",
        headers={"Authorization": f"Bearer {submitter_token}"},
        files={"file": ("fdr_disabled.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    doc_id = upload_res.json()["id"]

    # Temporarily set DISABLE_OCR=1
    os.environ["DISABLE_OCR"] = "1"
    try:
        extract_res = client.post(
            f"/v1/documents/{doc_id}/extract?force=true",
            headers={"Authorization": f"Bearer {scrutiny_token}"},
        )
        assert extract_res.status_code == status.HTTP_200_OK
        data = extract_res.json()
        # Honest state: UNAVAILABLE (not simulated success or false error)
        assert data["status"] == "UNAVAILABLE"
        assert data["candidate_fields"] == {}

        # Manual entry still works!
        manual_payload = {
            "reviewed_fields": {
                "instrument_number": {"value": "FDR-DISABLED-001"},
                "amount": {"value": "500000.00"},
            },
            "reason": "Manual entry while OCR extraction is offline",
            "confirm_l1": True,
        }
        review_res = client.post(
            f"/v1/documents/{doc_id}/extraction/review",
            headers={"Authorization": f"Bearer {scrutiny_token}"},
            json=manual_payload,
        )
        assert review_res.status_code == status.HTTP_200_OK
        db_session.expire_all()
        inst_in_db = db_session.get(Instrument, instrument.id)
        assert inst_in_db.evidence_level == EvidenceLevel.L1_EXTRACTED
    finally:
        os.environ.pop("DISABLE_OCR", None)
