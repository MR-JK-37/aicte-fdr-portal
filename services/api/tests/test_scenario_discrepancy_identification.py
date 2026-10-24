"""Test PS 26265 Scenario: Discrepancy Identification (F-08 / SPEC §14.1, §18.1).

Problem Statement Scenario:
"Discrepancy Identification:
Institution submits FDR with discrepancies (amount mismatch, date inconsistency, invalid IFSC, duplicate number).
System detects and highlights discrepancies:
- Flagged with severity
- Creates draft observation for officer scrutiny
- NEVER automatically rejects an instrument or labels institution as fraudulent
- Officer converts discrepancy into formal scrutiny observation or acknowledges it."
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import (
    AppUser,
    Discrepancy,
    Document,
    Institution,
    Instrument,
    ScrutinyObservation,
)
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType
from app.models.workflow import DocumentExtraction

client = TestClient(app)


@pytest.fixture
def discrepancy_setup(db_session):
    test_id = uuid.uuid4().hex[:6]

    inst_a = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-{test_id}-DISC-A",
        name="Institute of Technology Discrepancy Alpha",
    )
    inst_b = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-{test_id}-DISC-B",
        name="Institute of Management Beta",
    )
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    # Pre-existing instrument in Inst B to test duplicate detection
    existing_fdr_b = Instrument(
        id=uuid.uuid4(),
        institution_id=inst_b.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-SHARED-DUP-99999",
        amount=Decimal("1000000.00"),
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L1_EXTRACTED,
    )
    db_session.add(existing_fdr_b)

    # Scrutiny Officer
    officer = AppUser(
        id=uuid.uuid4(),
        email=f"scrutiny_{test_id}@aicte.gov.in",
        role=AppRole.SCRUTINY_OFFICER,
        full_name="AICTE Senior Scrutiny Officer",
        keycloak_sub=f"sub-scrutiny-{test_id}",
    )
    # Institution User
    inst_user = AppUser(
        id=uuid.uuid4(),
        email=f"registrar_{test_id}@discalpha.edu.in",
        role=AppRole.INSTITUTION_SUBMITTER,
        institution_id=inst_a.id,
        full_name="College Registrar",
        keycloak_sub=f"sub-inst-{test_id}",
    )
    db_session.add_all([officer, inst_user])
    db_session.commit()

    officer_token = create_access_token(officer)
    inst_token = create_access_token(inst_user)

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "officer": officer,
        "officer_token": officer_token,
        "inst_user": inst_user,
        "inst_token": inst_token,
    }


def test_scenario_discrepancy_identification_and_no_auto_reject(
    discrepancy_setup, db_session
):
    inst_a = discrepancy_setup["inst_a"]
    officer_token = discrepancy_setup["officer_token"]
    inst_token = discrepancy_setup["inst_token"]

    # 1. Create Instrument with multiple deliberate discrepancies:
    # - Declared amount: 500,000 INR
    # - Extracted amount: 350,000 INR (Amount Mismatch)
    # - Issue date: 2028-01-01, Maturity: 2026-01-01 (Date Inconsistency)
    # - IFSC: "INVALID_IFSC_CODE" (Invalid IFSC)
    # - Instrument number: "FDR-SHARED-DUP-99999" (Duplicate Instrument Number)
    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst_a.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-SHARED-DUP-99999",
        amount=Decimal("500000.00"),
        issue_date=datetime(2028, 1, 1, tzinfo=UTC),
        maturity_date=datetime(2026, 1, 1, tzinfo=UTC),
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )
    db_session.add(instrument)
    db_session.flush()

    # Create linked Document
    doc = Document(
        id=uuid.uuid4(),
        institution_id=inst_a.id,
        instrument_id=instrument.id,
        storage_key="test/fdr.pdf",
        sha256="test-sha256",
        mime_type="application/pdf",
        status="clean",
    )
    db_session.add(doc)
    db_session.flush()

    # Link DocumentExtraction with extracted amount 350,000 and invalid IFSC
    extraction = DocumentExtraction(
        id=uuid.uuid4(),
        document_id=doc.id,
        instrument_id=instrument.id,
        raw_text="Fixed Deposit Receipt Amount: Rs. 3,50,000 IFSC: INVALID_IFSC_CODE",
        candidate_fields={
            "amount": {"value": 350000, "confidence": 0.95},
            "instrument_number": {"value": "FDR-SHARED-DUP-99999", "confidence": 0.98},
            "ifsc": {"value": "INVALID_IFSC_CODE", "confidence": 0.90},
        },
    )
    db_session.add(extraction)
    db_session.commit()

    # 2. Evaluate Discrepancies via API
    eval_res = client.post(
        f"/v1/instruments/{instrument.id}/discrepancies/evaluate",
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert eval_res.status_code == status.HTTP_200_OK, eval_res.text
    discrepancies = eval_res.json()

    fields_flagged = {d["field"]: d for d in discrepancies}
    assert "amount" in fields_flagged
    assert "dates" in fields_flagged
    assert "ifsc" in fields_flagged
    assert "instrument_number" in fields_flagged

    assert fields_flagged["amount"]["severity"] == "CRITICAL"
    assert "350,000" in fields_flagged["amount"]["extracted_value"]

    assert fields_flagged["dates"]["severity"] == "CRITICAL"
    assert "issue=" in fields_flagged["dates"]["declared_value"]

    assert fields_flagged["ifsc"]["severity"] == "CRITICAL"
    assert fields_flagged["ifsc"]["declared_value"] == "INVALID_IFSC_CODE"

    assert fields_flagged["instrument_number"]["severity"] == "CRITICAL"

    # 3. CRITICAL INVARIANT: Instrument is NOT automatically rejected or labelled fraud
    db_session.expire_all()
    reloaded_inst = db_session.get(Instrument, instrument.id)
    assert reloaded_inst.status == InstrumentStatus.SUBMITTED, (
        "Discrepancies must NEVER auto-reject an instrument!"
    )

    # 4. Bureau Officer converts Amount Mismatch into a formal ScrutinyObservation (F-09)
    amount_disc_id = fields_flagged["amount"]["id"]
    obs_res = client.post(
        f"/v1/instruments/{instrument.id}/discrepancies/{amount_disc_id}/generate-observation",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "observation_text": "Declared deposit amount ₹500,000 differs from FDR certificate value ₹350,000. Submit revised FDR."
        },
    )
    assert obs_res.status_code == status.HTTP_201_CREATED, obs_res.text
    obs_data = obs_res.json()
    assert obs_data["status"] in ("OPEN", "open")
    assert "Declared deposit amount" in obs_data["observation"]

    # Verify Discrepancy status updated
    db_session.expire_all()
    disc_amount = db_session.get(Discrepancy, uuid.UUID(amount_disc_id))
    assert disc_amount.status == "OBSERVATION_GENERATED"

    # Verify ScrutinyObservation row created in database
    obs_db = (
        db_session.execute(
            select(ScrutinyObservation).where(
                ScrutinyObservation.instrument_id == instrument.id
            )
        )
        .scalars()
        .all()
    )
    assert len(obs_db) == 1
    assert obs_db[0].status in ("OPEN", "open")

    # 5. Bureau Officer acknowledges another discrepancy with justification
    ifsc_disc_id = fields_flagged["ifsc"]["id"]
    ack_res = client.post(
        f"/v1/instruments/{instrument.id}/discrepancies/{ifsc_disc_id}/acknowledge",
        headers={"Authorization": f"Bearer {officer_token}"},
        json={
            "reason": "Bank merger branch remapped IFSC verified by scrutiny committee"
        },
    )
    assert ack_res.status_code == status.HTTP_200_OK, ack_res.text
    ack_data = ack_res.json()
    assert ack_data["status"] == "ACKNOWLEDGED"

    # 6. Non-bureau user cannot generate observations
    forbidden_res = client.post(
        f"/v1/instruments/{instrument.id}/discrepancies/{amount_disc_id}/generate-observation",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"observation_text": "Trying to raise observation"},
    )
    assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN
