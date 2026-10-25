"""Policy draft loader (F-13 / SPEC §2.1-2.3, §21).

Imports official policy drafts from config/policy-drafts/:
- APH 2024-27 Table 1.4 (amounts per programme/level) -> status 'draft'
- APH 2024-27 Clause 6.46 (release checklist) -> status 'draft'
- Reminder schedule example -> status 'draft'
- Penalty rules -> status 'BLOCKED: awaiting AICTE written confirmation (D-01)'

CRITICAL SAFETY INVARIANT:
No draft is EVER imported as 'approved'. Approving requires a different user
(maker-checker) plus step-up MFA.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import PolicyVersion

logger = logging.getLogger(__name__)

DEFAULT_DRAFTS_DIR = Path(__file__).resolve().parents[3] / "config" / "policy-drafts"
# Fallback to repo root config/policy-drafts if run from another cwd
ALT_DRAFTS_DIR = Path("/home/mr1jk1/Desktop/SIH/config/policy-drafts")


def _find_drafts_dir(override: Path | None = None) -> Path:
    if override and override.exists():
        return override
    if DEFAULT_DRAFTS_DIR.exists():
        return DEFAULT_DRAFTS_DIR
    if ALT_DRAFTS_DIR.exists():
        return ALT_DRAFTS_DIR
    raise FileNotFoundError(
        f"Policy drafts directory not found at {DEFAULT_DRAFTS_DIR} or {ALT_DRAFTS_DIR}"
    )


def load_policy_drafts(
    session: Session, drafts_dir: Path | None = None
) -> list[PolicyVersion]:
    """Reads JSON files from config/policy-drafts and upserts them into policy_versions."""
    target_dir = _find_drafts_dir(drafts_dir)
    loaded: list[PolicyVersion] = []

    for path in sorted(target_dir.glob("*.json")):
        raw_bytes = path.read_bytes()
        doc_hash = hashlib.sha256(raw_bytes).hexdigest()
        data = json.loads(raw_bytes.decode("utf-8"))

        policy_id = data.get("policy_id") or path.stem
        raw_status = data.get("status", "draft")
        blocked_reason = data.get("blocked_reason")

        # Normalize status: only 'draft' or 'BLOCKED' allowed on import
        if raw_status.upper() == "BLOCKED" or "BLOCKED" in str(blocked_reason or ""):
            status = "BLOCKED"
            blocked_reason = (
                blocked_reason or "awaiting AICTE written confirmation (D-01)"
            )
        else:
            status = "draft"
            blocked_reason = None

        source_info = data.get("source", {})
        document_name = (
            source_info.get("document") or data.get("$comment", path.name)[:255]
        )
        clause = source_info.get("clause") or (data.get("checklist") and "6.46") or None
        source_url = source_info.get("url")

        existing = session.execute(
            select(PolicyVersion).where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.version_number == 1,
            )
        ).scalar_one_or_none()

        if existing is None:
            pv = PolicyVersion(
                id=uuid.uuid4(),
                policy_id=policy_id,
                document=document_name,
                clause=clause,
                source_url=source_url,
                document_hash=doc_hash,
                config_payload=data,
                status=status,
                blocked_reason=blocked_reason,
                author_id=None,
                approver_id=None,
                step_up_verified=False,
                version_number=1,
                changelog=f"Imported from {path.name} as {status}",
            )
            session.add(pv)
            loaded.append(pv)
            logger.info("Imported policy draft %s with status %s", policy_id, status)
        else:
            # Update draft payload if hash changed and still in draft/BLOCKED
            if (
                existing.status in ("draft", "BLOCKED")
                and existing.document_hash != doc_hash
            ):
                existing.config_payload = data
                existing.document_hash = doc_hash
                existing.status = status
                existing.blocked_reason = blocked_reason
                loaded.append(existing)

    session.flush()
    return loaded
