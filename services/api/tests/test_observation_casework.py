"""SPEC §18.1 Scenario 6: Observation Lifecycle, Threaded Comments, Internal Note Secrecy."""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import AppRole, InstrumentStatus, InstrumentType

client = TestClient(app)


@pytest.fixture
def casework_setup(db_session):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"CAS-{uuid.uuid4().hex[:6]}",
        name="Institute of Casework Tests",
    )
    db_session.add(inst)
    db_session.flush()

    inst_user = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-iu-{uuid.uuid4().hex[:8]}",
        email=f"inst-{uuid.uuid4().hex[:6]}@case.edu",
        full_name="Institution Submitter",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    db_session.add(inst_user)

    scrutiny_officer = AppUser(
        id=uuid.uuid4(),
        keycloak_sub=f"sub-so-{uuid.uuid4().hex[:8]}",
        email=f"so-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Scrutiny Officer",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    db_session.add(scrutiny_officer)

    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-CASE-001",
        amount=1500000.0,
        status=InstrumentStatus.SCRUTINY,
    )
    db_session.add(instrument)
    db_session.commit()

    return inst, inst_user, scrutiny_officer, instrument


def test_scenario_6_observation_lifecycle(db_session, casework_setup):
    _inst, inst_user, scrutiny_officer, instrument = casework_setup
    inst_token = create_access_token(inst_user)
    so_token = create_access_token(scrutiny_officer)

    # 1. Scrutiny officer raises observation
    res_obs = client.post(
        "/v1/observations",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "instrument_id": str(instrument.id),
            "observation": "Joint FDR pledge clause does not explicitly name AICTE as second holder.",
        },
    )
    assert res_obs.status_code == status.HTTP_201_CREATED
    obs_data = res_obs.json()
    obs_id = obs_data["id"]
    assert obs_data["status"] == "OPEN"

    # 2. Dispatch to institution: OPEN -> AWAITING_INSTITUTION
    res_dispatch = client.post(
        f"/v1/observations/{obs_id}/send-to-institution",
        headers={"Authorization": f"Bearer {so_token}"},
    )
    assert res_dispatch.status_code == status.HTTP_200_OK
    assert res_dispatch.json()["status"] == "AWAITING_INSTITUTION"

    # 3. Institution responds: AWAITING_INSTITUTION -> RESPONSE_RECEIVED
    res_respond = client.post(
        f"/v1/observations/{obs_id}/respond",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "response_text": "We have submitted the bank-amended joint pledge endorsement letter.",
        },
    )
    assert res_respond.status_code == status.HTTP_200_OK
    assert res_respond.json()["status"] == "RESPONSE_RECEIVED"

    # 4. Officer resolves observation: RESPONSE_RECEIVED -> RESOLVED
    res_resolve = client.post(
        f"/v1/observations/{obs_id}/resolve",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "resolution_code": "AMENDMENT_VERIFIED",
            "reason": "Bank endorsement matches AICTE joint name guidelines.",
        },
    )
    assert res_resolve.status_code == status.HTTP_200_OK
    assert res_resolve.json()["status"] == "RESOLVED"


def test_casework_comments_internal_secrecy(db_session, casework_setup):
    _inst, inst_user, scrutiny_officer, instrument = casework_setup
    inst_token = create_access_token(inst_user)
    so_token = create_access_token(scrutiny_officer)

    # 1. Scrutiny officer posts an INTERNAL note (bureau staff only)
    res_int = client.post(
        f"/v1/cases/{instrument.id}/comments",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "entity_type": "instrument",
            "comment": "INTERNAL NOTE: Check with branch manager regarding recent IFSC merger.",
            "is_internal": True,
        },
    )
    assert res_int.status_code == status.HTTP_201_CREATED
    assert res_int.json()["is_internal"] is True

    # 2. Scrutiny officer posts a PUBLIC note (institution visible)
    res_pub = client.post(
        f"/v1/cases/{instrument.id}/comments",
        headers={"Authorization": f"Bearer {so_token}"},
        json={
            "entity_type": "instrument",
            "comment": "PUBLIC NOTE: Please ensure your amendment letter has the bank seal.",
            "is_internal": False,
        },
    )
    assert res_pub.status_code == status.HTTP_201_CREATED
    assert res_pub.json()["is_internal"] is False

    # 3. Bureau officer views comments: receives BOTH internal and public notes
    res_so_comments = client.get(
        f"/v1/cases/{instrument.id}/comments",
        headers={"Authorization": f"Bearer {so_token}"},
    )
    assert res_so_comments.status_code == status.HTTP_200_OK
    so_list = res_so_comments.json()
    assert len(so_list) == 2
    assert any(c["is_internal"] is True for c in so_list)
    assert any(c["is_internal"] is False for c in so_list)

    # 4. NEGATIVE SECURITY TEST: Institution views comments
    # MUST NEVER receive the internal note (CLAUDE.md & SPEC §18.1 Scenario 6)
    res_inst_comments = client.get(
        f"/v1/cases/{instrument.id}/comments",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert res_inst_comments.status_code == status.HTTP_200_OK
    inst_list = res_inst_comments.json()
    assert len(inst_list) == 1
    assert inst_list[0]["is_internal"] is False
    assert "INTERNAL NOTE" not in inst_list[0]["comment"]
    assert "PUBLIC NOTE" in inst_list[0]["comment"]

    # 5. NEGATIVE SECURITY TEST: Institution user CANNOT create an internal note
    res_forged_internal = client.post(
        f"/v1/cases/{instrument.id}/comments",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "entity_type": "instrument",
            "comment": "Forged attempt to create internal note",
            "is_internal": True,
        },
    )
    assert res_forged_internal.status_code == status.HTTP_403_FORBIDDEN
