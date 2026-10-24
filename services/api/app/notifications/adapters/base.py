"""Base adapter interface and result models for push and communication channels (SPEC §11.3, §11.4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class PushPayload:
    user_notification_id: uuid.UUID
    recipient_user_id: uuid.UUID
    category: str
    channel: str
    title: str
    body: str
    lock_screen_title: str | None
    lock_screen_body: str | None
    deep_link: str | None
    metadata: dict[str, Any]


@dataclass
class SendResult:
    status: str  # PROVIDER_ACCEPTED | PROVIDER_FAILED
    result_code: str  # SUCCESS | UNREGISTERED | BAD_TOKEN | PROVIDER_OUTAGE | QUOTA_EXCEEDED | NOT_CONFIGURED | FAILED
    provider_message_id: str | None = None
    error_category: str | None = None  # TRANSIENT | PERMANENT | CONFIG_ERROR
    error_details: str | None = None
    should_revoke_device: bool = False
    retryable: bool = False
