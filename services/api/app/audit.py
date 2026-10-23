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
        [prev_hash, action, entity_type, entity_id, _canonical(before), _canonical(after)]
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
    last = session.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).scalar_one_or_none()
    prev_hash = last.row_hash if last else GENESIS_HASH
    row_hash = compute_row_hash(prev_hash, action, entity_type, entity_id, before, after)
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


def verify_chain(session: Session, from_id: int | None = None) -> ChainVerificationResult:
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
    query = select(AuditLog).order_by(AuditLog.id.asc()).execution_options(populate_existing=True)
    if from_id is not None:
        query = query.where(AuditLog.id >= from_id)
    rows = session.execute(query).scalars().all()
    if not rows:
        return ChainVerificationResult(True)

    expected_prev = GENESIS_HASH if from_id is None else rows[0].prev_hash
    for row in rows:
        if row.prev_hash != expected_prev:
            return ChainVerificationResult(False, row.id, "prev_hash does not match prior row's row_hash")
        expected_hash = compute_row_hash(
            row.prev_hash, row.action, row.entity_type, row.entity_id, row.before, row.after
        )
        if expected_hash != row.row_hash:
            return ChainVerificationResult(False, row.id, "row_hash does not match recomputed hash of row content")
        expected_prev = row.row_hash
    return ChainVerificationResult(True)
