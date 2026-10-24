"""Institution Onboarding and Registry Tests (F-02 / SPEC §8.2 / F-19)."""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution
from app.models.enums import AppRole

client = TestClient(app)


@pytest.fixture
def test_setup(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"ONB-{uuid.uuid4().hex[:6]}",
        name="Institute of Technology Onboarding",
    )
    db_session.add(inst)

    applicant = AppUser(
        id=uuid.uuid4(),
        institution_id=None,  # Not yet bound until council approves onboarding
        keycloak_sub=f"sub-app-{uuid.uuid4().hex[:8]}",
        email=f"applicant-{uuid.uuid4().hex[:6]}@tech.edu",
        full_name="Dr. Applicant Representative",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(applicant)

    intake_officer = AppUser(
        id=uuid.uuid4(),
        keycloak_sub=f"sub-intake-{uuid.uuid4().hex[:8]}",
        email=f"intake-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Intake Officer",
        role=AppRole.INTAKE_OFFICER,
        is_active=True,
    )
    db_session.add(intake_officer)

    platform_op = AppUser(
        id=uuid.uuid4(),
        keycloak_sub=f"sub-op-{uuid.uuid4().hex[:8]}",
        email=f"op-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="Platform Operator",
        role=AppRole.PLATFORM_OPERATOR,
        is_active=True,
    )
    db_session.add(platform_op)

    db_session.commit()
    return inst, applicant, intake_officer, platform_op


def test_onboarding_application_lifecycle(db_session, test_setup):
    inst, applicant, intake_officer, _platform_op = test_setup
    applicant_token = create_access_token(applicant)
    intake_token = create_access_token(intake_officer)

    # 1. Applicant submits onboarding request
    res = client.post(
        "/v1/institutions/onboarding",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "institution_id": str(inst.id),
            "official_id_ref": "AUTH-LETTER-2026-99",
            "authority_letter_doc_id": None,
        },
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["status"] == "PENDING"
    assert data["official_id_ref"] == "AUTH-LETTER-2026-99"
    req_id = data["id"]

    # 2. Duplicate submission while PENDING should return 409
    res_dup = client.post(
        "/v1/institutions/onboarding",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "institution_id": str(inst.id),
            "official_id_ref": "AUTH-LETTER-2026-99",
        },
    )
    assert res_dup.status_code == status.HTTP_409_CONFLICT

    # 3. Separation of duties: Applicant CANNOT self-approve
    res_self = client.post(
        f"/v1/institutions/onboarding/{req_id}/review",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={"decision": "APPROVE", "reason": "Self approving"},
    )
    # Fails with 403 Forbidden due to SoD or missing permission
    assert res_self.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_401_UNAUTHORIZED,
    ]

    # 4. Intake officer reviews and approves
    res_approve = client.post(
        f"/v1/institutions/onboarding/{req_id}/review",
        headers={"Authorization": f"Bearer {intake_token}"},
        json={
            "decision": "APPROVE",
            "reason": "Authorisation letter verified against council records",
        },
    )
    assert res_approve.status_code == status.HTTP_200_OK
    approved_data = res_approve.json()
    assert approved_data["status"] == "APPROVED"
    assert approved_data["reviewed_by"] == str(intake_officer.id)

    # Verify applicant user was activated in database
    db_session.expire_all()
    from app.db import set_app_context

    set_app_context(db_session, role="platform_operator")
    updated_applicant = db_session.execute(
        select(AppUser).where(AppUser.id == applicant.id)
    ).scalar_one()
    assert updated_applicant.is_active is True
    assert updated_applicant.institution_id == inst.id


def test_batch_import_with_provenance_and_deduplication(db_session, test_setup):
    inst, applicant, _intake_officer, platform_op = test_setup
    op_token = create_access_token(platform_op)
    applicant_token = create_access_token(applicant)

    # 1. Non-admin cannot batch import
    res_denied = client.post(
        "/v1/institutions/batch-import",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "source_owner": "Council Registry",
            "mapping_version": "v1.0",
            "rows": [{"aicte_code": "1-9999", "name": "Fake College"}],
        },
    )
    assert res_denied.status_code == status.HTTP_403_FORBIDDEN

    # 2. Platform operator runs batch import
    code_new = f"NEW-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/v1/institutions/batch-import",
        headers={"Authorization": f"Bearer {op_token}"},
        json={
            "source_owner": "Bureau Registry Division",
            "mapping_version": "v2.1",
            "rows": [
                {
                    "aicte_code": inst.aicte_code,
                    "name": "Existing College Name",
                },  # Duplicate
                {"aicte_code": code_new, "name": "Brand New Polytechnic"},
            ],
        },
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["imported_count"] == 1
    assert data["duplicates_skipped"] == 1
    assert len(data["file_hash"]) == 64
    assert data["mapping_version"] == "v2.1"
