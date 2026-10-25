"""Notification API router (F-14 / SPEC §10, §11)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.authz import Principal
from app.db import get_session
from app.models.enums import AppRole, NotificationStatus
from app.models.workflow import (
    NotificationDLQ,
    NotificationPreference,
    UserNotification,
)
from app.notifications.devices import register_device, revoke_device_token
from app.notifications.pipeline import process_domain_event
from app.notifications.resolver import UNSUPPRESSIBLE_CATEGORIES

router = APIRouter(prefix="/v1", tags=["notifications"])


# --- Schemas ---


class DeviceRegistrationPayload(BaseModel):
    platform: str = Field(..., description="android, ios, or web")
    provider: str = Field(..., description="fcm, apns, or webpush")
    push_token: str | None = None
    endpoint: str | None = None
    auth_key: str | None = None
    p256dh_key: str | None = None
    app_version: str | None = None


class DeviceRevokePayload(BaseModel):
    push_token: str


class NotificationPreferenceUpdatePayload(BaseModel):
    category: str
    channel: str
    enabled: bool
    locale: str = "en"
    quiet_hours_enabled: bool = False
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


class TestNotificationPayload(BaseModel):
    category: str = "critical_workflow"
    title: str = "Test Compliance Alert"
    body: str = "This is a verified test alert to confirm notification delivery."


class UserNotificationResponse(BaseModel):
    id: uuid.UUID
    category: str
    channel: str
    template_key: str
    status: str
    title: str
    body: str
    deep_link: str | None
    lock_screen_title: str | None
    lock_screen_body: str | None = None
    is_read: bool
    created_at: datetime
    read_at: datetime | None
    acknowledged_at: datetime | None
    actioned_at: datetime | None
    provider_accepted_at: datetime | None


class InboxResponse(BaseModel):
    items: list[UserNotificationResponse]
    unread_count: int
    total_count: int


# --- Endpoints ---


@router.get("/notifications", response_model=InboxResponse)
@router.get("/inbox", response_model=InboxResponse)
def get_inbox(
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    unread_only: bool = Query(False),
    since: datetime | None = Query(
        None, description="Filter notifications created since timestamp"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Retrieves user's in-app inbox items with live unread counter."""
    stmt = select(UserNotification).where(
        UserNotification.recipient_user_id == principal.id
    )

    if since:
        stmt = stmt.where(UserNotification.created_at >= since)
    if category:
        stmt = stmt.where(UserNotification.category == category)
    if status_filter:
        stmt = stmt.where(UserNotification.status == status_filter)
    if unread_only:
        stmt = stmt.where(UserNotification.is_read.is_(False))

    total_count = session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()

    unread_count = session.execute(
        select(func.count())
        .select_from(UserNotification)
        .where(
            UserNotification.recipient_user_id == principal.id,
            UserNotification.is_read.is_(False),
        )
    ).scalar_one()

    items = (
        session.execute(
            stmt.order_by(UserNotification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        .scalars()
        .all()
    )

    return InboxResponse(
        items=[
            UserNotificationResponse(
                id=n.id,
                category=n.category,
                channel=n.channel,
                template_key=n.template_key,
                status=n.status,
                title=n.title,
                body=n.body,
                deep_link=n.deep_link,
                lock_screen_title=n.lock_screen_title,
                lock_screen_body=n.lock_screen_body,
                is_read=n.is_read,
                created_at=n.created_at,
                read_at=n.read_at,
                acknowledged_at=n.acknowledged_at,
                actioned_at=n.actioned_at,
                provider_accepted_at=n.provider_accepted_at,
            )
            for n in items
        ],
        unread_count=unread_count,
        total_count=total_count,
    )


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_read(
    notification_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Records OPENED stage (SPEC §11.3)."""
    notif = session.get(UserNotification, notification_id)
    if not notif or notif.recipient_user_id != principal.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notif.is_read = True
    notif.read_at = datetime.now(UTC)
    if notif.status in (
        NotificationStatus.CREATED.value,
        NotificationStatus.QUEUED.value,
        NotificationStatus.PROVIDER_ACCEPTED.value,
    ):
        notif.status = NotificationStatus.OPENED.value

    session.commit()
    return {"id": str(notif.id), "status": notif.status, "read_at": notif.read_at}


@router.post(
    "/notifications/{notification_id}/acknowledge", status_code=status.HTTP_200_OK
)
def acknowledge_notification(
    notification_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Records ACKNOWLEDGED stage (SPEC §11.3). Explicit user acknowledgement."""
    notif = session.get(UserNotification, notification_id)
    if not notif or notif.recipient_user_id != principal.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notif.is_read = True
    notif.acknowledged_at = datetime.now(UTC)
    notif.status = NotificationStatus.ACKNOWLEDGED.value

    session.commit()
    return {
        "id": str(notif.id),
        "status": notif.status,
        "acknowledged_at": notif.acknowledged_at,
    }


@router.post("/notifications/{notification_id}/action", status_code=status.HTTP_200_OK)
def record_actioned(
    notification_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Records ACTIONED stage (SPEC §11.3). Triggered on successful state-changing action."""
    notif = session.get(UserNotification, notification_id)
    if not notif or notif.recipient_user_id != principal.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notif.is_read = True
    notif.actioned_at = datetime.now(UTC)
    notif.status = NotificationStatus.ACTIONED.value

    session.commit()
    return {
        "id": str(notif.id),
        "status": notif.status,
        "actioned_at": notif.actioned_at,
    }


@router.post("/devices/register", status_code=status.HTTP_200_OK)
def register_device_installation(
    payload: DeviceRegistrationPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Registers or updates a device token."""
    device = register_device(
        session,
        user_id=principal.id,
        platform=payload.platform,
        provider=payload.provider,
        push_token=payload.push_token,
        endpoint=payload.endpoint,
        auth_key=payload.auth_key,
        p256dh_key=payload.p256dh_key,
        app_version=payload.app_version,
    )
    session.commit()
    return {
        "id": str(device.id),
        "platform": device.platform,
        "is_active": device.is_active,
    }


@router.post("/devices/revoke", status_code=status.HTTP_200_OK)
def revoke_device(
    payload: DeviceRevokePayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Revokes a device token."""
    count = revoke_device_token(
        session, user_id=principal.id, push_token=payload.push_token
    )
    session.commit()
    return {"revoked_count": count}


@router.get("/notifications/preferences")
def get_preferences(
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Retrieves user notification preferences."""
    prefs = (
        session.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == principal.id
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "category": p.category,
            "channel": p.channel,
            "enabled": p.enabled,
            "locale": p.locale,
            "quiet_hours_enabled": p.quiet_hours_enabled,
            "quiet_hours_start": p.quiet_hours_start,
            "quiet_hours_end": p.quiet_hours_end,
        }
        for p in prefs
    ]


@router.put("/notifications/preferences", status_code=status.HTTP_200_OK)
def update_preference(
    payload: NotificationPreferenceUpdatePayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Updates user notification preferences.

    Validates that statutory/critical categories cannot be disabled.
    """
    if not payload.enabled and payload.category in UNSUPPRESSIBLE_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{payload.category}' is statutory and cannot be disabled per AICTE policy",
        )

    pref = session.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == principal.id,
            NotificationPreference.category == payload.category,
            NotificationPreference.channel == payload.channel,
        )
    ).scalar_one_or_none()

    if not pref:
        pref = NotificationPreference(
            id=uuid.uuid4(),
            user_id=principal.id,
            category=payload.category,
            channel=payload.channel,
            enabled=payload.enabled,
            locale=payload.locale,
            quiet_hours_enabled=payload.quiet_hours_enabled,
            quiet_hours_start=payload.quiet_hours_start,
            quiet_hours_end=payload.quiet_hours_end,
        )
        session.add(pref)
    else:
        pref.enabled = payload.enabled
        pref.locale = payload.locale
        pref.quiet_hours_enabled = payload.quiet_hours_enabled
        pref.quiet_hours_start = payload.quiet_hours_start
        pref.quiet_hours_end = payload.quiet_hours_end

    session.commit()
    return {"message": "Preference updated successfully"}


@router.post("/notifications/test", status_code=status.HTTP_200_OK)
def send_test_notification(
    payload: TestNotificationPayload,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Sends a verified test notification to the calling user's inbox and device."""
    notifs = process_domain_event(
        session,
        event_type="operations.alert",
        aggregate_type="user",
        aggregate_id=principal.id,
        payload={
            "recipient_user_id": str(principal.id),
            "subject": payload.title,
            "details": payload.body,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        },
    )
    session.commit()
    return {"message": "Test notification enqueued", "count": len(notifs)}


@router.get("/notifications/dlq")
def get_dead_letter_queue(
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Admin viewer for Dead-Letter Queue (SPEC §11.2 step 6). Bureau-side
    operator roles only — this is a system-wide, cross-institution view of
    notification delivery failures, never an institution-scoped resource, so
    no tenant role belongs on this list (CLAUDE.md non-negotiable #6)."""
    allowed_roles = (
        AppRole.PLATFORM_OPERATOR,
        AppRole.IDENTITY_ADMIN,
    )
    if principal.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Requires operator/admin role"
        )

    dlq_items = (
        session.execute(
            select(NotificationDLQ)
            .order_by(NotificationDLQ.created_at.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": str(item.id),
            "event_type": item.event_type,
            "error_reason": item.error_reason,
            "attempts": item.attempts,
            "status": item.status,
            "created_at": item.created_at,
            "replayed_at": item.replayed_at,
        }
        for item in dlq_items
    ]


@router.post("/notifications/dlq/{dlq_id}/replay")
def replay_dlq_item(
    dlq_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Replays an exhausted dead-letter item. Bureau-side operator roles
    only — same reasoning as get_dead_letter_queue above."""
    allowed_roles = (
        AppRole.PLATFORM_OPERATOR,
        AppRole.IDENTITY_ADMIN,
    )
    if principal.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Requires operator/admin role"
        )

    item = session.get(NotificationDLQ, dlq_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="DLQ item not found"
        )

    item.status = "REPLAYED"
    item.replayed_at = datetime.now(UTC)
    session.commit()
    return {"message": "DLQ item marked for replay"}


@router.get("/notifications/funnel")
def get_funnel_metrics(
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    """Returns funnel metrics measuring each pipeline stage separately (SPEC §11.1, §11.3)."""
    counts = dict(
        session.execute(
            select(UserNotification.status, func.count(UserNotification.id)).group_by(
                UserNotification.status
            )
        ).all()
    )

    return {
        "CREATED": counts.get(NotificationStatus.CREATED.value, 0),
        "QUEUED": counts.get(NotificationStatus.QUEUED.value, 0),
        "PROVIDER_ACCEPTED": counts.get(NotificationStatus.PROVIDER_ACCEPTED.value, 0),
        "PROVIDER_FAILED": counts.get(NotificationStatus.PROVIDER_FAILED.value, 0),
        "DEVICE_RECEIVED": counts.get(NotificationStatus.DEVICE_RECEIVED.value, 0),
        "OPENED": counts.get(NotificationStatus.OPENED.value, 0),
        "ACKNOWLEDGED": counts.get(NotificationStatus.ACKNOWLEDGED.value, 0),
        "ACTIONED": counts.get(NotificationStatus.ACTIONED.value, 0),
        "DEAD_LETTER": counts.get(NotificationStatus.DEAD_LETTER.value, 0),
    }
