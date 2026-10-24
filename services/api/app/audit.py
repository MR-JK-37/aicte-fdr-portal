"""Hash-chained audit log: each row's hash commits to the previous row's
hash plus its own content, so any out-of-band tamper with a stored row
breaks the chain from that point forward and is detectable by replay.

This mirrors a basic blockchain-style tamper-evidence log, not a
blockchain — there is one writer (the API/worker processes) and no
consensus; the guarantee is detection, not prevention. Prevention is the
companion DB trigger that rejects UPDATE/DELETE on audit_log for the app
role (see migration 0001).
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

GENESIS_HASH = "0" * 64


def _canonical(payload: dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), default=str)


def compute_row_hash(
    prev_hash: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict | None,
    after: dict | None,
) -> str:
    material = "|".join(
        [
            prev_hash,
            action,
            entity_type,
            entity_id,
            _canonical(before),
            _canonical(after),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def append_audit_entry(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict | None = None,
    after: dict | None = None,
    actor_id: str | None = None,
    institution_id: str | None = None,
) -> AuditLog:
    from app.db import set_app_context

    set_app_context(session, role="platform_operator")

    last = session.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
    ).scalar_one_or_none()
    prev_hash = last.row_hash if last else GENESIS_HASH
    row_hash = compute_row_hash(
        prev_hash, action, entity_type, entity_id, before, after
    )
    entry = AuditLog(
        actor_id=actor_id,
        institution_id=institution_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
    session.add(entry)
    session.flush()
    return entry


@dataclass
class ChainVerificationResult:
    ok: bool
    broken_at_id: int | None = None
    reason: str | None = None


def verify_chain(
    session: Session, from_id: int | None = None
) -> ChainVerificationResult:
    """Verifies hash-chain integrity.

    With `from_id=None`, verifies the whole log from genesis — the real
    production check. With `from_id` set, treats that row's own stored
    `prev_hash` as a trusted anchor and verifies forward from there; this
    lets tests (and incremental/checkpointed verification jobs) check a
    segment without depending on the full history already being pristine.
    """
    # populate_existing: without it, rows already in this Session's identity
    # map (e.g. from an earlier read in the same session) keep their
    # in-memory attribute values instead of reflecting rows mutated
    # out-of-band by another connection — which would silently defeat this
    # exact tamper check.
    from app.db import set_app_context

    set_app_context(session, role="audit_reviewer")

    query = (
        select(AuditLog)
        .order_by(AuditLog.id.asc())
        .execution_options(populate_existing=True)
    )
    if from_id is not None:
        query = query.where(AuditLog.id >= from_id)
    rows = session.execute(query).scalars().all()
    if not rows:
        return ChainVerificationResult(True)

    expected_prev = GENESIS_HASH if from_id is None else rows[0].prev_hash
    for row in rows:
        if row.prev_hash != expected_prev:
            return ChainVerificationResult(
                False, row.id, "prev_hash does not match prior row's row_hash"
            )
        expected_hash = compute_row_hash(
            row.prev_hash,
            row.action,
            row.entity_type,
            row.entity_id,
            row.before,
            row.after,
        )
        if expected_hash != row.row_hash:
            return ChainVerificationResult(
                False, row.id, "row_hash does not match recomputed hash of row content"
            )
        expected_prev = row.row_hash
    return ChainVerificationResult(True)


import base64
from datetime import UTC, datetime

from cryptography.hazmat.primitives.asymmetric import ed25519

from app.models.audit import AuditCheckpoint

# 32-byte deterministic key for development / testing
_DEV_KEY_BYTES = b"32-byte-secret-dev-audit-key-123"
DEV_SIGNING_KEY = ed25519.Ed25519PrivateKey.from_private_bytes(_DEV_KEY_BYTES)
DEV_PUBLIC_KEY = DEV_SIGNING_KEY.public_key()


def _format_checkpoint_payload(
    checkpoint_index: int,
    period_start: datetime,
    period_end: datetime,
    first_event_id: int | None,
    last_event_id: int | None,
    event_count: int,
    chain_root_hash: str,
) -> bytes:
    p_start_utc = (
        period_start.replace(tzinfo=UTC)
        if period_start.tzinfo is None
        else period_start.astimezone(UTC)
    )
    p_end_utc = (
        period_end.replace(tzinfo=UTC)
        if period_end.tzinfo is None
        else period_end.astimezone(UTC)
    )
    ts_start = int(p_start_utc.timestamp())
    ts_end = int(p_end_utc.timestamp())
    material = f"{checkpoint_index}|{ts_start}|{ts_end}|{first_event_id}|{last_event_id}|{event_count}|{chain_root_hash}"
    return material.encode("utf-8")


def create_checkpoint(
    session: Session,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    signing_key: ed25519.Ed25519PrivateKey | None = None,
    key_id: str = "dev-audit-key-1",
) -> AuditCheckpoint | None:
    """Creates a periodic signed checkpoint over un-checkpointed audit entries."""
    if signing_key is None:
        signing_key = DEV_SIGNING_KEY

    from app.db import set_app_context

    set_app_context(session, role="audit_reviewer")

    last_checkpoint = session.execute(
        select(AuditCheckpoint)
        .order_by(AuditCheckpoint.checkpoint_index.desc())
        .limit(1)
    ).scalar_one_or_none()

    next_index = (last_checkpoint.checkpoint_index + 1) if last_checkpoint else 1
    from_id = (
        (last_checkpoint.last_event_id + 1)
        if (last_checkpoint and last_checkpoint.last_event_id)
        else 1
    )

    query = select(AuditLog).where(AuditLog.id >= from_id).order_by(AuditLog.id.asc())
    rows = session.execute(query).scalars().all()
    if not rows:
        return None

    first_event = rows[0]
    last_event = rows[-1]

    now = datetime.now(UTC)
    p_start = period_start or (
        first_event.created_at
        if hasattr(first_event, "created_at") and first_event.created_at
        else now
    )
    p_end = period_end or now

    if p_start.tzinfo is None:
        p_start = p_start.replace(tzinfo=UTC)
    if p_end.tzinfo is None:
        p_end = p_end.replace(tzinfo=UTC)

    chain_root = last_event.row_hash
    count = len(rows)

    payload = _format_checkpoint_payload(
        next_index, p_start, p_end, first_event.id, last_event.id, count, chain_root
    )
    sig_bytes = signing_key.sign(payload)
    sig_b64 = base64.b64encode(sig_bytes).decode("utf-8")

    checkpoint = AuditCheckpoint(
        checkpoint_index=next_index,
        period_start=p_start,
        period_end=p_end,
        first_event_id=first_event.id,
        last_event_id=last_event.id,
        event_count=count,
        chain_root_hash=chain_root,
        signature=sig_b64,
        signer_key_id=key_id,
        created_at=now,
    )
    session.add(checkpoint)
    session.flush()
    return checkpoint


def verify_checkpoint(
    checkpoint: AuditCheckpoint,
    public_key: ed25519.Ed25519PublicKey | None = None,
) -> bool:
    """Cryptographically verifies the Ed25519 signature on an audit checkpoint."""
    if public_key is None:
        public_key = DEV_PUBLIC_KEY

    payload = _format_checkpoint_payload(
        checkpoint.checkpoint_index,
        checkpoint.period_start,
        checkpoint.period_end,
        checkpoint.first_event_id,
        checkpoint.last_event_id,
        checkpoint.event_count,
        checkpoint.chain_root_hash,
    )
    try:
        sig_bytes = base64.b64decode(checkpoint.signature)
        public_key.verify(sig_bytes, payload)
        return True
    except Exception:  # noqa: BLE001
        return False
