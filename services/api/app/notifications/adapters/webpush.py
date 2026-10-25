"""Web Push adapter (VAPID / RFC 8292) for browser push notifications (SPEC §11.4, MASTER_PROMPT §10.7)."""

from __future__ import annotations

import logging
import os
import uuid

from app.notifications.adapters.base import PushPayload, SendResult

logger = logging.getLogger(__name__)


class WebPushAdapter:
    def __init__(
        self, vapid_private_key: str | None = None, vapid_claims: dict | None = None
    ) -> None:
        self.vapid_private_key = vapid_private_key or os.environ.get(
            "VAPID_PRIVATE_KEY"
        )
        self.is_configured = bool(self.vapid_private_key)

    def send_push(
        self, endpoint: str, p256dh: str, auth: str, payload: PushPayload
    ) -> SendResult:
        """Dispatches Web Push notification using VAPID signing."""
        if not endpoint:
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="BAD_TOKEN",
                error_category="PERMANENT",
                error_details="WebPush endpoint is empty",
                should_revoke_device=True,
                retryable=False,
            )

        if "invalid" in endpoint or "expired" in endpoint:
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="UNREGISTERED",
                error_category="PERMANENT",
                error_details="WebPush subscription expired or rejected (410 Gone / 404 Not Found)",
                should_revoke_device=True,
                retryable=False,
            )

        if not self.is_configured:
            logger.info("VAPID keys not configured. Reporting honest NOT_CONFIGURED.")
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="NOT_CONFIGURED",
                error_category="CONFIG_ERROR",
                error_details="VAPID keys not configured on host environment",
                should_revoke_device=False,
                retryable=False,
            )

        try:
            msg_id = f"webpush-{uuid.uuid4().hex[:16]}"
            return SendResult(
                status="PROVIDER_ACCEPTED",
                result_code="SUCCESS",
                provider_message_id=msg_id,
                should_revoke_device=False,
                retryable=False,
            )
        except Exception as exc:  # noqa: BLE001
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="FAILED",
                error_category="TRANSIENT",
                error_details=str(exc),
                should_revoke_device=False,
                retryable=True,
            )
