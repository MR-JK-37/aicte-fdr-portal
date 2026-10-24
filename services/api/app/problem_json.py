"""application/problem+json error model (MASTER_PROMPT §16; CLAUDE.md
non-negotiable #6: cross-tenant ids return 404, never 403).

Wiring (do in app/main.py — see this phase's report):
    from app.problem_json import register_exception_handlers
    register_exception_handlers(app)
Register this AFTER `app.add_middleware(CorrelationIdMiddleware)` so
`request.state.correlation_id` is already set when a handler fires.

Error families implemented (MASTER_PROMPT §16 / SPEC §16.3):
- 401 `UnauthenticatedError`
- 403 `ForbiddenError` — same-tenant permission denial ONLY. If the
  resource belongs to a *different* tenant, raise `NotFoundError`
  instead, never this — CLAUDE.md non-negotiable #6 ("cross-tenant ids
  return 404, never 403"). Callers, not this module, are responsible
  for making that distinction at the point they know which case it is.
- 404 `NotFoundError` (also the anti-enumeration response for
  cross-tenant resource ids, per the above)
- 409 `ConflictError` — stale `If-Match`/ETag/row_version
  (app.concurrency), or an Idempotency-Key reused with a different body
  (app.idempotency.middleware, which builds its own 409 response
  directly via `build_problem_response` rather than raising, since it
  runs as middleware outside the exception-handler stack).
- 422 `UnprocessableEntityError` (and FastAPI's own
  `RequestValidationError`, handled below)
- 429 `RateLimitedError`
- 503 `IntegrationUnavailableError` — a connector/provider is not
  configured or temporarily unavailable (CLAUDE.md non-negotiable #9:
  never claim success that was not observed).
- 500 any unhandled exception (detail is never included — no internals
  leaked to the client; the correlation_id is the thread to pull on
  server-side logs).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

PROBLEM_CONTENT_TYPE = "application/problem+json"


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def build_problem_response(
    *,
    status_code: int,
    code: str,
    title: str,
    detail: str | None = None,
    correlation_id: str | None = None,
    retry_after: int | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "code": code,
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": correlation_id,
    }
    if retry_after is not None:
        body["retry_after"] = retry_after
    if extra:
        body.update(extra)
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    response = JSONResponse(status_code=status_code, content=body, headers=headers)
    response.media_type = PROBLEM_CONTENT_TYPE
    response.headers["content-type"] = PROBLEM_CONTENT_TYPE
    return response


class ProblemError(Exception):
    """Base class for the named exception types below. Raise one of the
    subclasses from route/service code; `register_exception_handlers`
    turns it into the matching problem+json response."""

    status_code: int = 500
    code: str = "internal_error"
    title: str = "Internal server error"

    def __init__(self, detail: str | None = None, *, retry_after: int | None = None):
        super().__init__(detail)
        self.detail = detail
        self.retry_after = retry_after


class UnauthenticatedError(ProblemError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthenticated"
    title = "Authentication required"


class ForbiddenError(ProblemError):
    """Same-tenant permission denial ONLY. If the resource belongs to a
    different tenant, raise `NotFoundError` instead — CLAUDE.md
    non-negotiable #6 (cross-tenant ids return 404, never 403)."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    title = "Not permitted"


class NotFoundError(ProblemError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    title = "Not found"

    def __init__(
        self,
        detail_or_resource: str | None = None,
        resource_id: object | None = None,
        *,
        retry_after: int | None = None,
    ):
        if resource_id is not None:
            detail = f"{detail_or_resource} '{resource_id}' not found"
        else:
            detail = detail_or_resource
        super().__init__(detail, retry_after=retry_after)


class ConflictError(ProblemError):
    """409: stale `If-Match`/ETag/row_version (app.concurrency), or an
    Idempotency-Key reused with a different request body."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    title = "Conflict"


class UnprocessableEntityError(ProblemError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "unprocessable_entity"
    title = "Unprocessable entity"


class RateLimitedError(ProblemError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    title = "Too many requests"


class IntegrationUnavailableError(ProblemError):
    """503: a connector/provider is not configured or temporarily
    unavailable (CLAUDE.md non-negotiable #9 — never claim success you
    did not observe)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "integration_unavailable"
    title = "Integration unavailable"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem_error_handler(
        request: Request, exc: ProblemError
    ) -> JSONResponse:
        return build_problem_response(
            status_code=exc.status_code,
            code=exc.code,
            title=exc.title,
            detail=exc.detail,
            correlation_id=_correlation_id(request),
            retry_after=exc.retry_after,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return build_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="validation_error",
            title="Request validation failed",
            detail=str(exc.errors()),
            correlation_id=_correlation_id(request),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return build_problem_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            title="Internal server error",
            detail=None,  # never leak internals to the client
            correlation_id=_correlation_id(request),
        )
