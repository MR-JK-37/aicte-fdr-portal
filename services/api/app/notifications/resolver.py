"""Recipient and preference resolution from current scope (SPEC §11.2, §11.5, MASTER_PROMPT §10.2 step 2, §10.4)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import AppUser
from app.models.enums import AppRole, NotificationCategory
from app.models.workflow import NotificationPreference

logger = logging.getLogger(__name__)

# Categories that can NEVER be suppressed by quiet hours or opt-outs (MASTER_PROMPT §10.4)
UNSUPPRESSIBLE_CATEGORIES = {
    NotificationCategory.CRITICAL_WORKFLOW.value,
    NotificationCategory.DEADLINE.value,
    NotificationCategory.SECURITY_ACCOUNT.value,
}


def resolve_recipients(
    session: Session,
    *,
    event_type: str,
    institution_id: uuid.UUID | None = None,
    specific_user_id: uuid.UUID | None = None,
    target_role: AppRole | str | None = None,
    region_id: str | None = None,
) -> list[AppUser]:
    """Resolves recipient candidates from current, approved database records.
    Never relies on stale cached lists.
    """
    stmt = select(AppUser).where(AppUser.is_active.is_(True))

    if specific_user_id:
        stmt = stmt.where(AppUser.id == specific_user_id)
        return list(session.execute(stmt).scalars().all())

    users: list[AppUser] = []

    if institution_id:
        # For institution-level events, notify active submitters and org admins of that institution
        inst_stmt = select(AppUser).where(
            AppUser.is_active.is_(True),
            AppUser.institution_id == institution_id,
        )
        users.extend(session.execute(inst_stmt).scalars().all())

    if target_role:
        role_val = (
            target_role.value if hasattr(target_role, "value") else str(target_role)
        )
        role_stmt = select(AppUser).where(
            AppUser.is_active.is_(True),
            AppUser.role == role_val,
        )
        if region_id:
            role_stmt = role_stmt.where(
                (AppUser.region_id == region_id) | (AppUser.region_id.is_(None))
            )
        users.extend(session.execute(role_stmt).scalars().all())

    # Fallback: if no users resolved and it is a critical/operations event, notify platform operators
    if not users and "operations" in event_type:
        op_stmt = select(AppUser).where(
            AppUser.is_active.is_(True),
            AppUser.role.in_(
                [AppRole.PLATFORM_OPERATOR.value, AppRole.IDENTITY_ADMIN.value]
            ),
        )
        users.extend(session.execute(op_stmt).scalars().all())

    # De-duplicate by user.id
    unique_users = {u.id: u for u in users}
    return list(unique_users.values())


def should_deliver_to_channel(
    session: Session,
    user_id: uuid.UUID,
    category: str,
    channel: str,
    now_utc: datetime | None = None,
) -> tuple[bool, str]:
    """Checks user notification preferences and quiet hours.

    CRITICAL RULE (MASTER_PROMPT §10.4):
    Quiet hours and opt-outs NEVER suppress critical_workflow, deadline,
    or security_account items; user preference cannot silently cancel an obligation.
    """
    now = now_utc or datetime.now(UTC)
    is_unsupressible = category in UNSUPPRESSIBLE_CATEGORIES

    pref = session.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.category == category,
            NotificationPreference.channel == channel,
        )
    ).scalar_one_or_none()

    if pref:
        if not pref.enabled:
            if is_unsupressible:
                return True, "delivered_statutory_override"
            return False, "user_disabled"

        if pref.quiet_hours_enabled and pref.quiet_hours_start and pref.quiet_hours_end:
            current_time_str = now.strftime("%H:%M")
            start = pref.quiet_hours_start
            end = pref.quiet_hours_end

            in_quiet_hours = False
            if start <= end:
                in_quiet_hours = start <= current_time_str <= end
            else:
                # Spans midnight
                in_quiet_hours = current_time_str >= start or current_time_str <= end

            if in_quiet_hours:
                if is_unsupressible:
                    return True, "quiet_hours_bypassed_critical"
                return False, "quiet_hours_suppressed"

    # Default conservative policy: in_app and push are enabled by default
    return True, "default_allowed"
