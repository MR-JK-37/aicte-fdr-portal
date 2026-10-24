"""PS 26265 End-to-End Scenario: New FDR Submission Lifecycle.

Demonstrates the complete workflow required by the PS problem statement and SPEC §18.1:
1. Institution Onboarding & Intake Review (F-02)
2. Document Evidence Vault Upload with ClamAV & PDF Sanitisation (F-04)
3. Instrument Draft, Masking & HMAC Blind Index (F-03)
4. Instrument Submission & Immutable Snapshot Freezing (F-03)
5. Verifiable Receipt Issuance & Public QR Verification (F-20)
6. Workload Queue Routing & Role Assignment (F-24)
7. Scrutiny Casework, Observation Resolution & Internal Note Secrecy (F-09, F-25)
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import (
    AppUser,
    Institution,
    Instrument,
)
from app.models.enums import (
    AppRole,
    DocumentStatus,
)
from tests.fixtures import random_fdr_fields, render_fdr_pdf

client = TestClient(app)


@pytest.fixture
def e2e_users(db_session):
    """Sets up the initial users for the end-to-end scenario."""
    # 1. Existing institution for initial context
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code="AICTE-E2E-2026",
        name="National Institute of Technology and Standards",
    )
    db_session.add(inst)
    db_session.flush()

    # 2. Institution submitter user
    inst_user = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-e2e-inst-{uuid.uuid4().hex[:8]}",
        email="registrar@nit-standards.edu",
        full_name="Dr. Registrar NIT",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(inst_user)

    # 3. Bureau Intake Officer
    intake_officer = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-e2e-intake-{uuid.uuid4().hex[:8]}",
        email="intake.desk@aicte.gov.in",
        full_name="Shri Intake Desk Officer",
        role=AppRole.INTAKE_OFFICER,
        is_active=True,
    )
    db_session.add(intake_officer)

    # 4. Bureau Scrutiny Officer
    scrutiny_officer = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-e2e-so-{uuid.uuid4().hex[:8]}",
        email="scrutiny.lead@aicte.gov.in",
        full_name="Smt. Scrutiny Lead Officer",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    db_session.add(scrutiny_officer)

    db_session.commit()
    return inst, inst_user, intake_officer, scrutiny_officer


def test_complete_new_fdr_submission_flow(db_session, e2e_users):
    inst, inst_user, intake_officer, scrutiny_officer = e2e_users
    inst_token = create_access_token(inst_user)
    intake_token = create_access_token(intake_officer)
    so_token = create_access_token(scrutiny_officer)

    # =========================================================================
    # Step 1: Institution Onboarding Lifecycle (F-02)
    # =========================================================================
    onboard_res = client.post(
        "/v1/institutions/onboarding",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "institution_id": str(inst.id),
            "official_id_ref": "REG-NIT-2026-001",
        },
    )
    assert onboard_res.status_code == status.HTTP_201_CREATED
    onboard_id = onboard_res.json()["id"]

    # Intake Officer inspects intake queue (F-24)
    intake_queue_res = client.get(
        "/v1/queues/intake",
        headers={"Authorization": f"Bearer {intake_token}"},
    )
    assert intake_queue_res.status_code == status.HTTP_200_OK
    queue_items = intake_queue_res.json()
    assert any(q["case_id"] == onboard_id for q in queue_items)

    # Intake Officer approves onboarding (F-02 with SoD enforcement)
    approve_res = client.post(
        f"/v1/institutions/onboarding/{onboard_id}/review",
        headers={"Authorization": f"Bearer {intake_token}"},
        json={"decision": "APPROVE", "reason": "Institutional KYC & charter verified."},
    )
    assert approve_res.status_code == status.HTTP_200_OK
    assert approve_res.json()["status"] == "APPROVED"

    # =========================================================================
    # Step 2: Create FDR Draft & Concurrency Control (F-03)
    # =========================================================================
    fdr_number = f"E2E-FDR-{uuid.uuid4().hex[:8].upper()}"
    draft_res = client.post(
        "/v1/instruments/draft",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "institution_id": str(inst.id),
            "type": "FDR",
            "instrument_number": fdr_number,
            "amount": 2500000.00,
            "issue_date": datetime.now(UTC).isoformat(),
            "maturity_date": (datetime.now(UTC) + timedelta(days=365 * 5)).isoformat(),
            "tenor_months": 60,
            "utr": "UTRE2E987654321",
        },
    )
    assert draft_res.status_code == status.HTTP_201_CREATED
    draft_data = draft_res.json()
    instrument_id = draft_data["id"]
    assert draft_data["status"] == "DRAFT"
    # Ensure identifier is masked in public API view
    assert draft_data["instrument_number"] != fdr_number
    assert draft_data["instrument_number"].endswith(fdr_number[-4:])

    # Verify blind index was computed in DB
    db_inst = db_session.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one()
    assert db_inst.blind_index is not None
    assert len(db_inst.blind_index) == 64

    # =========================================================================
    # Step 3: Direct Document Upload & Antivirus/Sanitisation Pipeline (F-04)
    # =========================================================================
    # Render genuine FDR PDF
    fdr_fields = random_fdr_fields(seed=42)
    clean_pdf = render_fdr_pdf(fdr_fields, 0)

    upload_res = client.post(
        f"/v1/documents/upload-direct?instrument_id={instrument_id}&declared_mime_type=application/pdf",
        headers={"Authorization": f"Bearer {inst_token}"},
        files={"file": ("fdr_scanned_copy.pdf", clean_pdf, "application/pdf")},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == DocumentStatus.ACCEPTED.value
    assert doc_data["sha256"] != "PENDING_UPLOAD"
    assert doc_data["phash"] is not None

    # Verify document download presigned URL
    download_res = client.get(
        f"/v1/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert download_res.status_code == status.HTTP_200_OK
    assert "download_url" in download_res.json()

    # =========================================================================
    # Step 4: Official Instrument Submission & Cryptographic Receipt (F-03, F-20)
    # =========================================================================
    submit_res = client.post(
        f"/v1/instruments/{instrument_id}/submit",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "reason": "Formal submission of 5-year security deposit FDR for AICTE approval"
        },
    )
    assert submit_res.status_code == status.HTTP_200_OK
    assert submit_res.json()["status"] == "SUBMITTED"

    # Verify immutable version snapshot
    versions_res = client.get(
        f"/v1/instruments/{instrument_id}/versions",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert versions_res.status_code == status.HTTP_200_OK
    versions = versions_res.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    snapshot = versions[0]["snapshot"]
    assert snapshot["amount"] == "2500000.00"

    # Download receipt PDF with Ed25519 signature
    receipt_res = client.get(
        f"/v1/instruments/{instrument_id}/receipt",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert receipt_res.status_code == status.HTTP_200_OK
    assert receipt_res.headers["content-type"] == "application/pdf"
    sig_header = receipt_res.headers["X-Receipt-Signature"]
    assert len(sig_header) > 0

    # =========================================================================
    # Step 5: Public QR Verification Endpoint (F-20 / §11.1)
    # =========================================================================
    ver_created_at = datetime.fromisoformat(versions[0]["created_at"]).isoformat()
    receipt_id = f"REC-{uuid.UUID(instrument_id).hex[:8].upper()}-v1"
    public_verify_res = client.get(
        "/v1/public/receipts/verify",
        params={
            "rid": receipt_id,
            "iid": instrument_id,
            "inst": inst.aicte_code,
            "ver": 1,
            "h": versions[0]["content_hash"][:16],
            "ts": ver_created_at,
            "sig": sig_header,
        },
    )
    assert public_verify_res.status_code == status.HTTP_200_OK
    verify_data = public_verify_res.json()
    assert verify_data["verified"] is True
    assert verify_data["receipt_id"] == receipt_id
    assert verify_data["institution_code"] == inst.aicte_code

    # =========================================================================
    # Step 6: Intake Officer Review & Assignment to Scrutiny (F-24, F-03)
    # =========================================================================
    # Intake officer views submitted instrument in intake queue
    intake_q = client.get(
        "/v1/queues/intake",
        headers={"Authorization": f"Bearer {intake_token}"},
    )
    assert intake_q.status_code == status.HTTP_200_OK
    intake_items = intake_q.json()
    assert any(q["case_id"] == instrument_id for q in intake_items)

    # Intake officer assigns case to Scrutiny Officer
    assign_res = client.post(
        "/v1/queues/assign",
        headers={"Authorization": f"Bearer {intake_token}"},
        json={
            "case_id": instrument_id,
            "queue_name": "scrutiny",
            "assigned_to_user_id": str(scrutiny_officer.id),
            "notes": "Verified KYC and bank seal, routing to technical scrutiny.",
        },
    )
    assert assign_res.status_code == status.HTTP_201_CREATED
    assert assign_res.json()["status"] == "ACTIVE"

    # Transition instrument SUBMITTED -> INTAKE_REVIEW -> SCRUTINY
    t1_res = client.post(
        f"/v1/instruments/{instrument_id}/transition",
        headers={"Authorization": f"Bearer {intake_token}"},
        json={
            "to_status": "INTAKE_REVIEW",
            "reason": "Beginning initial document completeness check",
            "reason_code": "INTAKE_START",
        },
    )
    assert t1_res.status_code == status.HTTP_200_OK
    assert t1_res.json()["status"] == "INTAKE_REVIEW"

    t2_res = client.post(
        f"/v1/instruments/{instrument_id}/transition",
        headers={"Authorization": f"Bearer {intake_token}"},
        json={
            "to_status": "SCRUTINY",
            "reason": "Intake completed with all clearances; moving to scrutiny",
            "reason_code": "ROUTED_TO_SCRUTINY",
        },
    )
    assert t2_res.status_code == status.HTTP_200_OK
    assert t2_res.json()["status"] == "SCRUTINY"

    # Scrutiny queue now lists this instrument
    scrutiny_q = client.get(
        "/v1/queues/scrutiny",
        headers={"Authorization": f"Bearer {so_token}"},
    )
    assert scrutiny_q.status_code == status.HTTP_200_OK
    scrutiny_items = scrutiny_q.json()
    assert any(q["case_id"] == instrument_id for q in scrutiny_items)

    # =========================================================================
    # Step 7: Scrutiny Casework, Observation Resolution & Secrecy (F-09, F-25)
    # =========================================================================
    # 1. Scrutiny officer logs an internal note (bureau staff only)
    internal_comment_res = client.post(
        f"/v1/cases/{instrument_id}/comments",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "entity_type": "instrument",
            "comment": "INTERNAL NOTE: Confirm whether the bank's IFSC reflects the recent SBI amalgamation.",
            "is_internal": True,
        },
    )
    assert internal_comment_res.status_code == status.HTTP_201_CREATED

    # 2. Institution views comments - MUST NOT see internal note
    inst_comments = client.get(
        f"/v1/cases/{instrument_id}/comments",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert inst_comments.status_code == status.HTTP_200_OK
    assert len(inst_comments.json()) == 0

    # 3. Scrutiny officer raises observation
    obs_res = client.post(
        "/v1/observations",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "instrument_id": instrument_id,
            "observation": "Joint FDR endorsement clause does not mention AICTE as joint lien holder.",
        },
    )
    assert obs_res.status_code == status.HTTP_201_CREATED
    obs_id = obs_res.json()["id"]

    # 4. Dispatch observation to institution
    dispatch_res = client.post(
        f"/v1/observations/{obs_id}/send-to-institution",
        headers={"Authorization": f"Bearer {so_token}"},
    )
    assert dispatch_res.status_code == status.HTTP_200_OK
    assert dispatch_res.json()["status"] == "AWAITING_INSTITUTION"

    # 5. Institution responds
    respond_res = client.post(
        f"/v1/observations/{obs_id}/respond",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "response_text": "We have obtained an amended lien endorsement letter from SBI naming AICTE.",
        },
    )
    assert respond_res.status_code == status.HTTP_200_OK
    assert respond_res.json()["status"] == "RESPONSE_RECEIVED"

    # 6. Scrutiny officer resolves observation
    resolve_res = client.post(
        f"/v1/observations/{obs_id}/resolve",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "resolution_code": "AMENDMENT_ACCEPTED",
            "reason": "Amended lien endorsement complies with AICTE 2024 handbook §3.4.",
        },
    )
    assert resolve_res.status_code == status.HTTP_200_OK
    assert resolve_res.json()["status"] == "RESOLVED"
