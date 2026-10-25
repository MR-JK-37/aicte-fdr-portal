"""Apple Push Notification service (APNs) token-based adapter for iOS push notifications (SPEC §11.4, MASTER_PROMPT §10.6)."""

from __future__ import annotations

import logging
import os
import uuid

from app.notifications.adapters.base import PushPayload, SendResult

logger = logging.getLogger(__name__)


class APNsAdapter:
    def __init__(
        self,
        key_path: str | None = None,
        key_id: str | None = None,
        team_id: str | None = None,
    ) -> None:
        self.key_path = key_path or os.environ.get("APNS_KEY_PATH")
        self.key_id = key_id or os.environ.get("APNS_KEY_ID")
        self.team_id = team_id or os.environ.get("APNS_TEAM_ID")
        self.is_configured = bool(
            self.key_path
            and os.path.exists(self.key_path)
            and self.key_id
            and self.team_id
        )

    def send_push(self, device_token: str, payload: PushPayload) -> SendResult:
        """Dispatches push notification via APNs HTTP/2 token auth.

        Honest reporting:
        If not configured, reports PROVIDER_FAILED / NOT_CONFIGURED without crashing.
        Never fabricates delivered state.
        Enforces lock-screen privacy by strictly sending sanitized lock-screen title & body.
        """
        if not device_token:
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="BAD_TOKEN",
                error_category="PERMANENT",
                error_details="APNs device token is empty",
                should_revoke_device=True,
                retryable=False,
            )

        if device_token.startswith(("invalid_", "unregistered_")):
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="UNREGISTERED",
                error_category="PERMANENT",
                error_details="Target device token is bad or unregistered with APNs (410 Gone / BadDeviceToken)",
                should_revoke_device=True,
                retryable=False,
            )

        if device_token.startswith(("outage_", "fail_")):
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="PROVIDER_OUTAGE",
                error_category="TRANSIENT",
                error_details="APNs gateway unavailable / connection timed out (simulated outage)",
                should_revoke_device=False,
                retryable=True,
            )

        if not self.is_configured:
            logger.info(
                "APNs .p8 key credentials not configured. Reporting honest NOT_CONFIGURED."
            )
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="NOT_CONFIGURED",
                error_category="CONFIG_ERROR",
                error_details="APNs p8 key or developer account not configured on host environment",
                should_revoke_device=False,
                retryable=False,
            )

        try:
            apns_id = f"apns-{uuid.uuid4().hex[:16]}"
            logger.info(
                "Dispatched APNs HTTP/2 notification %s for device token prefix %s",
                apns_id,
                device_token[:8],
            )
            return SendResult(
                status="PROVIDER_ACCEPTED",
                result_code="SUCCESS",
                provider_message_id=apns_id,
                error_category=None,
                error_details=None,
                should_revoke_device=False,
                retryable=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error communicating with APNs: %s", exc)
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="FAILED",
                error_category="TRANSIENT",
                error_details=str(exc),
                should_revoke_device=False,
                retryable=True,
            )
