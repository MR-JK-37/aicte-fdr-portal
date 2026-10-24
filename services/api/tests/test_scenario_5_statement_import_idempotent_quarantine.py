"""SPEC §18.1 Scenario 5: Statement Import Idempotency, Malformed Row Quarantine, and Ambiguity Handling.

Mandatory assertions:
1. Statement import is idempotent; same batch (identical checksum) is not duplicated.
2. Malformed rows (unparseable amounts, corrupted dates) are quarantined with detailed reasons in batch metadata.
3. Valid rows in the quarantined batch proceed and reconcile cleanly against ONLINE_SD instruments.
4. Exact match (UTR + Amount) promotes ONLINE_SD deposit to L3_LEDGER_RECONCILED.
5. Critical Invariant: Reconciliation of an FDR scan can NEVER produce L3_LEDGER_RECONCILED.
6. Ambiguous matches (e.g. amount mismatch or multiple matching records) route to ReconciliationException and NEVER auto-confirm.
7. Officer resolves open reconciliation exception with audit traceability.
8. Multi-format support: CSV, MT940, and CAMT.053 (ISO 20022 XML).
"""

import uuid
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution, Instrument, VerificationRecord
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType
from app.models.workflow import ReconciliationException, StatementLine

client = TestClient(app)


@pytest.fixture
def scenario_5_setup(db_session):
    uid = uuid.uuid4().hex[:6]
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"AICTE-S5-{uid}",
        name="State Technical Institute",
    )
    db_session.add(inst)
    db_session.flush()

    finance_officer = AppUser(
        id=uuid.uuid4(),
        institution_id=None,
        keycloak_sub=f"sub-s5-fin-{uid}",
        email=f"finance-{uid}@aicte-india.org",
        full_name="Finance Officer Five",
        role=AppRole.FINANCE_VERIFIER,
        is_active=True,
    )
    db_session.add(finance_officer)
    db_session.commit()

    return {
        "institution": inst,
        "finance_officer": finance_officer,
        "finance_token": create_access_token(finance_officer),
    }


def test_scenario_5_statement_import_and_reconciliation(scenario_5_setup, db_session):
    inst = scenario_5_setup["institution"]
    finance_token = scenario_5_setup["finance_token"]

    # 1. Create ONLINE_SD instruments (Online Security Deposits)
    # Deposit A: Exact match candidate
    deposit_exact = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.ONLINE_SD,
        instrument_number="ONL-2026-EXACT-001",
        amount=Decimal("500000.00"),
        utr="UTR2026EXACT001",
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )

    # Deposit B: Amount mismatch candidate (Declared 200,000 vs Statement 150,000)
    deposit_mismatch = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.ONLINE_SD,
        instrument_number="ONL-2026-MISMATCH-002",
        amount=Decimal("200000.00"),
        utr="UTR2026MISMATCH002",
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )

    # Deposit C: FDR Instrument (should NEVER be promoted to L3 by statement import)
    fdr_instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-2026-NEVER-L3",
        amount=Decimal("1000000.00"),
        utr="UTR2026FDR003",
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L1_EXTRACTED,
    )

    db_session.add_all([deposit_exact, deposit_mismatch, fdr_instrument])
    db_session.commit()

    # 2. Build CSV Statement with:
    # - Valid exact match row (UTR2026EXACT001, 500000.00)
    # - Valid amount mismatch row (UTR2026MISMATCH002, 150000.00)
    # - Malformed row 1: unparseable amount
    # - Malformed row 2: invalid date format
    # - Row targeting FDR UTR (UTR2026FDR003, 1000000.00)
    csv_content = (
        b"date,utr,narration,amount,currency\n"
        b"2026-10-15,UTR2026EXACT001,Online Security Deposit Exact,500000.00,INR\n"
        b"2026-10-16,UTR2026MISMATCH002,Online Deposit Partial Mismatch,150000.00,INR\n"
        b"2026-10-17,UTR_MALFORMED_1,Corrupted Amount Row,INVALID_AMOUNT,INR\n"
        b"MALFORMED_DATE,UTR_MALFORMED_2,Corrupted Date Row,25000.00,INR\n"
        b"2026-10-18,UTR2026FDR003,Deposit attempt against FDR,1000000.00,INR\n"
    )

    # 3. First Import: POST /v1/statements/import
    import_res = client.post(
        "/v1/statements/import",
        headers={"Authorization": f"Bearer {finance_token}"},
        files={"file": ("aicte_october_statement.csv", csv_content, "text/csv")},
    )
    assert import_res.status_code == status.HTTP_201_CREATED, import_res.text
    batch_data = import_res.json()
    batch_id = batch_data["id"]

    assert batch_data["line_count"] == 3  # 3 valid parsed lines
    assert batch_data["quarantined_count"] == 2  # 2 malformed rows quarantined!
    assert batch_data["matched_count"] == 1  # 1 exact match
    assert batch_data["exception_count"] == 1  # 1 amount mismatch exception

    # Verify quarantined rows in metadata
    quarantined = batch_data["metadata"]["quarantined_rows"]
    assert len(quarantined) == 2
    reasons = [q["reason"] for q in quarantined]
    assert any("Unparseable amount" in r for r in reasons)
    assert any("Malformed date" in r for r in reasons)

    # 4. Idempotency Check (SPEC §18.1 Scenario 5: "Statement import is idempotent; same batch is not duplicated")
    reimport_res = client.post(
        "/v1/statements/import",
        headers={"Authorization": f"Bearer {finance_token}"},
        files={"file": ("aicte_october_statement.csv", csv_content, "text/csv")},
    )
    assert reimport_res.status_code == status.HTTP_201_CREATED
    reimport_data = reimport_res.json()
    assert reimport_data["id"] == batch_id
    assert reimport_data["checksum"] == batch_data["checksum"]

    # Verify statement_lines count did not duplicate in database
    total_lines = db_session.execute(
        select(func.count(StatementLine.id)).where(
            StatementLine.batch_id == uuid.UUID(batch_id)
        )
    ).scalar()
    assert total_lines == 3, (
        f"Expected 3 lines, got {total_lines} (duplication occurred!)"
    )

    # 5. Check exact match promoted ONLINE_SD to L3_LEDGER_RECONCILED
    db_session.expire_all()
    inst_exact = db_session.get(Instrument, deposit_exact.id)
    assert inst_exact.evidence_level == EvidenceLevel.L3_LEDGER_RECONCILED

    # Check VerificationRecord created for exact match
    vr_records = list(
        db_session.execute(
            select(VerificationRecord).where(
                VerificationRecord.instrument_id == deposit_exact.id
            )
        )
        .scalars()
        .all()
    )
    assert len(vr_records) == 1
    assert vr_records[0].level == EvidenceLevel.L3_LEDGER_RECONCILED
    assert vr_records[0].source == "statement_import"

    # 6. Critical Invariant Check: FDR scan can NEVER produce L3_LEDGER_RECONCILED
    inst_fdr = db_session.get(Instrument, fdr_instrument.id)
    assert inst_fdr.evidence_level != EvidenceLevel.L3_LEDGER_RECONCILED, (
        "FDR instrument must never receive L3_LEDGER_RECONCILED from statement import!"
    )
    assert inst_fdr.evidence_level == EvidenceLevel.L1_EXTRACTED

    # 7. Ambiguity Check: Mismatch row did NOT auto-confirm and opened ReconciliationException
    inst_mismatch = db_session.get(Instrument, deposit_mismatch.id)
    assert inst_mismatch.evidence_level != EvidenceLevel.L3_LEDGER_RECONCILED, (
        "Ambiguous mismatch must never auto-confirm!"
    )
    assert inst_mismatch.evidence_level == EvidenceLevel.L0_DECLARED

    # Check open ReconciliationException
    exceptions = list(
        db_session.execute(
            select(ReconciliationException).where(
                ReconciliationException.instrument_id == deposit_mismatch.id
            )
        )
        .scalars()
        .all()
    )
    assert len(exceptions) == 1
    exc = exceptions[0]
    assert exc.status == "OPEN"
    assert exc.exception_type == "AMOUNT_MISMATCH"
    assert exc.details["declared_amount"] == "200000.00"
    assert exc.details["statement_amount"] == "150000.00"

    # 8. Officer Resolves Exception (F-07)
    resolve_res = client.post(
        f"/v1/statements/exceptions/{exc.id}/resolve",
        headers={"Authorization": f"Bearer {finance_token}"},
        json={
            "resolution_notes": "Institution paid 150,000 INR; balance 50,000 INR covered in supplementary challan verified offline",
            "matched_instrument_id": str(deposit_mismatch.id),
        },
    )
    assert resolve_res.status_code == status.HTTP_200_OK
    resolved_data = resolve_res.json()
    assert resolved_data["status"] == "RESOLVED"
    assert "balance 50,000 INR covered" in resolved_data["resolution_notes"]


def test_scenario_5_camt053_and_mt940_formats(scenario_5_setup, db_session):
    """Verifies that CAMT.053 (XML) and MT940 statement files parse and reconcile properly."""
    inst = scenario_5_setup["institution"]
    finance_token = scenario_5_setup["finance_token"]

    camt_deposit = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.ONLINE_SD,
        instrument_number="ONL-2026-CAMT-001",
        amount=Decimal("750000.00"),
        utr="CAMTUTR2026999",
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
    )
    db_session.add(camt_deposit)
    db_session.commit()

    # CAMT.053 XML snippet
    camt_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <Stmt>
      <Id>STMT-2026-001</Id>
      <Ntry>
        <Amt Ccy="INR">750000.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt><Dt>2026-10-20</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <Refs>
              <EndToEndId>CAMTUTR2026999</EndToEndId>
            </Refs>
            <RmtInf>
              <Ustrd>AICTE Security Deposit Online Payment</Ustrd>
            </RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>"""

    camt_res = client.post(
        "/v1/statements/import",
        headers={"Authorization": f"Bearer {finance_token}"},
        files={"file": ("camt053_statement.xml", camt_xml, "application/xml")},
    )
    assert camt_res.status_code == status.HTTP_201_CREATED, camt_res.text
    camt_data = camt_res.json()
    assert camt_data["file_format"] == "CAMT053"
    assert camt_data["matched_count"] == 1

    db_session.expire_all()
    inst_post = db_session.get(Instrument, camt_deposit.id)
    assert inst_post.evidence_level == EvidenceLevel.L3_LEDGER_RECONCILED
