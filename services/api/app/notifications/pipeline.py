"""Outbox event handler and notification pipeline (SPEC §11.2, §11.3, MASTER_PROMPT §10.2)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import NotificationCategory, NotificationStatus
from app.models.workflow import (
    DeviceInstallation,
    NotificationAttempt,
    NotificationDLQ,
    SSEEvent,
    UserNotification,
)
from app.notifications.adapters.apns import APNsAdapter
from app.notifications.adapters.base import PushPayload, SendResult
from app.notifications.adapters.fcm import FCMAdapter
from app.notifications.adapters.webpush import WebPushAdapter
from app.notifications.resolver import resolve_recipients, should_deliver_to_channel
from app.notifications.templates import TEMPLATE_VERSION, render_template
from app.outbox.handlers import register_handler
from app.outbox.models import OutboxEvent

logger = logging.getLogger(__name__)

# Initialize adapters
_fcm_adapter = FCMAdapter()
_apns_adapter = APNsAdapter()
_webpush_adapter = WebPushAdapter()


def determine_category_and_deep_link(
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
) -> tuple[str, str]:
    """Determines the notification category and deep link from event type."""
    if "expiring" in event_type or "matured" in event_type or "deadline" in event_type:
        category = NotificationCategory.DEADLINE.value
    elif "security" in event_type or "session" in event_type:
        category = NotificationCategory.SECURITY_ACCOUNT.value
    elif (
        "operations" in event_type
        or "connector" in event_type
        or "outage" in event_type
    ):
        category = NotificationCategory.OPERATIONS.value
    else:
        category = NotificationCategory.CRITICAL_WORKFLOW.value

    if aggregate_type == "instrument":
        deep_link = f"/instruments/{aggregate_id}"
    elif aggregate_type == "observation":
        deep_link = f"/observations/{aggregate_id}"
    elif aggregate_type == "release_request":
        deep_link = f"/release/{aggregate_id}"
    elif aggregate_type == "institution":
        deep_link = f"/institutions/{aggregate_id}"
    else:
        deep_link = "/dashboard"

    return category, deep_link


def process_domain_event(
    session: Session,
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any],
    *,
    outbox_id: uuid.UUID | None = None,
) -> list[UserNotification]:
    """Processes an outbox domain event:
    1. Resolves recipients from current approved records.
    2. Persists UserNotification in-app inbox item FIRST (status=CREATED).
    3. Emits real-time SSE event to replay buffer.
    4. Evaluates active device registrations and dispatches push notifications.
    5. Records attempt in notification_attempts table.
    6. Automatically cleans invalid tokens and dead-letters exhausted events.
    """
    category, deep_link = determine_category_and_deep_link(
        event_type, aggregate_type, aggregate_id
    )
    institution_id_val = payload.get("institution_id")
    target_institution_id = (
        uuid.UUID(str(institution_id_val)) if institution_id_val else None
    )

    # Resolve recipients dynamically from database
    recipients = resolve_recipients(
        session,
        event_type=event_type,
        institution_id=target_institution_id,
        specific_user_id=uuid.UUID(str(payload["recipient_user_id"]))
        if "recipient_user_id" in payload
        else None,
        target_role=payload.get("target_role"),
    )

    created_notifications: list[UserNotification] = []
    now_utc = datetime.now(UTC)

    for user in recipients:
        # Check in-app delivery preferences
        in_app_allowed, _reason = should_deliver_to_channel(
            session, user.id, category, "in_app", now_utc=now_utc
        )
        if not in_app_allowed:
            continue

        # Render versioned, localized templates
        user_locale = getattr(user, "locale", "en") or "en"
        title, body, lock_title, lock_body = render_template(
            event_type, context=payload, locale=user_locale
        )

        # 1. Inbox-first persistence (SPEC §11.2 step 3, MASTER_PROMPT §10.2 step 3)
        notif = UserNotification(
            id=uuid.uuid4(),
            event_id=outbox_id,
            recipient_user_id=user.id,
            institution_id=user.institution_id or target_institution_id,
            category=category,
            channel="in_app",
            template_key=event_type,
            template_version=TEMPLATE_VERSION,
            locale=user_locale,
            status=NotificationStatus.CREATED.value,
            title=title,
            body=body,
            deep_link=deep_link,
            lock_screen_title=lock_title,
            lock_screen_body=lock_body,
            is_read=False,
            metadata_payload=payload,
            created_at=now_utc,
        )
        session.add(notif)
        session.flush()
        created_notifications.append(notif)

        # 2. Emit SSE event into buffer for real-time subscribers (MASTER_PROMPT §10.8)
        sse_item = SSEEvent(
            id=uuid.uuid4(),
            event_type="inbox.created",
            recipient_user_id=user.id,
            institution_id=user.institution_id,
            payload={
                "inbox_id": str(notif.id),
                "title": notif.title,
                "category": notif.category,
                "deep_link": notif.deep_link,
            },
            created_at=now_utc,
        )
        session.add(sse_item)

        # 3. Check for active device registrations
        devices = (
            session.execute(
                select(DeviceInstallation).where(
                    DeviceInstallation.user_id == user.id,
                    DeviceInstallation.is_active.is_(True),
                    DeviceInstallation.revoked_at.is_(None),
                )
            )
            .scalars()
            .all()
        )

        push_allowed, _push_reason = should_deliver_to_channel(
            session, user.id, category, "push", now_utc=now_utc
        )

        if devices and push_allowed:
            notif.status = NotificationStatus.QUEUED.value

            push_payload = PushPayload(
                user_notification_id=notif.id,
                recipient_user_id=user.id,
                category=category,
                channel="push",
                title=title,
                body=body,
                lock_screen_title=lock_title,
                lock_screen_body=lock_body,
                deep_link=deep_link,
                metadata={"inbox_id": str(notif.id), "event_type": event_type},
            )

            any_accepted = False
            for device in devices:
                if device.platform == "android":
                    send_res = _fcm_adapter.send_push(
                        device.push_token or "", push_payload
                    )
                elif device.platform == "ios":
                    send_res = _apns_adapter.send_push(
                        device.push_token or "", push_payload
                    )
                elif device.platform == "web":
                    send_res = _webpush_adapter.send_push(
                        device.endpoint or "",
                        device.p256dh_key or "",
                        device.auth_key or "",
                        push_payload,
                    )
                else:
                    send_res = SendResult(
                        status="PROVIDER_FAILED",
                        result_code="FAILED",
                        error_details=f"Unsupported platform {device.platform}",
                    )

                # Record delivery attempt (SPEC §11.2 step 5)
                attempt = NotificationAttempt(
                    id=uuid.uuid4(),
                    user_notification_id=notif.id,
                    provider=device.provider,
                    provider_message_id=send_res.provider_message_id,
                    attempt_number=1,
                    attempted_at=datetime.now(UTC),
                    result_code=send_res.result_code,
                    error_category=send_res.error_category,
                    error_details=send_res.error_details,
                )
                session.add(attempt)

                if send_res.status == "PROVIDER_ACCEPTED":
                    any_accepted = True

                # If token is invalid or unregistered: revoke immediately
                if send_res.should_revoke_device:
                    logger.info(
                        "Cleaning invalid device installation %s (reason: %s)",
                        device.id,
                        send_res.result_code,
                    )
                    device.is_active = False
                    device.revoked_at = datetime.now(UTC)

            if any_accepted:
                notif.status = NotificationStatus.PROVIDER_ACCEPTED.value
                notif.provider_accepted_at = datetime.now(UTC)
            else:
                notif.status = NotificationStatus.PROVIDER_FAILED.value
                # If provider failed and unrecoverable, dead-letter notice
                dlq_entry = NotificationDLQ(
                    id=uuid.uuid4(),
                    outbox_id=outbox_id,
                    user_notification_id=notif.id,
                    event_type=event_type,
                    error_reason="All push provider dispatch attempts failed",
                    attempts=len(devices),
                    payload=payload,
                    status="DEAD_LETTER",
                )
                session.add(dlq_entry)

    session.flush()
    return created_notifications


def _generic_outbox_handler(session: Session, event: OutboxEvent) -> None:
    """Outbox worker handler mapping OutboxEvent to notification pipeline."""
    process_domain_event(
        session,
        event_type=event.event_type,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        payload=event.payload or {},
        outbox_id=event.id,
    )


# Register outbox handlers for all core workflow events
CORE_OUTBOX_EVENTS = [
    "instrument.submitted",
    "instrument.returned",
    "instrument.matured",
    "instrument.expiring",
    "observation.created",
    "observation.responded",
    "observation.resolved",
    "release.submitted",
    "release.decision",
    "security.session_revoked",
    "operations.alert",
]

for evt in CORE_OUTBOX_EVENTS:
    register_handler(evt, _generic_outbox_handler)
