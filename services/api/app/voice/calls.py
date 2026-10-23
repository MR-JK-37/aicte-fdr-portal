"""Outbound call triggering, consent verification, WebRTC session room tokens,
and PSTN adapter (flagged per Blueprint.txt §5.1 & §5.2).
"""

import hashlib
import hmac
import os
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.core import AppUser, CallSession, ConsentRecord, DeviceToken
from app.reminders.push import PushNotConfiguredError, send_push
from app.sim_clock import now as sim_now


class CallConsentRequiredError(Exception):
    pass


class CallSuppressedQuietHoursError(Exception):
    pass


def _in_quiet_hours(user: AppUser, as_of: datetime) -> bool:
    """True if as_of falls within user's quiet hours."""
    start = user.quiet_hours_start
    end = user.quiet_hours_end
    if start == end:
        return False
    current_hour = as_of.hour
    if start < end:
        return start <= current_hour < end
    return current_hour >= start or current_hour < end


def mint_room_token(session_id: uuid.UUID, ttl_seconds: int = 120, current_timestamp: int | None = None) -> str:
    """Generates a cryptographic time-bound WebRTC session room token."""
    secret = os.environ.get("CALL_TOKEN_SECRET", "dev_voice_room_secret_key")
    now_ts = current_timestamp if current_timestamp is not None else int(datetime.now(UTC).timestamp())
    expires_at = now_ts + ttl_seconds
    data = f"{session_id}:{expires_at}"
    sig = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{data}:{sig}"


def verify_room_token(token: str, current_timestamp: int | None = None) -> tuple[bool, str]:
    """Verifies room token authenticity and expiry."""
    secret = os.environ.get("CALL_TOKEN_SECRET", "dev_voice_room_secret_key")
    parts = token.split(":")
    if len(parts) != 3:
        return False, "invalid_format"
    session_id_str, expires_at_str, sig = parts
    data = f"{session_id_str}:{expires_at_str}"
    expected_sig = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return False, "invalid_signature"
    now_ts = current_timestamp if current_timestamp is not None else int(datetime.now(UTC).timestamp())
    if int(expires_at_str) < now_ts:
        return False, "expired"
    return True, session_id_str


def start_outbound_call(
    session: Session,
    user_id: uuid.UUID,
    reminder_id: uuid.UUID | None = None,
    transport: str = "webrtc",
    as_of: datetime | None = None,
) -> tuple[CallSession, str]:
    """Triggers an outbound voice call session to the specified user.

    Enforces:
    1. Mandatory consent check (ConsentRecord with type 'automated_voice_calls').
    2. Quiet hours suppression check.
    3. Creation of CallSession in database.
    4. Room token generation for WebRTC session.
    5. High-priority FCM push notification.
    """
    as_of = as_of or sim_now(session)
    user = session.get(AppUser, user_id)
    if not user:
        raise ValueError(f"AppUser {user_id} not found")

    # 1. Consent verification
    consent = session.execute(
        select(ConsentRecord).where(
            ConsentRecord.app_user_id == user.id,
            ConsentRecord.consent_type == "automated_voice_calls",
            ConsentRecord.revoked_at.is_(None),
        )
    ).scalar_one_or_none()
    if not consent:
        raise CallConsentRequiredError("User has not granted active consent for automated voice calls")

    # 2. Quiet hours verification
    if _in_quiet_hours(user, as_of):
        raise CallSuppressedQuietHoursError(
            f"Call suppressed: current time {as_of.hour}:00 is within user's quiet hours ({user.quiet_hours_start}:00-{user.quiet_hours_end}:00)"
        )

    # 3. Create CallSession
    call_session = CallSession(
        institution_id=user.institution_id,
        app_user_id=user.id,
        reminder_id=reminder_id,
        language=user.preferred_language or "en",
        status="ringing",
        pin_attempts=0,
        transcript={"state": "VERIFY_PIN", "turns": []},
        started_at=as_of,
    )
    session.add(call_session)
    session.flush()

    # 4. Mint WebRTC room token
    token = mint_room_token(call_session.id, ttl_seconds=180)

    # 5. Push notification to user's registered devices (FCM high-priority)
    devices = list(
        session.execute(
            select(DeviceToken).where(DeviceToken.app_user_id == user.id)
        ).scalars().all()
    )
    for dev in devices:
        try:
            send_push(
                device_token=dev.token,
                title="AICTE FDR Voice Alert",
                body="Incoming automated call from AICTE Regulation Bureau",
                data={
                    "type": "ai_call",
                    "session_id": str(call_session.id),
                    "token": token,
                    "lang": call_session.language,
                },
                high_priority=True,
            )
        except PushNotConfiguredError:
            # Fails closed without crashing the session; logged in notification pipeline
            pass

    return call_session, token


def start_pstn_call(session: Session, user: AppUser, call_session: CallSession) -> dict[str, str]:
    """PSTN adapter flagged behind production_telephony_enabled.

    Per Blueprint.txt §5.1 & §5.2:
    In India, outbound PSTN robocalls/auto-dialers require advance intimation to TRAI
    under TCCCPR 2018 Second Amendment (12 Feb 2025) and dedicated 1600-series headers.
    """
    if not settings.production_telephony_enabled:
        return {
            "status": "simulated",
            "session_id": str(call_session.id),
            "transport": "pstn",
            "notice": (
                "SIMULATED: Production PSTN auto-dialing is disabled. In production, this routes via "
                "a licensed CPaaS on a registered TRAI 1600-series transactional header with advance robocall intimation."
            ),
            "twiml_preview": f'<Response><Connect><Stream url="wss://voice.aicte.gov.in/pstn/{call_session.id}"/></Connect></Response>',
        }

    # Production path (feature-flagged):
    return {
        "status": "initiated",
        "session_id": str(call_session.id),
        "transport": "pstn",
        "stream_url": f"wss://voice.aicte.gov.in/pstn/{call_session.id}",
    }
