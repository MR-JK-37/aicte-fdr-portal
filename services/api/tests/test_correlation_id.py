from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.correlation import CorrelationIdMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/ping")
    def ping(request_state_probe=None):
        return {"ok": True}

    app.add_middleware(CorrelationIdMiddleware)
    return app


client = TestClient(_build_app())


def test_generates_correlation_id_when_absent():
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.headers["X-Correlation-ID"]


def test_echoes_supplied_correlation_id():
    resp = client.get("/ping", headers={"X-Correlation-ID": "abc-123"})
    assert resp.headers["X-Correlation-ID"] == "abc-123"


def test_generates_distinct_ids_across_requests():
    first = client.get("/ping").headers["X-Correlation-ID"]
    second = client.get("/ping").headers["X-Correlation-ID"]
    assert first != second
