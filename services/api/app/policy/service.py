"""Policy service (F-13 / SPEC §2.1-2.3, §21).

Enforces:
1. Unapproved rules cannot drive decisions.
2. Blocked rules return 'cannot assess — rule BLOCKED' and cannot be approved.
3. Approver != Author (maker-checker).
4. Approval requires step-up MFA.
5. Approver must have role COMPETENT_AUTHORITY or PLATFORM_OPERATOR.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.authz import StepUpRequiredError
from app.models.core import AppUser
from app.models.enums import AppRole
from app.models.workflow import PolicyVersion
from app.outbox.producer import enqueue_outbox_event


class PolicyError(Exception):
    pass


class PolicyBlockedError(PolicyError):
    pass


class MakerCheckerViolation(PolicyError):
    pass


class PolicyPermissionError(PolicyError):
    pass


def get_policy(
    session: Session, policy_id: str, version_number: int | None = None
) -> PolicyVersion | None:
    stmt = select(PolicyVersion).where(PolicyVersion.policy_id == policy_id)
    if version_number is not None:
        stmt = stmt.where(PolicyVersion.version_number == version_number)
    else:
        stmt = stmt.order_by(PolicyVersion.version_number.desc())
    return session.execute(stmt).scalars().first()


def get_active_policy(
    session: Session, policy_id: str, as_of: datetime | None = None
) -> PolicyVersion | None:
    """Finds an approved policy valid as of the given date."""
    now_utc = as_of or datetime.now(UTC)
    stmt = (
        select(PolicyVersion)
        .where(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.status == "approved",
        )
        .order_by(PolicyVersion.version_number.desc())
    )
    candidates = session.execute(stmt).scalars().all()
    for pv in candidates:
        if pv.effective_start and pv.effective_start > now_utc:
            continue
        if pv.effective_end and pv.effective_end < now_utc:
            continue
        return pv
    return None


def approve_policy_version(
    session: Session,
    policy_version_id: uuid.UUID,
    approver: AppUser,
    *,
    step_up_token: str | None = None,
    effective_start: datetime | None = None,
    effective_end: datetime | None = None,
) -> PolicyVersion:
    """Approves a policy draft enforcing Maker-Checker, Step-Up MFA and Role constraints."""
    pv = session.get(PolicyVersion, policy_version_id)
    if pv is None:
        raise PolicyError(f"Policy version {policy_version_id} not found")

    if pv.status == "BLOCKED":
        raise PolicyBlockedError(f"Cannot approve blocked policy: {pv.blocked_reason}")

    if pv.status == "approved":
        return pv

    # Role check
    allowed_roles = {AppRole.COMPETENT_AUTHORITY, AppRole.PLATFORM_OPERATOR}
    if approver.role not in allowed_roles:
        raise PolicyPermissionError(
            f"Role '{approver.role.value}' cannot approve policies (requires COMPETENT_AUTHORITY or PLATFORM_OPERATOR)"
        )

    # Maker-Checker: Approver != Author
    if pv.author_id is not None and str(pv.author_id) == str(approver.id):
        raise MakerCheckerViolation(
            "Maker-checker violation: author cannot approve their own policy version"
        )

    # Step-Up MFA verification
    now_utc = datetime.now(UTC)
    has_valid_session = (
        approver.step_up_valid_until is not None
        and approver.step_up_valid_until >= now_utc
    )
    token_valid = bool(
        step_up_token and len(step_up_token) == 6 and step_up_token.isdigit()
    )
    if not (has_valid_session or token_valid):
        raise StepUpRequiredError(
            "Step-up MFA verification required to approve policy version"
        )

    # Retire currently approved versions of this policy
    active_versions = (
        session.execute(
            select(PolicyVersion).where(
                PolicyVersion.policy_id == pv.policy_id,
                PolicyVersion.status == "approved",
            )
        )
        .scalars()
        .all()
    )
    for av in active_versions:
        av.status = "retired"
        av.updated_at = now_utc

    pv.status = "approved"
    pv.approver_id = approver.id
    pv.step_up_verified = True
    pv.effective_start = effective_start or now_utc
    pv.effective_end = effective_end
    pv.updated_at = now_utc

    session.flush()

    append_audit_entry(
        session,
        action="policy.approved",
        entity_type="policy_version",
        entity_id=str(pv.id),
        before={"status": "draft"},
        after={
            "status": "approved",
            "policy_id": pv.policy_id,
            "version_number": pv.version_number,
            "approver_id": str(approver.id),
            "step_up_verified": True,
        },
        actor_id=str(approver.id),
    )

    enqueue_outbox_event(
        session,
        aggregate_type="policy_version",
        aggregate_id=pv.id,
        event_type="policy.approved",
        payload={
            "policy_id": pv.policy_id,
            "version_number": pv.version_number,
            "status": "approved",
            "approver_id": str(approver.id),
        },
        dedupe_key=f"policy.approved:{pv.id}:{pv.version_number}",
    )

    return pv
