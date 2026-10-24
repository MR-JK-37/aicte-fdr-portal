"""Tests for the feature/connector registry admin API
(app.registry.router).

BLOCKED-ON-MIGRATION NOTE: `feature_registry`/`connector_health_checks`
are owned by the parallel Phase-1 workstream's Alembic migration, not
landed yet. As with test_outbox_worker.py, this module creates the
contracted tables itself for the duration of the module and drops them
afterwards — delete `_ensure_registry_tables` once the real migration
lands.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import get_db
from app.problem_json import register_exception_handlers
from app.registry.models import FeatureRegistryEntry
from app.registry.router import _require_configure_integrations, router

# See test_outbox_worker.py's _SUPERUSER_DATABASE_URL comment: fdr_app
# (the `engine`/`db_session` fixtures' role) has no CREATE privilege on
# the public schema by design, so this blocked-on-migration DDL needs
# the table-owning role. fdr_app gets CRUD on the result automatically
# via that role's ALTER DEFAULT PRIVILEGES grant.
_SUPERUSER_DATABASE_URL = os.environ.get(
    "SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)


@pytest.fixture(autouse=True)
def _clean_registry(db_session):
    db_session.execute(text("DELETE FROM feature_registry"))
    db_session.commit()
    yield


@pytest.fixture
def client(db_session, engine):
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    # The real dependency fails closed (403) until app.authz lands (see
    # app.registry.router) — overridden here so these tests exercise
    # the registry business logic itself, not the placeholder auth gate.
    app.dependency_overrides[_require_configure_integrations] = lambda: None
    return TestClient(app, raise_server_exceptions=False)


def test_placeholder_auth_fails_closed_when_not_overridden(db_session):
    """Separate from the `client` fixture (which overrides the auth
    placeholder to test business logic) — this confirms the real,
    un-overridden dependency denies every caller by default."""
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    raw_client = TestClient(app, raise_server_exceptions=False)

    resp = raw_client.get("/v1/admin/registry")
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


def test_list_and_get_feature(db_session, client):
    db_session.add(
        FeatureRegistryEntry(
            id=uuid.uuid4(),
            key="android_push",
            state="disabled",
            description="FCM HTTP v1",
            updated_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    listed = client.get("/v1/admin/registry")
    assert listed.status_code == 200
    assert any(row["key"] == "android_push" for row in listed.json())

    got = client.get("/v1/admin/registry/android_push")
    assert got.status_code == 200
    assert got.json()["state"] == "disabled"


def test_get_unknown_key_is_404_problem_json(client):
    resp = client.get("/v1/admin/registry/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


def test_patch_to_production_enabled_without_evidence_is_422(db_session, client):
    db_session.add(
        FeatureRegistryEntry(
            id=uuid.uuid4(),
            key="web_push",
            state="sandbox-only",
            description="VAPID web push",
            acceptance_evidence_ref=None,
            updated_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    resp = client.patch(
        "/v1/admin/registry/web_push", json={"state": "production-enabled"}
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "unprocessable_entity"


def test_patch_to_production_enabled_with_evidence_succeeds(db_session, client):
    db_session.add(
        FeatureRegistryEntry(
            id=uuid.uuid4(),
            key="statement_import",
            state="sandbox-only",
            description="MT940/CAMT.053/CSV/XLSX import",
            acceptance_evidence_ref="docs/evidence/statement-import-UAT.pdf",
            updated_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    resp = client.patch(
        "/v1/admin/registry/statement_import", json={"state": "production-enabled"}
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "production-enabled"
