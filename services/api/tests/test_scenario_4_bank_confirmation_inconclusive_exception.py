"""SPEC §18.1 Scenario 4: Bank Confirmation Lifecycle, Verifier Isolation, SoD, and Inconclusive Exception.

Mandatory assertions:
1. Bank confirmation request workflow remains pending until authorised source evidence is received and reviewed.
2. Participating Bank Verifier is isolated to assigned bank and requests only (cannot see other banks' requests).
3. Response without a verifiable sender identity is rejected.
4. Overdue request creates escalation notification only (never automatic rejection).
5. Separation of Duties: Requester cannot decide on their own confirmation request.
6. Inconclusive response opens a ReconciliationException (never a fraud label); instrument remains at current evidence level.
7. Authorized verifier ACCEPT decision advances instrument to L2_BANK_CONFIRMED with audit verification record.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution, Instrument, VerificationRecord
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType
from app.models.workflow import ReconciliationException

client = TestClient(app)


@pytest.fixture
def scenario_4_setup(db_session):
    uid = uuid.uuid4().hex[:6]
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"AICTE-S4-{uid}",
        name="Apex Technical University",
    )
    db_session.add(inst)
    db_session.flush()

    # Submitter
    submitter = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-s4-inst-{uid}",
        email=f"submitter-{uid}@apex.edu",
        full_name="Registrar Apex",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )

    # Scrutiny Officer (Requester)
    requester_officer = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-s4-req-{uid}",
        email=f"requester-{uid}@aicte-india.org",
        full_name="Officer Requester",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )

    # Independent Finance Verifier (Decider)
    independent_verifier = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-s4-fin-{uid}",
        email=f"verifier-{uid}@aicte-india.org",
        full_name="Finance Verifier Two",
        role=AppRole.FINANCE_VERIFIER,
        is_active=True,
    )

    # Bank Verifier for State Bank of India
    sbi_verifier = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-s4-sbi-{uid}",
        email=f"verifier-{uid}@sbi.co.in",
        full_name="SBI Verifier",
        role=AppRole.BANK_VERIFIER,
        is_active=True,
    )

    # Bank Verifier for Punjab National Bank (Different Bank)
    pnb_verifier = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-s4-pnb-{uid}",
        email=f"verifier-{uid}@pnb.co.in",
        full_name="PNB Verifier",
        role=AppRole.BANK_VERIFIER,
        is_active=True,
    )

    db_session.add_all(
        [
            submitter,
            requester_officer,
            independent_verifier,
            sbi_verifier,
            pnb_verifier,
        ]
    )
    db_session.commit()

    return {
        "institution": inst,
        "submitter": submitter,
        "requester_officer": requester_officer,
        "independent_verifier": independent_verifier,
        "sbi_verifier": sbi_verifier,
        "pnb_verifier": pnb_verifier,
        "submitter_token": create_access_token(submitter),
        "requester_token": create_access_token(requester_officer),
        "verifier_token": create_access_token(independent_verifier),
        "sbi_token": create_access_token(sbi_verifier),
        "pnb_token": create_access_token(pnb_verifier),
    }


def test_scenario_4_bank_confirmation_workflow_and_invariants(
    scenario_4_setup, db_session
):
    inst = scenario_4_setup["institution"]
    requester = scenario_4_setup["requester_officer"]
    sbi_verifier = scenario_4_setup["sbi_verifier"]

    req_token = scenario_4_setup["requester_token"]
    dec_token = scenario_4_setup["verifier_token"]
    sbi_token = scenario_4_setup["sbi_token"]
    pnb_token = scenario_4_setup["pnb_token"]

    # Create Instrument
    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-S4-CONF-001",
        amount=Decimal("2500000.00"),
        status=InstrumentStatus.SCRUTINY,
        evidence_level=EvidenceLevel.L1_EXTRACTED,
    )
    db_session.add(instrument)
    db_session.commit()

    # 1. Bureau officer issues Bank Confirmation Request (F-06)
    create_payload = {
        "instrument_id": str(instrument.id),
        "bank_name": "State Bank of India",
        "branch_name": "Parliament Street",
        "ifsc": "SBIN0000691",
        "account_number_ref": "38294019283",
        "assigned_bank_verifier_id": str(sbi_verifier.id),
        "notes": "Verify FDR genuineness and lock-in period for AICTE regulation",
    }
    create_res = client.post(
        "/v1/verification/bank-requests",
        headers={"Authorization": f"Bearer {req_token}"},
        json=create_payload,
    )
    assert create_res.status_code == status.HTTP_201_CREATED, create_res.text
    bcr_data = create_res.json()
    bcr_id = bcr_data["id"]
    tracking_number = bcr_data["tracking_number"]

    assert bcr_data["status"] == "AWAITING_RESPONSE"
    assert bcr_data["requested_by"] == str(requester.id)
    assert tracking_number.startswith("BCR-2026-")

    # 2. Bank Verifier Isolation check (SPEC §18.1-4):
    # PNB verifier cannot view SBI request
    pnb_view_res = client.get(
        f"/v1/verification/bank-requests/{bcr_id}",
        headers={"Authorization": f"Bearer {pnb_token}"},
    )
    assert pnb_view_res.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ), pnb_view_res.text

    # SBI verifier can view their assigned request
    sbi_view_res = client.get(
        f"/v1/verification/bank-requests/{bcr_id}",
        headers={"Authorization": f"Bearer {sbi_token}"},
    )
    assert sbi_view_res.status_code == status.HTTP_200_OK

    # 3. Overdue escalation notification only (MASTER_PROMPT §F-06: request overdue -> escalation notification only, no status change to rejected)
    esc_res = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/escalate",
        headers={"Authorization": f"Bearer {req_token}"},
        json={"reason": "14-day bank confirmation response SLA breached"},
    )
    assert esc_res.status_code == status.HTTP_200_OK
    assert esc_res.json()["status"] == "AWAITING_RESPONSE"  # Never auto-rejected!

    # 4. Response without verifiable sender identity is rejected
    unauth_resp = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/respond",
        headers={"Authorization": f"Bearer {pnb_token}"},  # Wrong verifier!
        json={
            "confirmed_fields": {"amount": 2500000.00},
            "notes": "Attempting unauthorized reply",
        },
    )
    assert unauth_resp.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    )

    # 5. Authorised Bank Verifier responds
    valid_resp = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/respond",
        headers={"Authorization": f"Bearer {sbi_token}"},
        json={
            "confirmed_fields": {
                "amount": "2500000.00",
                "instrument_number": "FDR-S4-CONF-001",
                "bank_status": "CONFIRMED_ACTIVE",
            },
            "notes": "FDR record matches SBI core banking ledger. Lien recorded in favor of Member Secretary AICTE.",
        },
    )
    assert valid_resp.status_code == status.HTTP_200_OK
    assert valid_resp.json()["status"] == "UNDER_REVIEW"

    # 6. Separation of Duties enforcement:
    # Requester officer tries to decide on their own confirmation request -> MUST BE FORBIDDEN
    sod_res = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/decision",
        headers={"Authorization": f"Bearer {req_token}"},
        json={"decision": "ACCEPT", "reason": "Self-approval attempt"},
    )
    assert sod_res.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ), "Requester must be blocked by Separation of Duties"

    # 7. Independent Verifier marks INCONCLUSIVE (SPEC §18.1 Scenario 4: "inconclusive response opens an exception")
    inconclusive_payload = {
        "decision": "INCONCLUSIVE",
        "reason": "Branch seal is illegible on core banking scan; awaiting physical verification dispatch",
    }
    inconcl_res = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/decision",
        headers={"Authorization": f"Bearer {dec_token}"},
        json=inconclusive_payload,
    )
    assert inconcl_res.status_code == status.HTTP_200_OK
    dec_data = inconcl_res.json()
    assert dec_data["status"] == "INCONCLUSIVE"
    assert dec_data["decision"] == "INCONCLUSIVE"

    # Invariant: INCONCLUSIVE must open ReconciliationException and NOT change evidence level or label as fraud
    db_session.expire_all()
    inst_after_inconcl = db_session.get(Instrument, instrument.id)
    assert inst_after_inconcl.evidence_level == EvidenceLevel.L1_EXTRACTED

    # Exception record opened
    exc_records = list(
        db_session.execute(
            select(ReconciliationException).where(
                ReconciliationException.instrument_id == instrument.id
            )
        )
        .scalars()
        .all()
    )
    assert len(exc_records) == 1
    assert exc_records[0].exception_type == "INCONCLUSIVE_BANK_CONFIRMATION"
    assert exc_records[0].status == "OPEN"
    assert exc_records[0].details["tracking_number"] == tracking_number


def test_scenario_4_authorized_accept_advances_to_l2(scenario_4_setup, db_session):
    """When an independent verifier accepts valid bank reply evidence, instrument advances to L2_BANK_CONFIRMED."""
    inst = scenario_4_setup["institution"]
    sbi_verifier = scenario_4_setup["sbi_verifier"]

    req_token = scenario_4_setup["requester_token"]
    dec_token = scenario_4_setup["verifier_token"]
    sbi_token = scenario_4_setup["sbi_token"]

    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-S4-ACCEPT-002",
        amount=Decimal("1000000.00"),
        status=InstrumentStatus.SCRUTINY,
        evidence_level=EvidenceLevel.L1_EXTRACTED,
    )
    db_session.add(instrument)
    db_session.commit()

    # 1. Create request
    create_res = client.post(
        "/v1/verification/bank-requests",
        headers={"Authorization": f"Bearer {req_token}"},
        json={
            "instrument_id": str(instrument.id),
            "bank_name": "State Bank of India",
            "assigned_bank_verifier_id": str(sbi_verifier.id),
        },
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    bcr_id = create_res.json()["id"]

    # 2. Bank responds
    respond_res = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/respond",
        headers={"Authorization": f"Bearer {sbi_token}"},
        json={
            "confirmed_fields": {"amount": "1000000.00", "holder": inst.name},
            "notes": "Confirmed and authenticated by Chief Manager.",
        },
    )
    assert respond_res.status_code == status.HTTP_200_OK

    # 3. Independent verifier decides ACCEPT
    decide_res = client.post(
        f"/v1/verification/bank-requests/{bcr_id}/decision",
        headers={"Authorization": f"Bearer {dec_token}"},
        json={
            "decision": "ACCEPT",
            "reason": "Bank reply confirmed with core banking verification and official digital signature",
        },
    )
    assert decide_res.status_code == status.HTTP_200_OK
    assert decide_res.json()["status"] == "ACCEPTED"

    # 4. Check instrument evidence level advanced to L2_BANK_CONFIRMED
    db_session.expire_all()
    inst_post = db_session.get(Instrument, instrument.id)
    assert inst_post.evidence_level == EvidenceLevel.L2_BANK_CONFIRMED

    # 5. Check VerificationRecord created with source=bank_confirmation
    vr = list(
        db_session.execute(
            select(VerificationRecord).where(
                VerificationRecord.instrument_id == instrument.id
            )
        )
        .scalars()
        .all()
    )
    assert len(vr) == 1
    assert vr[0].level == EvidenceLevel.L2_BANK_CONFIRMED
    assert vr[0].source == "bank_confirmation"
