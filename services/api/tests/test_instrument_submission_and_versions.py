"""SPEC §18.1 Scenario 2: Instrument Draft, Immutable Versioning, Receipt, No Silent Overwrites."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution
from app.models.enums import AppRole
from app.models.workflow import InstrumentVersion
from app.receipts.signer import verify_receipt_signature

client = TestClient(app)


@pytest.fixture
def submitter_setup(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"SUB-{uuid.uuid4().hex[:6]}",
        name="Institute of Financial Engineering",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-usr-{uuid.uuid4().hex[:8]}",
        email=f"submitter-{uuid.uuid4().hex[:6]}@eng.edu",
        full_name="Prof. Submitter",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(user)

    intake_officer = AppUser(
        id=uuid.uuid4(),
        keycloak_sub=f"sub-in-{uuid.uuid4().hex[:8]}",
        email=f"intake-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="Council Intake Officer",
        role=AppRole.INTAKE_OFFICER,
        is_active=True,
    )
    db_session.add(intake_officer)

    db_session.commit()
    return inst, user, intake_officer


def test_scenario_2_submission_immutable_version_receipt_queue(
    db_session, submitter_setup
):
    inst, user, intake_officer = submitter_setup
    token = create_access_token(user)
    intake_token = create_access_token(intake_officer)

    now = datetime.now(UTC)
    issue_date = now - timedelta(days=10)
    maturity_date = now + timedelta(days=365 * 5)

    # 1. Validation test: maturity <= issue_date rejected
    res_invalid_dates = client.post(
        "/v1/instruments/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "institution_id": str(inst.id),
            "type": "FDR",
            "instrument_number": "FDR-INVALID-001",
            "amount": "1500000.00",
            "issue_date": now.isoformat(),
            "maturity_date": (now - timedelta(days=1)).isoformat(),
        },
    )
    assert res_invalid_dates.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Create valid draft instrument
    res_draft = client.post(
        "/v1/instruments/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "institution_id": str(inst.id),
            "type": "FDR",
            "instrument_number": "FDR-SEC2-001",
            "amount": "1500000.00",
            "issue_date": issue_date.isoformat(),
            "maturity_date": maturity_date.isoformat(),
            "tenor_months": 60,
        },
    )
    assert res_draft.status_code == status.HTTP_201_CREATED
    inst_data = res_draft.json()
    instrument_id = inst_data["id"]
    assert inst_data["status"] == "DRAFT"
    # By default, instrument number is masked
    assert inst_data["instrument_number"].startswith("XXXX")

    # 3. Edit draft with optimistic concurrency
    res_edit = client.put(
        f"/v1/instruments/{instrument_id}/draft",
        headers={
            "Authorization": f"Bearer {token}",
            "If-Match": f'"{inst_data["updated_at"]}"',
        },
        json={
            "amount": "2000000.00",
        },
    )
    assert res_edit.status_code == status.HTTP_200_OK
    assert res_edit.json()["amount"] == "2000000.00"

    # 4. Submit instrument: freezes version snapshot + transitions to SUBMITTED + issues receipt
    res_submit = client.post(
        f"/v1/instruments/{instrument_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reason": "Official deposit submission for B.Tech approval cycle 2026-27",
            "policy_version": "APH-2024-27-v1.0",
        },
    )
    assert res_submit.status_code == status.HTTP_200_OK
    submitted_data = res_submit.json()
    assert submitted_data["status"] == "SUBMITTED"

    # 5. Verify immutable version snapshot exists in DB
    from app.db import set_app_context

    set_app_context(db_session, role="platform_operator")
    versions = (
        db_session.execute(
            select(InstrumentVersion).where(
                InstrumentVersion.instrument_id == uuid.UUID(instrument_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(versions) == 1
    v1 = versions[0]
    assert v1.version_number == 1
    assert v1.snapshot["amount"] == "2000000.00"
    assert v1.snapshot["instrument_number"] == "FDR-SEC2-001"
    assert len(v1.content_hash) == 64

    # 6. Verify NO SILENT OVERWRITES:
    # Attempting to edit a submitted instrument via draft update returns 400 Bad Request
    res_illegal_edit = client.put(
        f"/v1/instruments/{instrument_id}/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": "3000000.00"},
    )
    assert res_illegal_edit.status_code == status.HTTP_400_BAD_REQUEST
    assert "must be DRAFT" in res_illegal_edit.json()["detail"]

    # 7. Query version history endpoint
    res_versions = client.get(
        f"/v1/instruments/{instrument_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_versions.status_code == status.HTTP_200_OK
    v_list = res_versions.json()
    assert len(v_list) == 1
    assert v_list[0]["version_number"] == 1
    assert v_list[0]["content_hash"] == v1.content_hash

    # 8. Download generated cryptographic receipt (F-20)
    res_receipt = client.get(
        f"/v1/instruments/{instrument_id}/receipt",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_receipt.status_code == status.HTTP_200_OK
    assert res_receipt.headers["content-type"] == "application/pdf"
    assert res_receipt.content.startswith(b"%PDF")
    sig = res_receipt.headers.get("X-Receipt-Signature")
    assert sig is not None

    # Verify signature matches
    expected_qr_payload = {
        "rid": f"REC-{uuid.UUID(instrument_id).hex[:8].upper()}-v1",
        "iid": instrument_id,
        "inst": inst.aicte_code,
        "ver": 1,
        "h": v1.content_hash[:16],
        "ts": v1.created_at.isoformat(),
    }
    assert verify_receipt_signature(expected_qr_payload, sig) is True

    # 9. Verify instrument appears in Council Intake Queue (F-24)
    res_queue = client.get(
        "/v1/queues/intake",
        headers={"Authorization": f"Bearer {intake_token}"},
    )
    assert res_queue.status_code == status.HTTP_200_OK
    queue_items = res_queue.json()
    matching = [q for q in queue_items if q["case_id"] == instrument_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "SUBMITTED"
    assert matching[0]["institution_id"] == str(inst.id)


def test_list_instruments_endpoint(db_session, submitter_setup):
    inst, user, _ = submitter_setup
    token = create_access_token(user)

    # Initially empty or pre-existing list for this institution
    res = client.get("/v1/instruments", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.json(), list)

    # Create draft
    draft_res = client.post(
        "/v1/instruments/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "institution_id": str(inst.id),
            "type": "FDR",
            "instrument_number": f"LIST-FDR-{uuid.uuid4().hex[:6]}",
            "amount": "1500000.00",
        },
    )
    assert draft_res.status_code == status.HTTP_201_CREATED
    inst_id = draft_res.json()["id"]

    # Now list returns the created instrument
    res2 = client.get("/v1/instruments", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == status.HTTP_200_OK
    items = res2.json()
    assert any(i["id"] == inst_id for i in items)


