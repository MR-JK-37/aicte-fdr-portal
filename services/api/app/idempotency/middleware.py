"""Idempotency-Key middleware (MASTER_PROMPT §15.1/§16): a state-changing
request carrying an `Idempotency-Key` header is replayed from the stored
response instead of reprocessed, if a prior request with the same key
and an identical body already completed; a replayed key with a
*different* body is a 409 Conflict, never a silent reprocess.

Table contract (owned by the parallel Phase-1 workstream's migration,
not landed yet — see this phase's task brief):

    idempotency_keys: key text PK, user_id UUID, method text, path
    text, request_hash text, response_status int NULL, response_body
    JSONB NULL, created_at timestamptz, expires_at timestamptz

This module's queries will start working the moment that migration
lands; nothing else here needs to change EXCEPT: flag to the migration
owner that `key text PK` alone allows two different users' rows to
collide if they ever pick the same literal key string (an INSERT
IntegrityError, not a leak, now that lookups are scoped by (key,
user_id) below — but still worth a composite PK (user_id, key) in a
follow-up migration).

Wiring (do in app/main.py — see this phase's report for exact order):
    from app.idempotency.middleware import IdempotencyMiddleware
    app.add_middleware(IdempotencyMiddleware)
Register this BEFORE `app.add_middleware(CorrelationIdMiddleware)` in
source order. Starlette's `add_middleware` stacks in reverse (the last
one added becomes the outermost, and runs first), so to get the actual
request path [correlation] -> [idempotency] -> [route] — i.e.
`request.state.correlation_id` already set before this middleware's
`dispatch` reads it — add IdempotencyMiddleware first and
CorrelationIdMiddleware second (last).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db import SessionLocal
from app.idempotency.models import IdempotencyKey
from app.problem_json import UnauthenticatedError, build_problem_response

STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
DEFAULT_TTL = timedelta(hours=24)
# Idempotency-Key replay must never cache a 5xx — a transient failure
# should be retried for real, not frozen into a permanent error reply.
_CACHEABLE_MAX_STATUS = 499


def _hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
        if key is None or request.method not in STATE_CHANGING_METHODS:
            return await call_next(request)

        body = await request.body()
        request_hash = _hash_body(body)
        correlation_id = getattr(request.state, "correlation_id", None)
        # TODO: wire to the real authenticated user once app.authz lands
        # (owned by the parallel role/RLS workstream). Until then this
        # middleware must NOT be enabled in main.py (see module docstring)
        # — there is no authenticated identity to scope a key to yet, and
        # serving a replay to an unauthenticated/nil-UUID caller is a
        # cross-caller information leak (one caller could read another's
        # cached response by reusing their Idempotency-Key value).
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            # Built directly rather than raised: this middleware runs
            # outside FastAPI's exception-handler stack (those only
            # catch exceptions from routing/endpoints, not from another
            # middleware's own dispatch), so raising UnauthenticatedError
            # here would surface as a generic 500, not this 401.
            err = UnauthenticatedError(
                "Idempotency-Key handling requires an authenticated user_id; "
                "none is present on request.state yet (authorise() pending)"
            )
            return build_problem_response(
                status_code=err.status_code,
                code=err.code,
                title=err.title,
                detail=err.detail,
                correlation_id=correlation_id,
            )

        session = SessionLocal()
        try:
            session.execute(text("SELECT set_config('app.role', 'bureau_admin', true)"))
            now = datetime.now(UTC)
            existing = session.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.key == key,
                    IdempotencyKey.user_id == user_id,
                )
            ).scalar_one_or_none()

            if existing is not None and existing.expires_at > now:
                if existing.request_hash != request_hash:
                    return build_problem_response(
                        status_code=409,
                        code="idempotency_key_reused",
                        title="Idempotency-Key reused with a different request",
                        detail=(
                            "this Idempotency-Key was already used for a request with a "
                            "different body; use a new key for a new request"
                        ),
                        correlation_id=correlation_id,
                    )
                # Exact replay of a previously completed request.
                return Response(
                    content=_dump_body(existing.response_body),
                    status_code=existing.response_status or 200,
                    media_type="application/json",
                )

            response = await call_next(request)

            if response.status_code <= _CACHEABLE_MAX_STATUS:
                response_body = b"".join(
                    [chunk async for chunk in response.body_iterator]
                )
                _store_response(
                    session,
                    key=key,
                    user_id=user_id,
                    method=request.method,
                    path=request.url.path,
                    request_hash=request_hash,
                    status_code=response.status_code,
                    body=response_body,
                    now=now,
                )
                session.commit()
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            return response
        finally:
            session.close()


def _dump_body(response_body: dict | None) -> bytes:
    import json

    return json.dumps(response_body or {}).encode("utf-8")


def _store_response(
    session,
    *,
    key: str,
    user_id: uuid.UUID,
    method: str,
    path: str,
    request_hash: str,
    status_code: int,
    body: bytes,
    now: datetime,
) -> None:
    import json

    try:
        response_body = json.loads(body) if body else None
    except ValueError:
        response_body = None

    session.add(
        IdempotencyKey(
            key=key,
            user_id=user_id,
            method=method,
            path=path,
            request_hash=request_hash,
            response_status=status_code,
            response_body=response_body,
            created_at=now,
            expires_at=now + DEFAULT_TTL,
        )
    )
