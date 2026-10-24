"""The reminder/escalation ladder: in-app -> FCM push (actions
Acknowledge / Snooze) -> email -> (production flag) PSTN/WhatsApp ->
Regulation Bureau. Each step escalates to the next only if the previous
one went unacknowledged for a clock-measured delay.

Delivery is idempotent (NotificationLog.idempotency_key, unique per
instrument+window+step — a re-run of the same scheduler tick for the
same due step is a no-op, not a duplicate send) and quiet-hours aware
for the channel that actually interrupts someone (push).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import Clock
from app.config import settings
from app.models.core import (
    AppUser,
    Escalation,
    Instrument,
    NotificationLog,
    Reminder,
)
from app.reminders import i18n
from app.reminders.email import send_email
from app.reminders.push import PushNotConfiguredError, send_push

LADDER_STEPS = ["in_app", "push", "email", "pstn_whatsapp", "regulation_bureau"]

# Days to wait at each step before escalating to the next one.
STEP_ESCALATION_DELAY_DAYS = {
    "in_app": 1,
    "push": 1,
    "email": 2,
    "pstn_whatsapp": 2,
    "regulation_bureau": 0,  # terminal step — nothing after it
}


@dataclass
class LadderStepResult:
    reminder_id: str
    step: str
    sent: bool
    reason: str


def _in_quiet_hours(user: AppUser, as_of: datetime) -> bool:
    hour = as_of.hour
    start, end = user.quiet_hours_start, user.quiet_hours_end
    if start == end:
        return False  # zero-width window: quiet hours disabled, not "always quiet"
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end  # wraps past midnight


def _institution_contacts(session: Session, institution_id) -> list[AppUser]:
    from app.models.enums import AppRole

    return list(
        session.execute(
            select(AppUser).where(
                AppUser.institution_id == institution_id,
                AppUser.role == AppRole.INSTITUTION_SUBMITTER,
            )
        )
        .scalars()
        .all()
    )


def _log_notification(
    session: Session,
    *,
    reminder: Reminder,
    channel: str,
    template: str,
    payload: dict,
    app_user_id=None,
) -> bool:
    """Returns False (no-op) if this exact step was already logged for
    this reminder — the idempotency the brief requires."""
    idempotency_key = f"{reminder.instrument_id}:{reminder.window}:{channel}"
    existing = session.execute(
        select(NotificationLog).where(
            NotificationLog.idempotency_key == idempotency_key
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    session.add(
        NotificationLog(
            institution_id=reminder.institution_id,
            app_user_id=app_user_id,
            instrument_id=reminder.instrument_id,
            channel=channel,
            template=template,
            payload=payload,
            status="sent",
            idempotency_key=idempotency_key,
        )
    )
    return True


def _execute_step(
    session: Session,
    reminder: Reminder,
    instrument: Instrument,
    step: str,
    as_of: datetime,
) -> LadderStepResult:
    contacts = _institution_contacts(session, reminder.institution_id)
    primary = contacts[0] if contacts else None
    language = primary.preferred_language if primary else i18n.DEFAULT_LANGUAGE

    message = i18n.render(
        "reminder.maturity_window",
        language,
        instrument_number=instrument.instrument_number,
        amount=str(instrument.amount),
        window_label=i18n.window_label(reminder.window, language),
    )

    if step == "in_app":
        logged = _log_notification(
            session,
            reminder=reminder,
            channel="in_app",
            template="reminder.maturity_window",
            payload={"message": message},
            app_user_id=primary.id if primary else None,
        )
        return LadderStepResult(
            str(reminder.id), step, logged, "logged" if logged else "already sent"
        )

    if step == "push":
        if primary and _in_quiet_hours(primary, as_of):
            return LadderStepResult(str(reminder.id), step, False, "quiet hours")
        try:
            # No device token model wiring exists yet (no mobile client
            # has registered one) — real send path exists and is
            # exercised in tests with a stub token; a real token would
            # flow in via app.models.core.DeviceToken once Phase 9 wires
            # push registration.
            send_push(
                device_token="stub-device-token",
                title="Maturity reminder",
                body=message,
                high_priority=False,
            )
        except PushNotConfiguredError as exc:
            return LadderStepResult(str(reminder.id), step, False, str(exc))
        logged = _log_notification(
            session,
            reminder=reminder,
            channel="push",
            template="reminder.maturity_window",
            payload={"message": message},
            app_user_id=primary.id if primary else None,
        )
        return LadderStepResult(
            str(reminder.id), step, logged, "sent" if logged else "already sent"
        )

    if step == "email":
        if primary:
            send_email(
                to_address=primary.email,
                subject="AICTE Security Deposit — maturity reminder",
                body=message,
            )
        logged = _log_notification(
            session,
            reminder=reminder,
            channel="email",
            template="reminder.maturity_window",
            payload={"message": message},
            app_user_id=primary.id if primary else None,
        )
        return LadderStepResult(
            str(reminder.id), step, logged, "sent" if logged else "already sent"
        )

    if step == "pstn_whatsapp":
        if not settings.production_telephony_enabled:
            return LadderStepResult(
                str(reminder.id),
                step,
                False,
                "SIMULATED: PSTN/WhatsApp requires a licensed CPaaS + TRAI robocall intimation in production; disabled in this environment",
            )
        # Real production telephony is out of scope for this build —
        # see Blueprint.txt's zero-cost boundaries table.
        return LadderStepResult(
            str(reminder.id), step, False, "production telephony not implemented"
        )

    if step == "regulation_bureau":
        escalation_message = i18n.render(
            "escalation.regulation_bureau",
            language,
            instrument_number=instrument.instrument_number,
        )
        session.add(
            Escalation(
                institution_id=reminder.institution_id,
                instrument_id=reminder.instrument_id,
                level="regulation_bureau",
                escalated_to="Regulation Bureau",
                status="open",
            )
        )
        logged = _log_notification(
            session,
            reminder=reminder,
            channel="regulation_bureau",
            template="escalation.regulation_bureau",
            payload={"message": escalation_message},
        )
        return LadderStepResult(
            str(reminder.id), step, logged, "escalated" if logged else "already sent"
        )

    raise ValueError(f"unknown ladder step '{step}'")


def advance_ladder(
    session: Session, reminder: Reminder, clock: Clock
) -> LadderStepResult | None:
    """Runs the current (or, if its delay has elapsed, the next) ladder
    step for one reminder. Returns None if the reminder is acknowledged
    or the next step's delay hasn't elapsed yet (nothing to do)."""
    if reminder.acknowledged_at is not None:
        return None

    as_of = clock.now()
    instrument = session.get(Instrument, reminder.instrument_id)

    if reminder.last_step_at is not None:
        current_step = LADDER_STEPS[reminder.ladder_step]
        elapsed_days = (as_of - reminder.last_step_at).days
        if elapsed_days < STEP_ESCALATION_DELAY_DAYS[current_step]:
            return None
        if reminder.ladder_step >= len(LADDER_STEPS) - 1:
            return None  # terminal step already reached
        reminder.ladder_step += 1

    step = LADDER_STEPS[reminder.ladder_step]
    result = _execute_step(session, reminder, instrument, step, as_of)
    reminder.last_step_at = as_of
    reminder.status = step
    session.flush()
    return result


def acknowledge_reminder(session: Session, reminder: Reminder, clock: Clock) -> None:
    reminder.acknowledged_at = clock.now()
    reminder.status = "acknowledged"
    session.flush()
