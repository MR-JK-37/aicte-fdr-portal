"""FCM push, via firebase-admin. Requires a Firebase project + service
account JSON — not configured in this build (no Firebase account set up
yet; see progress.md Phase 7). Fails closed and loud (raises
PushNotConfiguredError) rather than silently pretending to send, so the
ladder's caller can log the real reason a push step didn't happen
instead of a false "sent" status.

Once FIREBASE_SERVICE_ACCOUNT_JSON is set, this is real, not a mock:
firebase_admin.messaging.send() makes a genuine call to FCM.
"""

import json
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, messaging


class PushNotConfiguredError(Exception):
    pass


@lru_cache
def _app() -> firebase_admin.App:
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise PushNotConfiguredError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not set — no Firebase project configured"
        )
    cred = credentials.Certificate(json.loads(raw))
    return firebase_admin.initialize_app(cred, name="fdr-portal")


def send_push(
    *,
    device_token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    high_priority: bool = False,
) -> str:
    """Returns the FCM message ID on success. Raises PushNotConfiguredError
    if no Firebase project is set up, or firebase_admin's own exceptions
    on a real send failure (invalid/expired token, etc.) — never
    swallowed, since a silently-dropped maturity reminder is exactly the
    failure mode this ladder exists to prevent."""
    app = _app()
    message = messaging.Message(
        token=device_token,
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        android=messaging.AndroidConfig(priority="high" if high_priority else "normal"),
        apns=messaging.APNSConfig(
            headers={"apns-priority": "10" if high_priority else "5"},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(content_available=high_priority)
            ),
        ),
    )
    return messaging.send(message, app=app)
