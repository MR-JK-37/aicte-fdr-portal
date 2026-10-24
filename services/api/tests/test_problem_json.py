from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.correlation import CorrelationIdMiddleware
from app.problem_json import (
    ConflictError,
    ForbiddenError,
    IntegrationUnavailableError,
    NotFoundError,
    RateLimitedError,
    UnauthenticatedError,
    UnprocessableEntityError,
    register_exception_handlers,
)


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/boom/{kind}")
    def boom(kind: str):
        mapping = {
            "401": UnauthenticatedError("no token"),
            "403": ForbiddenError("not your resource"),
            "404": NotFoundError("missing"),
            "409": ConflictError("stale"),
            "422": UnprocessableEntityError("bad field"),
            "429": RateLimitedError("slow down", retry_after=30),
            "503": IntegrationUnavailableError("not configured"),
            "500": RuntimeError("unexpected"),
        }
        raise mapping[kind]

    register_exception_handlers(app)
    # Added first so IdempotencyMiddleware (if present) would be inner;
    # here there's only CorrelationIdMiddleware, which must still be
    # outermost to set request.state.correlation_id before the handler
    # fires below it.
    app.add_middleware(CorrelationIdMiddleware)
    return app


client = TestClient(_build_app(), raise_server_exceptions=False)


def test_problem_json_content_type_and_fields():
    resp = client.get("/boom/404")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["code"] == "not_found"
    assert body["title"] == "Not found"
    assert body["detail"] == "missing"
    assert body["correlation_id"]  # set by CorrelationIdMiddleware


def test_problem_json_retry_after_on_429():
    resp = client.get("/boom/429")
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "30"
    assert resp.json()["retry_after"] == 30


def test_problem_json_500_never_leaks_detail():
    resp = client.get("/boom/500")
    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] is None
    assert body["code"] == "internal_error"


def test_problem_json_correlation_id_echoed_from_request_header():
    resp = client.get("/boom/404", headers={"X-Correlation-ID": "test-corr-id"})
    assert resp.headers["X-Correlation-ID"] == "test-corr-id"
    assert resp.json()["correlation_id"] == "test-corr-id"


def test_status_codes_match_each_family():
    for kind, expected in [
        ("401", 401),
        ("403", 403),
        ("409", 409),
        ("422", 422),
        ("503", 503),
    ]:
        resp = client.get(f"/boom/{kind}")
        assert resp.status_code == expected
