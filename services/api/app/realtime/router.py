"""Server-Sent Events (SSE) streaming router (MASTER_PROMPT §10.8)."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.authz import Principal
from app.db import SessionLocal, set_app_context
from app.models.workflow import SSEEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["realtime"])


def is_event_authorized_for_principal(event: SSEEvent, principal: Principal) -> bool:
    """Per-event re-authorisation before emission (MASTER_PROMPT §10.8).

    Verifies that the principal still possesses the authority/scope to see this event.
    """
    # 1. Operators and bureau admins have broad operational visibility
    role_val = (
        principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role)
    )
    if role_val in ("platform_operator", "bureau_admin"):
        return True

    # 2. Direct user event
    if event.recipient_user_id and event.recipient_user_id == principal.id:
        return True

    # 3. Institution event
    if (
        event.institution_id
        and principal.institution_id
        and event.institution_id == principal.institution_id
    ):
        return True

    # 4. Role-based event
    if event.role and event.role == role_val:
        return True

    # 5. Broadcast / maintenance events (no recipient or institution specified)
    return bool(
        not event.recipient_user_id and not event.institution_id and not event.role
    )


async def sse_generator(
    request: Request,
    principal: Principal,
    last_event_id_val: int = 0,
) -> AsyncGenerator[str, None]:
    """Generates SSE stream with Last-Event-ID catch-up replay and live heartbeat."""
    current_seq = last_event_id_val
    role_val = principal.role.value if hasattr(principal.role, "value") else str(principal.role)
    inst_val = str(principal.institution_id) if principal.institution_id else None
    user_val = str(principal.id)

    # 1. Catch-up phase: replay buffered events from sse_events table
    db: Session = SessionLocal()
    try:
        set_app_context(db, role=role_val, institution_id=inst_val, user_id=user_val)
        if current_seq > 0:
            buffered_events = (
                db.execute(
                    select(SSEEvent)
                    .where(SSEEvent.sequence_id > current_seq)
                    .order_by(SSEEvent.sequence_id.asc())
                    .limit(100)
                )
                .scalars()
                .all()
            )
            for evt in buffered_events:
                if is_event_authorized_for_principal(evt, principal):
                    payload_json = json.dumps(evt.payload)
                    yield f"id: {evt.sequence_id}\nevent: {evt.event_type}\ndata: {payload_json}\n\n"
                current_seq = max(current_seq, evt.sequence_id)
    finally:
        db.close()

    # 2. Live streaming & heartbeat loop
    heartbeat_interval = 15  # seconds per MASTER_PROMPT §10.8
    try:
        while True:
            if request is not None and await request.is_disconnected():
                break

            # Poll for new events in sse_events beyond current_seq
            db = SessionLocal()
            try:
                set_app_context(db, role=role_val, institution_id=inst_val, user_id=user_val)
                new_events = (
                    db.execute(
                        select(SSEEvent)
                        .where(SSEEvent.sequence_id > current_seq)
                        .order_by(SSEEvent.sequence_id.asc())
                        .limit(20)
                    )
                    .scalars()
                    .all()
                )
                for evt in new_events:
                    if is_event_authorized_for_principal(evt, principal):
                        payload_json = json.dumps(evt.payload)
                        yield f"id: {evt.sequence_id}\nevent: {evt.event_type}\ndata: {payload_json}\n\n"
                    current_seq = max(current_seq, evt.sequence_id)
            finally:
                db.close()

            # Heartbeat comment to keep connection alive
            yield ": keep-alive\n\n"
            await asyncio.sleep(heartbeat_interval)
    except asyncio.CancelledError:
        logger.info("SSE client disconnected: %s", principal.id)


@router.get("/stream")
async def event_stream(
    request: Request,
    last_event_id_header: str | None = Header(None, alias="Last-Event-ID"),
    last_event_id_query: int | None = Query(None, alias="last_event_id"),
    principal: Principal = Depends(get_current_principal),
):
    """Server-Sent Events endpoint with Last-Event-ID replay and per-event re-authorization."""
    last_id = 0
    if last_event_id_header and last_event_id_header.isdigit():
        last_id = int(last_event_id_header)
    elif last_event_id_query is not None:
        last_id = last_event_id_query

    return StreamingResponse(
        sse_generator(request, principal, last_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
