"""Device installation lifecycle and token management (SPEC §11.6, MASTER_PROMPT §10.5)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import DeviceInstallation

logger = logging.getLogger(__name__)


def register_device(
    session: Session,
    *,
    user_id: uuid.UUID,
    platform: str,
    provider: str,
    push_token: str | None = None,
    endpoint: str | None = None,
    auth_key: str | None = None,
    p256dh_key: str | None = None,
    app_version: str | None = None,
) -> DeviceInstallation:
    """Registers or refreshes a device installation token.

    If the push_token was previously linked to another user, deactivates the prior association
    to strictly prevent cross-user token reuse on device handover.
    """
    now = datetime.now(UTC)

    # If this push token was active on ANY other user, revoke it first
    if push_token:
        prior_devices = (
            session.execute(
                select(DeviceInstallation).where(
                    DeviceInstallation.push_token == push_token,
                    DeviceInstallation.user_id != user_id,
                    DeviceInstallation.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        for d in prior_devices:
            d.is_active = False
            d.revoked_at = now

    # Check if user already registered this device/token
    existing = None
    if push_token:
        existing = session.execute(
            select(DeviceInstallation).where(
                DeviceInstallation.user_id == user_id,
                DeviceInstallation.push_token == push_token,
            )
        ).scalar_one_or_none()

    if existing:
        existing.is_active = True
        existing.revoked_at = None
        existing.last_registered_at = now
        existing.last_seen_at = now
        existing.app_version = app_version or existing.app_version
        session.flush()
        return existing

    device = DeviceInstallation(
        id=uuid.uuid4(),
        user_id=user_id,
        platform=platform.lower(),
        provider=provider.lower(),
        push_token=push_token,
        endpoint=endpoint,
        auth_key=auth_key,
        p256dh_key=p256dh_key,
        app_version=app_version,
        is_active=True,
        created_at=now,
        last_registered_at=now,
        last_seen_at=now,
    )
    session.add(device)
    session.flush()
    return device


def revoke_device_token(
    session: Session,
    *,
    user_id: uuid.UUID,
    push_token: str,
) -> int:
    """Revokes a specific device token for a user."""
    devices = (
        session.execute(
            select(DeviceInstallation).where(
                DeviceInstallation.user_id == user_id,
                DeviceInstallation.push_token == push_token,
                DeviceInstallation.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now(UTC)
    count = 0
    for d in devices:
        d.is_active = False
        d.revoked_at = now
        count += 1
    session.flush()
    return count


def revoke_all_user_devices(
    session: Session,
    user_id: uuid.UUID,
) -> int:
    """Revokes all active device installations for a user (called on logout/session revocation).

    Guarantees: after logout, the previous user's device token receives NO notifications.
    """
    devices = (
        session.execute(
            select(DeviceInstallation).where(
                DeviceInstallation.user_id == user_id,
                DeviceInstallation.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now(UTC)
    count = 0
    for d in devices:
        d.is_active = False
        d.revoked_at = now
        count += 1
    session.flush()
    return count
