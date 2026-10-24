"""Optimistic concurrency helper (MASTER_PROMPT §16: "All state-changing
endpoints: `Idempotency-Key`, `If-Match`/`ETag` or `row_version`, audit
+ outbox atomically.").

Pattern: a mutable resource that's edited through a "read current state,
then submit a change" flow (as opposed to an append-only/event-sourced
write) should expose a version token in its GET response as an `ETag`
header, and require that same token back as `If-Match` on the mutating
request. A mismatch means someone else changed the resource in between
— that must be a 409 Conflict (`app.problem_json.ConflictError`), never
a silent overwrite.

Two ways to compute the version token:
 1. A real `row_version` INTEGER column, incremented on every UPDATE
    (SQLAlchemy's built-in `mapper.version_id_col` support can do this
    automatically, raising `StaleDataError` if the
    `WHERE id=... AND row_version=:n` matches zero rows — which a caller
    turns into this module's `ConflictError`). This is the correct
    production mechanism, but it requires an actual migration to add
    the column — not this phase's to create (see this phase's task
    brief: no Alembic migrations this phase). Do it in whichever future
    phase owns the model being retrofitted.
 2. Until that column exists, a column that *already* changes on every
    UPDATE is a usable stand-in version token today — just a
    timestamp-shaped one instead of an integer-shaped one. The worked
    example below uses exactly that: `Instrument.updated_at`
    (`onupdate=func.now()`, already present, no migration needed).

Worked example (against `app.models.core.Instrument`, which has no
`row_version` column — picked per this phase's brief: "one worked
example against an existing model that doesn't already have this"):

    @router.get("/v1/instruments/{id}")
    def get_instrument(id: UUID, session: Session = Depends(get_db)):
        instrument = session.get(Instrument, id)
        if instrument is None:
            raise NotFoundError()
        etag = etag_from_updated_at(instrument.updated_at)
        return JSONResponse(content=serialize(instrument), headers={"ETag": etag})

    @router.patch("/v1/instruments/{id}")
    def update_instrument(
        id: UUID,
        body: InstrumentPatch,
        if_match: str | None = Header(default=None, alias="If-Match"),
        session: Session = Depends(get_db),
    ):
        instrument = session.get(Instrument, id)
        if instrument is None:
            raise NotFoundError()
        check_if_match(if_match, etag_from_updated_at(instrument.updated_at))
        # ... apply body's changes, session.commit() ...
        # instrument.updated_at just changed, so the ETag this response
        # returns is already the *new* token — no extra query needed.
        return JSONResponse(
            content=serialize(instrument),
            headers={"ETag": etag_from_updated_at(instrument.updated_at)},
        )

The moment a real `row_version` column lands on a model, swap
`etag_from_updated_at` for `etag_from_row_version` at that model's call
sites — both produce an opaque quoted ETag string, so nothing on the
client side needs to change.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from app.problem_json import ConflictError


def etag_from_updated_at(updated_at: datetime) -> str:
    """Opaque, quoted ETag derived from a timestamp-shaped version
    token. Quoted per RFC 9110 (ETag field values are quoted strings)."""
    digest = hashlib.sha256(updated_at.isoformat().encode("utf-8")).hexdigest()[:32]
    return f'"{digest}"'


def etag_from_row_version(row_version: int) -> str:
    """Same opaque-quoted-string shape, for a future real `row_version`
    integer column (see module docstring, mechanism 1)."""
    return f'"{row_version}"'


def check_if_match(if_match_header: str | None, current_etag: str) -> None:
    """Raises `ConflictError` (409) if the caller's `If-Match` header
    doesn't match the resource's current ETag — i.e. the resource
    changed between the caller's GET and this write. A missing header
    on a mutating request is also a conflict: no version was proven to
    have been read first.
    """
    if if_match_header is None:
        raise ConflictError("If-Match header is required for this update")
    # Clients may send a comma-separated list, or the wildcard '*' per
    # RFC 9110 — '*' matches any current representation.
    candidates = {token.strip() for token in if_match_header.split(",")}
    if "*" in candidates:
        return
    if current_etag not in candidates:
        raise ConflictError(
            "resource has changed since it was last read (stale If-Match)"
        )
