"""Pluggable handler registry for outbox event processing.

Register a handler per `event_type`; `app.outbox.worker` looks up the
handler for each claimed row's `event_type` and calls it with the
(session, row). Real handlers — notification dispatch, reminder
escalation, document-pipeline follow-ups, etc. — land in later phases
and register themselves here with `register_handler`. This module ships
two trivial example handlers only, to prove the claim -> dispatch ->
mark-processed wiring works end-to-end before any real handler exists.

A handler that raises is treated as a retryable failure by the worker
(exponential backoff + jitter, bounded attempts, then it stops being
reclaimed and is visible in the dead-letter sense via `last_error` +
`attempts` on the row itself). A handler must not swallow its own
errors if it wants the worker's retry behaviour.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.outbox.models import OutboxEvent

logger = logging.getLogger(__name__)

HandlerFn = Callable[[Session, OutboxEvent], None]

_REGISTRY: dict[str, HandlerFn] = {}


def register_handler(event_type: str, handler: HandlerFn) -> None:
    """Registers `handler` for `event_type`, overwriting any prior
    registration — last registration wins, so import order matters if a
    later phase ever re-registers the same event_type on purpose."""
    _REGISTRY[event_type] = handler


def get_handler(event_type: str) -> HandlerFn | None:
    return _REGISTRY.get(event_type)


def registered_event_types() -> list[str]:
    return sorted(_REGISTRY)


def _handle_ping(session: Session, event: OutboxEvent) -> None:
    """Trivial example handler: does nothing and never fails. Proves a
    claimed row with a registered handler reaches `processed_at` without
    a real side effect."""
    return


def _handle_log_example(session: Session, event: OutboxEvent) -> None:
    """Trivial example handler: logs the event's payload. Stands in for
    a future real handler (e.g. "resolve recipients and persist inbox
    items" per MASTER_PROMPT §10.2 step 3) — it has the same signature
    and the same claim/retry guarantees a real handler gets."""
    logger.info(
        "outbox.example_handler_logged",
        extra={"event_type": event.event_type, "aggregate_id": str(event.aggregate_id)},
    )


register_handler("example.ping", _handle_ping)
register_handler("example.log", _handle_log_example)
