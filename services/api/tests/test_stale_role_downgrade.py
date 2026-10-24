import uuid

from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.db import set_app_context
from app.main import app
from app.models.core import AppUser
from app.models.enums import AppRole


def test_stale_role_downgrade_takes_immediate_effect(db_session):
    """MASTER_PROMPT §9 F-01: An open session cannot keep stale access when downgraded.

    1. User is assigned COMPETENT_AUTHORITY role.
    2. Token is minted with that role.
    3. User's role is downgraded in app_users to INSTITUTION_VIEWER.
    4. Client makes request presenting the older token.
    5. get_current_principal resolves fresh state from DB: permissions are immediately downgraded!
    """
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Setup user with privileged bureau role
    set_app_context(db_session, role="platform_operator")
    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"approver_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Approver User",
        role=AppRole.COMPETENT_AUTHORITY,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # 2. Mint token while role was COMPETENT_AUTHORITY
    token = create_access_token(user)
    headers = {"Authorization": f"Bearer {token}"}

    # Initial check: /v1/me/permissions shows approve_release
    resp1 = client.get("/v1/me/permissions", headers=headers)
    assert resp1.status_code == 200
    assert "approve_release" in resp1.json()["permissions"]

    # 3. Identity Admin downgrades user to INSTITUTION_VIEWER in the DB
    set_app_context(db_session, role="identity_admin")
    user.role = AppRole.INSTITUTION_VIEWER
    db_session.commit()

    # 4. Next request using the SAME existing token
    resp2 = client.get("/v1/me/permissions", headers=headers)
    assert resp2.status_code == 200
    perms2 = resp2.json()["permissions"]

    # Immediate revocation of privileged verb: approve_release must NOT be present!
    assert "approve_release" not in perms2
    assert perms2 == ["download_evidence", "view"]


def test_immediate_session_revocation_on_user_deactivation(db_session):
    """When a user is deactivated in the DB, their active token is immediately rejected with 401."""
    client = TestClient(app, raise_server_exceptions=False)

    set_app_context(db_session, role="platform_operator")
    user = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4()}",
        email=f"deact_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Deactivated User",
        role=AppRole.INTAKE_OFFICER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user)
    headers = {"Authorization": f"Bearer {token}"}

    resp1 = client.get("/v1/me", headers=headers)
    assert resp1.status_code == 200

    # Deactivate user
    set_app_context(db_session, role="identity_admin")
    user.is_active = False
    db_session.commit()

    # Next request must be rejected
    resp2 = client.get("/v1/me", headers=headers)
    assert resp2.status_code == 401
    assert resp2.headers["content-type"] == "application/problem+json"
