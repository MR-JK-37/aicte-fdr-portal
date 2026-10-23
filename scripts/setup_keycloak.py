"""Provisions the Keycloak realm for the FDR portal: idempotent — safe to
re-run. Self-hosted Keycloak, authenticated with the bootstrap admin
credentials set via KC_BOOTSTRAP_ADMIN_USERNAME/PASSWORD in Docker Compose.
No external account or login is needed for this step.

Usage:
    uv run --project services/api python ../../scripts/setup_keycloak.py
or, from the repo root with the api venv active:
    python scripts/setup_keycloak.py

Env vars: KEYCLOAK_URL (default http://localhost:8080),
KEYCLOAK_ADMIN_USER / KEYCLOAK_ADMIN_PASSWORD (default admin/admin).
"""

import os
import sys

import httpx

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
ADMIN_USER = os.environ.get("KEYCLOAK_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin")
REALM = "fdr-portal"

# Mirrors app.models.enums.AppRole / BUREAU_SIDE_ROLES.
ALL_ROLES = [
    "institution",
    "scrutiny_officer",
    "verifier",
    "regional_officer",
    "competent_authority",
    "bureau_admin",
    "bank_user",
    "auditor",
]
# "Officers" per the brief ("mandatory TOTP for officers") = bureau-side
# roles with cross-institution visibility under RLS. Institutions and bank
# users are external parties and are not mandated TOTP here.
OFFICER_ROLES = [
    "scrutiny_officer",
    "verifier",
    "regional_officer",
    "competent_authority",
    "bureau_admin",
    "auditor",
]


def get_admin_token(client: httpx.Client) -> str:
    resp = client.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD,
            "grant_type": "password",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def ensure_realm(client: httpx.Client) -> None:
    resp = client.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}")
    if resp.status_code == 200:
        print(f"realm '{REALM}' already exists")
        return
    payload = {
        "realm": REALM,
        "enabled": True,
        "registrationAllowed": False,
        "loginWithEmailAllowed": True,
        "otpPolicyType": "totp",
        "otpPolicyAlgorithm": "HmacSHA1",
        "otpPolicyDigits": 6,
        "otpPolicyPeriod": 30,
        "bruteForceProtected": True,
    }
    resp = client.post(f"{KEYCLOAK_URL}/admin/realms", json=payload)
    resp.raise_for_status()
    print(f"created realm '{REALM}'")


def ensure_roles(client: httpx.Client) -> None:
    for role in ALL_ROLES:
        resp = client.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles/{role}")
        if resp.status_code == 200:
            continue
        resp = client.post(f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles", json={"name": role})
        resp.raise_for_status()
        print(f"created role '{role}'")


def ensure_demo_user(client: httpx.Client, username: str, role: str, institution_id: str | None = None) -> None:
    """Creates one demo user per role, with CONFIGURE_TOTP forced on first
    login for officer roles — this is the "mandatory TOTP for officers"
    requirement, enforced per-user at provisioning time rather than via a
    global required action (which would also force it on institution/bank
    users, who are out of scope for that requirement)."""
    resp = client.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/users", params={"username": username, "exact": "true"})
    resp.raise_for_status()
    if resp.json():
        print(f"user '{username}' already exists")
        return

    required_actions = ["CONFIGURE_TOTP"] if role in OFFICER_ROLES else []
    attributes = {"app_role": [role]}
    if institution_id:
        attributes["institution_id"] = [institution_id]

    resp = client.post(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
        json={
            "username": username,
            "email": f"{username}@example.test",
            "enabled": True,
            "emailVerified": True,
            "requiredActions": required_actions,
            "attributes": attributes,
            "credentials": [{"type": "password", "value": "ChangeMe123!", "temporary": True}],
        },
    )
    resp.raise_for_status()
    print(f"created user '{username}' (role={role}, forced TOTP={bool(required_actions)})")

    # Fetch the new user's id and assign the realm role.
    resp = client.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/users", params={"username": username, "exact": "true"})
    user_id = resp.json()[0]["id"]
    resp = client.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles/{role}")
    role_repr = resp.json()
    resp = client.post(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/realm",
        json=[role_repr],
    )
    resp.raise_for_status()


def main() -> int:
    with httpx.Client(timeout=15.0) as client:
        token = get_admin_token(client)
        client.headers["Authorization"] = f"Bearer {token}"

        ensure_realm(client)
        ensure_roles(client)
        for role in ALL_ROLES:
            ensure_demo_user(client, f"demo-{role}", role)

    print("Keycloak provisioning complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
