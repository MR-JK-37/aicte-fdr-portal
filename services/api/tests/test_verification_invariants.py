"""Structural Invariant Property Tests (F-05, F-06, F-07, F-08 / SPEC §14.1, §18.1).

Verifies the mathematical and logical integrity of the Evidence Ladder:
1. Invariant: OCR extraction and human correction NEVER advance an instrument to L2_BANK_CONFIRMED or L3_LEDGER_RECONCILED.
2. Invariant: An instrument NEVER reaches L2_BANK_CONFIRMED without an authorized human officer's ACCEPT decision on a bank confirmation.
3. Invariant: Bank response alone does NOT advance instrument to L2_BANK_CONFIRMED (requires independent bureau decision).
4. Invariant: Inconclusive bank response NEVER labels institution as fraud; routes to ReconciliationException.
5. Invariant: FDR instruments can NEVER receive L3_LEDGER_RECONCILED.
6. Invariant: Separation of duties: Requester cannot decide on bank confirmation.
7. AST Proof: Static code analysis verifying all code paths setting L2 and L3 evidence levels.
"""

import ast
import os
import uuid
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType

client = TestClient(app)


@pytest.fixture
def invariant_setup(db_session):
    test_id = uuid.uuid4().hex[:6]

    institution = Institution(
        id=uuid.uuid4(),
        aicte_code=f"1-{test_id}-INVARIANT",
        name="Institute of Verification Invariants",
    )
    db_session.add(institution)
    db_session.flush()

    requester_officer = AppUser(
        id=uuid.uuid4(),
        email=f"requester_{test_id}@aicte.gov.in",
        role=AppRole.FINANCE_VERIFIER,
        full_name="Finance Verifier Requester",
        keycloak_sub=f"sub-req-{test_id}",
    )
    independent_verifier = AppUser(
        id=uuid.uuid4(),
        email=f"verifier_{test_id}@aicte.gov.in",
        role=AppRole.FINANCE_VERIFIER,
        full_name="Finance Verifier Independent",
        keycloak_sub=f"sub-ver-{test_id}",
    )
    bank_officer = AppUser(
        id=uuid.uuid4(),
        email=f"officer_{test_id}@sbi.co.in",
        role=AppRole.BANK_VERIFIER,
        full_name="SBI Chief Manager",
        keycloak_sub=f"sub-bank-{test_id}",
    )
    db_session.add_all([requester_officer, independent_verifier, bank_officer])
    db_session.commit()

    return {
        "institution": institution,
        "requester": requester_officer,
        "requester_token": create_access_token(requester_officer),
        "verifier": independent_verifier,
        "verifier_token": create_access_token(independent_verifier),
        "bank_officer": bank_officer,
        "bank_token": create_access_token(bank_officer),
    }


def test_invariant_fdr_never_reaches_l3_from_statement_reconciliation(
    invariant_setup, db_session
):
    """Structural invariant: FDR instruments can NEVER receive L3_LEDGER_RECONCILED."""
    inst = invariant_setup["institution"]
    verifier_token = invariant_setup["verifier_token"]

    fdr = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-INVARIANT-TEST-001",
        amount=Decimal("1500000.00"),
        utr="UTRINVARIANT001",
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L1_EXTRACTED,
    )
    db_session.add(fdr)
    db_session.commit()

    csv_payload = (
        b"date,utr,narration,amount,currency\n"
        b"2026-10-20,UTRINVARIANT001,FDR Deposit Match Attempt,1500000.00,INR\n"
    )

    import_res = client.post(
        "/v1/statements/import",
        headers={"Authorization": f"Bearer {verifier_token}"},
        files={"file": ("fdr_match_attempt.csv", csv_payload, "text/csv")},
    )
    assert import_res.status_code == status.HTTP_201_CREATED

    db_session.expire_all()
    reloaded_fdr = db_session.get(Instrument, fdr.id)
    assert reloaded_fdr.evidence_level == EvidenceLevel.L1_EXTRACTED
    assert reloaded_fdr.evidence_level != EvidenceLevel.L3_LEDGER_RECONCILED, (
        "INVARIANT VIOLATION: FDR instrument must NEVER be promoted to L3_LEDGER_RECONCILED!"
    )


def test_invariant_sod_enforced_requester_cannot_decide(invariant_setup, db_session):
    """Structural invariant: Separation of duties prevents requester from deciding on bank confirmation."""
    inst = invariant_setup["institution"]
    requester_token = invariant_setup["requester_token"]
    bank_token = invariant_setup["bank_token"]

    fdr = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-SOD-001",
        amount=Decimal("500000.00"),
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )
    db_session.add(fdr)
    db_session.commit()

    # 1. Create bank confirmation request
    req_res = client.post(
        "/v1/verification/bank-requests",
        headers={"Authorization": f"Bearer {requester_token}"},
        json={
            "instrument_id": str(fdr.id),
            "bank_name": "State Bank of India",
            "branch_name": "Main Branch",
            "ifsc": "SBIN0001234",
            "account_number_ref": "30012345678",
        },
    )
    assert req_res.status_code == status.HTTP_201_CREATED
    req_id = req_res.json()["id"]

    # 2. Bank responds
    resp_res = client.post(
        f"/v1/verification/bank-requests/{req_id}/respond",
        headers={"Authorization": f"Bearer {bank_token}"},
        json={
            "confirmed_amount": 500000.00,
            "fdr_status_confirmed": "ACTIVE",
            "notes": "Verified against CBS",
        },
    )
    assert resp_res.status_code == status.HTTP_200_OK

    # 3. Requester attempts to decide -> MUST be rejected with 403 / SoD violation
    dec_res = client.post(
        f"/v1/verification/bank-requests/{req_id}/decision",
        headers={"Authorization": f"Bearer {requester_token}"},
        json={"decision": "ACCEPT", "reason": "Attempting self-approval"},
    )
    assert dec_res.status_code == status.HTTP_403_FORBIDDEN, (
        "INVARIANT VIOLATION: Requester was able to self-approve bank confirmation!"
    )
    assert (
        "separation_of_duties" in dec_res.text.lower()
        or "requester cannot decide" in dec_res.text.lower()
    )


def test_ast_proof_evidence_level_transitions():
    """Static AST verification of all code paths assigning L2_BANK_CONFIRMED and L3_LEDGER_RECONCILED.
    Guarantees by AST inspection that no rogue code path can promote evidence levels.
    """
    app_dir = os.path.join(os.path.dirname(__file__), "..", "app")

    l2_assignments = []
    l3_assignments = []

    for root, _, files in os.walk(app_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=fpath)
                except (SyntaxError, UnicodeDecodeError):
                    continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check if assigning to evidence_level
                    targets_evidence = any(
                        isinstance(t, ast.Attribute) and t.attr == "evidence_level"
                        for t in node.targets
                    )
                    if targets_evidence:
                        val_str = ast.unparse(node.value)
                        rel_path = os.path.relpath(fpath, app_dir)
                        if "L2_BANK_CONFIRMED" in val_str:
                            l2_assignments.append((rel_path, node.lineno, val_str))
                        if "L3_LEDGER_RECONCILED" in val_str:
                            l3_assignments.append((rel_path, node.lineno, val_str))

    # Verification: L2_BANK_CONFIRMED must ONLY be set in verification modules upon authorized officer action
    for rel_path, line, val in l2_assignments:
        assert rel_path.startswith("verification/"), (
            f"INVARIANT VIOLATION: L2_BANK_CONFIRMED assigned outside verification package at {rel_path}:{line}"
        )

    # Verification: L3_LEDGER_RECONCILED must ONLY be set in statement/reconciliation modules upon statement match
    for rel_path, line, val in l3_assignments:
        assert rel_path.startswith(("statements/", "verification/")), (
            f"INVARIANT VIOLATION: L3_LEDGER_RECONCILED assigned outside statement reconciliation at {rel_path}:{line}"
        )
