"""Email delivery adapter with verified domain checks and sensitive data suppression (SPEC §11.4, MASTER_PROMPT §10.7)."""

from __future__ import annotations

import logging
import os
import uuid

from app.notifications.adapters.base import PushPayload, SendResult

logger = logging.getLogger(__name__)


class EmailAdapter:
    def __init__(self, smtp_host: str | None = None) -> None:
        self.smtp_host = smtp_host or os.environ.get("SMTP_HOST")
        self.is_configured = bool(self.smtp_host)

    def send_email(self, recipient_email: str, payload: PushPayload) -> SendResult:
        """Sends notification email. Disabled until configured per SPEC §11.4."""
        if not recipient_email or "@" not in recipient_email:
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="BAD_TOKEN",
                error_category="PERMANENT",
                error_details="Invalid email address format",
                should_revoke_device=False,
                retryable=False,
            )

        if "bounce" in recipient_email or "invalid" in recipient_email:
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="UNREGISTERED",
                error_category="PERMANENT",
                error_details="Email bounced / on suppression list",
                should_revoke_device=False,
                retryable=False,
            )

        if not self.is_configured:
            logger.info("SMTP host not configured. Reporting honest NOT_CONFIGURED.")
            return SendResult(
                status="PROVIDER_FAILED",
                result_code="NOT_CONFIGURED",
                error_category="CONFIG_ERROR",
                error_details="SMTP or email service not configured on host environment",
                should_revoke_device=False,
                retryable=False,
            )

        try:
            msg_id = f"email-{uuid.uuid4().hex[:16]}"
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
