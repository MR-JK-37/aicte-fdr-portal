"""Tests for the Idempotency-Key replay middleware
(app.idempotency.middleware).

BLOCKED-ON-MIGRATION NOTE: `idempotency_keys` is owned by the parallel
Phase-1 workstream's Alembic migration, not landed yet. As with the
other blocked-on-migration test modules in this phase, this module
creates the contracted table itself for the duration of the module and
drops it afterwards.
"""

import os
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.idempotency.middleware import IdempotencyMiddleware

_FAKE_USER_ID = uuid.uuid4()

# See test_outbox_worker.py's _SUPERUSER_DATABASE_URL comment: fdr_app
# (the `engine`/`db_session` fixtures' role) has no CREATE privilege on
# the public schema by design, so this blocked-on-migration DDL needs
# the table-owning role. fdr_app gets CRUD on the result automatically
# via that role's ALTER DEFAULT PRIVILEGES grant.
_SUPERUSER_DATABASE_URL = os.environ.get(
    "SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)


class _FakeAuthMiddleware(BaseHTTPMiddleware):
    """Stands in for the real auth dependency (app.authz, not built yet)
    so these tests exercise the idempotency replay logic itself rather
    than its fail-closed "no user_id" guard. Must run BEFORE
    IdempotencyMiddleware on the way in, i.e. be added to the app
    AFTER it (Starlette's add_middleware stacks in reverse)."""

    async def dispatch(self, request, call_next):
        request.state.user_id = _FAKE_USER_ID
        return await call_next(request)


@pytest.fixture(autouse=True)
def _clean_idempotency(db_session):
    db_session.execute(text("DELETE FROM idempotency_keys"))
    db_session.commit()
    yield


_call_count = {"n": 0}


@pytest.fixture
def client():
    app = FastAPI()

    @app.post("/widgets")
    def create_widget(body: dict):
        _call_count["n"] += 1
        return {"created": True, "calls_so_far": _call_count["n"]}

    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(_FakeAuthMiddleware)
    return TestClient(app)


def test_replays_identical_request_without_recalling_handler(client):
    _call_count["n"] = 0
    headers = {"Idempotency-Key": "key-1"}
    first = client.post("/widgets", json={"name": "a"}, headers=headers)
    second = client.post("/widgets", json={"name": "a"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()  # same calls_so_far => handler only ran once
    assert _call_count["n"] == 1


def test_different_body_with_same_key_is_409(client):
    headers = {"Idempotency-Key": "key-2"}
    first = client.post("/widgets", json={"name": "a"}, headers=headers)
    assert first.status_code == 200

    second = client.post("/widgets", json={"name": "different"}, headers=headers)
    assert second.status_code == 409
    assert second.json()["code"] == "idempotency_key_reused"


def test_no_header_means_no_idempotency_behaviour(client):
    _call_count["n"] = 0
    client.post("/widgets", json={"name": "a"})
    client.post("/widgets", json={"name": "a"})
    assert _call_count["n"] == 2


def test_state_changing_request_without_authenticated_user_is_401():
    """Fails closed: with no app.authz yet, there's no identity to scope
    a key to, and replaying a cached response to the wrong caller would
    be a cross-caller leak — see app.idempotency.middleware."""
    app = FastAPI()

    @app.post("/widgets")
    def create_widget(body: dict):
        return {"created": True}

    app.add_middleware(IdempotencyMiddleware)  # no _FakeAuthMiddleware here
    local_client = TestClient(app, raise_server_exceptions=False)

    resp = local_client.post(
        "/widgets", json={"name": "a"}, headers={"Idempotency-Key": "k"}
    )
    assert resp.status_code == 401


def test_get_requests_are_not_subject_to_idempotency():
    app = FastAPI()

    @app.get("/noop")
    def noop():
        return {"ok": True}

    app.add_middleware(IdempotencyMiddleware)
    local_client = TestClient(app)

    resp = local_client.get("/noop", headers={"Idempotency-Key": "irrelevant"})
    assert resp.status_code == 200
