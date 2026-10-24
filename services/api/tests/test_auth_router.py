import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.db import set_app_context
from app.main import app
from app.models.core import AppUser, Institution
from app.models.enums import AppRole


@pytest.fixture
def auth_client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def test_institution(db_session):
    set_app_context(db_session, role="platform_operator")
    inst = Institution(
        aicte_code=f"1-AUTH-{uuid.uuid4().hex[:6]}", name="Auth Test Institute"
    )
    db_session.add(inst)
    db_session.commit()
    return inst


@pytest.fixture
def test_user(db_session, test_institution):
    set_app_context(db_session, role="platform_operator")
    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"submitter_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Test Submitter",
        role=AppRole.INSTITUTION_SUBMITTER,
        institution_id=test_institution.id,
        is_active=True,
        mfa_enrolled=False,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_login_success(auth_client, test_user):
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": "any_password_for_dev"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email
    assert data["user"]["role"] == AppRole.INSTITUTION_SUBMITTER.value
    assert "fdr_session" in resp.cookies


def test_login_invalid_email(auth_client):
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": "nonexistent_user_999@example.com", "password": "password"},
    )
    assert resp.status_code == 401
    assert resp.headers["content-type"] == "application/problem+json"
    data = resp.json()
    assert data["code"] == "unauthenticated"


def test_login_deactivated_user(auth_client, db_session, test_user):
    set_app_context(db_session, role="platform_operator")
    test_user.is_active = False
    db_session.commit()

    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": "any_password"},
    )
    assert resp.status_code == 403
    assert resp.headers["content-type"] == "application/problem+json"


def test_get_me_and_permissions(auth_client, test_user):
    token = create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}

    resp = auth_client.get("/v1/me", headers=headers)
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["email"] == test_user.email
    assert profile["role"] == AppRole.INSTITUTION_SUBMITTER.value

    # Check permissions
    perm_resp = auth_client.get("/v1/me/permissions", headers=headers)
    assert perm_resp.status_code == 200
    perms = perm_resp.json()
    assert perms["role"] == AppRole.INSTITUTION_SUBMITTER.value
    assert "submit" in perms["permissions"]
    assert "view" in perms["permissions"]


def test_step_up_mfa_flow(auth_client, test_user):
    token = create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initial me has step_up_valid = False
    resp1 = auth_client.get("/v1/me", headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["step_up_valid"] is False

    # Perform step-up
    step_resp = auth_client.post(
        "/v1/auth/step-up",
        headers=headers,
        json={"otp_code": "123456"},
    )
    assert step_resp.status_code == 200
    assert step_resp.json()["success"] is True

    # Check me again, now step_up_valid should be True
    resp2 = auth_client.get("/v1/me", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["step_up_valid"] is True


def test_logout(auth_client, test_user):
    login_resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": "password"},
    )
    assert login_resp.status_code == 200

    logout_resp = auth_client.post("/v1/auth/logout")
    assert logout_resp.status_code == 200
    # Cookie should be cleared / expired
    assert logout_resp.cookies.get("fdr_session") is None
