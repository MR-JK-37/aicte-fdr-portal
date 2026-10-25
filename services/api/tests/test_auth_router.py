import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.auth.security import encrypt_totp_secret, generate_totp_secret, hash_password
from app.db import set_app_context
from app.main import app
from app.models.core import AppUser, Institution
from app.models.enums import AppRole

REAL_PASSWORD = "correct horse battery staple 9!"


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
        password_hash=hash_password(REAL_PASSWORD),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def mfa_user(db_session, test_institution):
    """A user with TOTP already enrolled, for login/step-up tests that need it."""
    set_app_context(db_session, role="platform_operator")
    secret = generate_totp_secret()
    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"officer_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Test Officer",
        role=AppRole.SCRUTINY_OFFICER,
        institution_id=None,
        is_active=True,
        mfa_enrolled=True,
        password_hash=hash_password(REAL_PASSWORD),
        totp_secret_encrypted=encrypt_totp_secret(secret),
    )
    db_session.add(user)
    db_session.commit()
    return user, secret


def _totp_code(secret: str) -> str:
    import pyotp

    return pyotp.TOTP(secret).now()


def test_login_success_with_correct_password(auth_client, test_user):
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": REAL_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email
    assert data["user"]["role"] == AppRole.INSTITUTION_SUBMITTER.value
    assert "fdr_session" in resp.cookies


def test_login_rejects_wrong_password(auth_client, test_user):
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": "definitely-not-the-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "unauthenticated"


def test_login_rejects_any_password_when_none_set(auth_client, db_session, test_institution):
    """A user with no password_hash (e.g. created directly, never through a real
    signup) must never be logged into by "any" password — this is the exact bypass
    this stream closes."""
    set_app_context(db_session, role="platform_operator")
    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"nopass_{uuid.uuid4().hex[:6]}@example.com",
        full_name="No Password User",
        role=AppRole.INSTITUTION_VIEWER,
        institution_id=test_institution.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": user.email, "password": "anything-at-all"},
    )
    assert resp.status_code == 401


def test_login_locks_account_after_max_attempts(auth_client, db_session, test_user):
    from app.config import settings

    for _ in range(settings.max_login_attempts):
        resp = auth_client.post(
            "/v1/auth/login",
            json={"email": test_user.email, "password": "wrong"},
        )
        assert resp.status_code == 401

    # One more attempt, even with the CORRECT password, is now locked out.
    locked_resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": REAL_PASSWORD},
    )
    assert locked_resp.status_code == 403


def test_login_with_mfa_enrolled_requires_totp(auth_client, mfa_user):
    user, secret = mfa_user

    # Correct password, no TOTP code -> rejected.
    resp = auth_client.post(
        "/v1/auth/login", json={"email": user.email, "password": REAL_PASSWORD}
    )
    assert resp.status_code == 401

    # Correct password, wrong TOTP code -> rejected.
    resp2 = auth_client.post(
        "/v1/auth/login",
        json={"email": user.email, "password": REAL_PASSWORD, "totp_code": "000000"},
    )
    assert resp2.status_code == 401

    # Correct password, correct TOTP code -> accepted.
    resp3 = auth_client.post(
        "/v1/auth/login",
        json={
            "email": user.email,
            "password": REAL_PASSWORD,
            "totp_code": _totp_code(secret),
        },
    )
    assert resp3.status_code == 200


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
        json={"email": test_user.email, "password": REAL_PASSWORD},
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

    perm_resp = auth_client.get("/v1/me/permissions", headers=headers)
    assert perm_resp.status_code == 200
    perms = perm_resp.json()
    assert perms["role"] == AppRole.INSTITUTION_SUBMITTER.value
    assert "submit" in perms["permissions"]
    assert "view" in perms["permissions"]


def test_mfa_enrolment_flow(auth_client, test_user):
    token = create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}

    start_resp = auth_client.post("/v1/auth/mfa/enrol/start", headers=headers)
    assert start_resp.status_code == 200
    secret = start_resp.json()["secret"]
    assert start_resp.json()["provisioning_uri"].startswith("otpauth://")

    # Wrong code rejected; nothing persisted.
    bad_confirm = auth_client.post(
        "/v1/auth/mfa/enrol/confirm",
        headers=headers,
        json={"secret": secret, "totp_code": "000000"},
    )
    assert bad_confirm.status_code == 403

    confirm_resp = auth_client.post(
        "/v1/auth/mfa/enrol/confirm",
        headers=headers,
        json={"secret": secret, "totp_code": _totp_code(secret)},
    )
    assert confirm_resp.status_code == 200
    body = confirm_resp.json()
    assert body["success"] is True
    assert len(body["recovery_codes"]) == 10


def test_step_up_requires_real_totp_not_any_six_digits(auth_client, mfa_user):
    user, secret = mfa_user
    token = create_access_token(user)
    headers = {"Authorization": f"Bearer {token}"}

    resp1 = auth_client.get("/v1/me", headers=headers)
    assert resp1.json()["step_up_valid"] is False

    # The old bypass: any syntactically-valid 6-digit code used to succeed. Now it
    # must fail unless it's the real current TOTP code.
    wrong_resp = auth_client.post(
        "/v1/auth/step-up", headers=headers, json={"otp_code": "123456"}
    )
    assert wrong_resp.status_code == 403

    right_resp = auth_client.post(
        "/v1/auth/step-up", headers=headers, json={"otp_code": _totp_code(secret)}
    )
    assert right_resp.status_code == 200
    assert right_resp.json()["success"] is True

    resp2 = auth_client.get("/v1/me", headers=headers)
    assert resp2.json()["step_up_valid"] is True


def test_step_up_without_mfa_enrolled_is_rejected(auth_client, test_user):
    token = create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    resp = auth_client.post(
        "/v1/auth/step-up", headers=headers, json={"otp_code": "123456"}
    )
    assert resp.status_code == 403


def test_logout(auth_client, test_user):
    login_resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": REAL_PASSWORD},
    )
    assert login_resp.status_code == 200

    logout_resp = auth_client.post("/v1/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.cookies.get("fdr_session") is None


def test_login_issues_refresh_token_and_refresh_rotates_it(auth_client, test_user):
    login_resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": REAL_PASSWORD},
    )
    assert login_resp.status_code == 200
    first_refresh = login_resp.json()["refresh_token"]
    assert first_refresh

    refresh_resp = auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": first_refresh}
    )
    assert refresh_resp.status_code == 200
    second_refresh = refresh_resp.json()["refresh_token"]
    assert second_refresh != first_refresh


def test_refresh_rejects_reused_rotated_out_token(auth_client, test_user):
    login_resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": REAL_PASSWORD},
    )
    first_refresh = login_resp.json()["refresh_token"]

    # Rotate once — first_refresh is now "previous", no longer current.
    rotate_resp = auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": first_refresh}
    )
    assert rotate_resp.status_code == 200
    second_refresh = rotate_resp.json()["refresh_token"]

    # Replaying the already-rotated-out token is a reuse/theft signal.
    reuse_resp = auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": first_refresh}
    )
    assert reuse_resp.status_code == 401

    # The session is now revoked entirely — even the valid rotated token
    # (second_refresh) must stop working.
    after_reuse_resp = auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": second_refresh}
    )
    assert after_reuse_resp.status_code == 401


def test_refresh_rejects_garbage_token(auth_client):
    resp = auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
    )
    assert resp.status_code == 401


def test_session_list_shows_current_and_revoke_removes_it(auth_client, test_user):
    login_resp = auth_client.post(
        "/v1/auth/login",
        json={"email": test_user.email, "password": REAL_PASSWORD, "device_label": "Test Device"},
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    list_resp = auth_client.get("/v1/auth/sessions", headers=headers)
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert len(sessions) == 1
    assert sessions[0]["device_label"] == "Test Device"
    assert sessions[0]["current"] is True

    session_id = sessions[0]["session_id"]
    revoke_resp = auth_client.delete(f"/v1/auth/sessions/{session_id}", headers=headers)
    assert revoke_resp.status_code == 200

    list_after = auth_client.get("/v1/auth/sessions", headers=headers)
    assert list_after.status_code == 200
    assert list_after.json() == []


def test_session_revoke_cross_user_returns_404(auth_client, db_session, test_institution):
    """Revoking someone else's session id must 404, not 403 — SPEC §4.2: cross-tenant
    ids are never distinguishable from nonexistent ones."""
    set_app_context(db_session, role="platform_operator")
    other_user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"other_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Other User",
        role=AppRole.INSTITUTION_VIEWER,
        institution_id=test_institution.id,
        is_active=True,
        password_hash=hash_password(REAL_PASSWORD),
    )
    db_session.add(other_user)
    db_session.commit()

    other_login = auth_client.post(
        "/v1/auth/login",
        json={"email": other_user.email, "password": REAL_PASSWORD},
    )
    other_session_id = (
        auth_client.get(
            "/v1/auth/sessions",
            headers={"Authorization": f"Bearer {other_login.json()['access_token']}"},
        )
        .json()[0]["session_id"]
    )

    # A different user tries to revoke it.
    user2 = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"viewer_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Viewer",
        role=AppRole.INSTITUTION_VIEWER,
        institution_id=test_institution.id,
        is_active=True,
        password_hash=hash_password(REAL_PASSWORD),
    )
    db_session.add(user2)
    db_session.commit()
    token2 = create_access_token(user2)

    resp = auth_client.delete(
        f"/v1/auth/sessions/{other_session_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == 404


def test_logout_all_revokes_every_session(auth_client, test_user):
    login1 = auth_client.post(
        "/v1/auth/login", json={"email": test_user.email, "password": REAL_PASSWORD}
    )
    login2 = auth_client.post(
        "/v1/auth/login", json={"email": test_user.email, "password": REAL_PASSWORD}
    )
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    logout_all_resp = auth_client.post("/v1/auth/logout-all", headers=headers2)
    assert logout_all_resp.status_code == 200

    sessions_after = auth_client.get("/v1/auth/sessions", headers=headers2)
    # The access token itself is still valid (stateless JWT, not yet expired) but no
    # sessions remain listed, and the refresh tokens from both logins are now dead.
    assert sessions_after.json() == []

    refresh_resp = auth_client.post(
        "/v1/auth/refresh", json={"refresh_token": login1.json()["refresh_token"]}
    )
    assert refresh_resp.status_code == 401


def test_navigation_is_role_specific(auth_client, test_user, mfa_user):
    submitter_token = create_access_token(test_user)
    resp = auth_client.get(
        "/v1/me/navigation", headers={"Authorization": f"Bearer {submitter_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["landing_route"] == "/home"
    sidebar_keys = {i["key"] for i in body["web_sidebar"]}
    assert "deposits" in sidebar_keys
    assert "users" not in sidebar_keys  # org_admin-only, not submitter

    officer_user, _secret = mfa_user
    officer_token = create_access_token(officer_user)
    resp2 = auth_client.get(
        "/v1/me/navigation", headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert resp2.status_code == 200
    officer_body = resp2.json()
    assert officer_body["landing_route"] == "/my-queue"
    assert officer_body != body  # different role, genuinely different manifest


def test_navigation_requires_auth(auth_client):
    resp = auth_client.get("/v1/me/navigation")
    assert resp.status_code == 401


def test_profile_completion_reflects_real_fields(auth_client, test_user):
    token = create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}

    resp = auth_client.get("/v1/me/profile-completion", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    items = {i["key"]: i for i in body["items"]}
    assert items["name"]["complete"] is True  # full_name set at fixture creation
    assert items["designation"]["complete"] is False  # never set
    assert items["verified_mobile"]["complete"] is False  # no SMS provider exists
    assert items["mfa_enrolled"]["complete"] is False  # test_user has no TOTP
    assert items["passkey"]["optional"] is True
    assert items["passkey"]["complete"] is False
    # percent only counts required items, and passkey never inflates it
    required_complete = sum(1 for i in body["items"] if i["complete"] and not i["optional"])
    required_total = sum(1 for i in body["items"] if not i["optional"])
    assert body["percent"] == round(100 * required_complete / required_total)

    # Fill in the fields PATCH /me/profile can actually set, then re-check.
    patch_resp = auth_client.patch(
        "/v1/me/profile",
        headers=headers,
        json={"designation": "Finance Officer", "mobile_number": "+919876543210"},
    )
    assert patch_resp.status_code == 200

    resp2 = auth_client.get("/v1/me/profile-completion", headers=headers)
    items2 = {i["key"]: i for i in resp2.json()["items"]}
    assert items2["designation"]["complete"] is True
    # Setting a mobile number does NOT verify it — no real SMS/OTP flow exists.
    assert items2["verified_mobile"]["complete"] is False
    assert resp2.json()["percent"] > body["percent"]


def test_update_profile_persists_and_is_self_scoped(auth_client, test_user):
    token = create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}

    resp = auth_client.patch(
        "/v1/me/profile", headers=headers, json={"full_name": "Renamed Person"}
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Renamed Person"

    me_resp = auth_client.get("/v1/me", headers=headers)
    assert me_resp.json()["full_name"] == "Renamed Person"
