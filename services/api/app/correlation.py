"""Correlation ID middleware (MASTER_PROMPT §15.1/§16): every request
gets a correlation ID — taken from the inbound `X-Correlation-ID`
header if the caller supplied one, generated otherwise — set on
`request.state.correlation_id` for route handlers/audit/logging/
problem+json error bodies to read, and echoed back on the response
header so logs on both sides can be joined.

Wiring (do in app/main.py — see this phase's report):
    from app.correlation import CorrelationIdMiddleware
    app.add_middleware(CorrelationIdMiddleware)
Add this LAST, after `app.add_middleware(IdempotencyMiddleware)` and
after `register_exception_handlers`. Starlette's `add_middleware` stacks
in reverse — the last one added becomes the *outermost* middleware, so
it runs first on the way in. Adding this one last makes it outermost,
so `request.state.correlation_id` is already set before
IdempotencyMiddleware, the route, or any exception handler runs —
everything downstream depends on reading that value.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
