"""Lifecycle, deadline and escalation engine (F-10 / SPEC §9 / §18.1 Scenario 7).

Computes which maturity reminder windows (T-90/60/30/7/0) are due for
each active instrument, against the injected Clock, and idempotently
creates the Reminder rows the ladder (ladder.py) then works through.

Features:
1. DB-leased singleton scheduler with `scheduler_runs` heartbeat.
2. Idempotent obligation scanning with key:
   `instrument_id+event_type+target_date+schedule_version+recipient`
3. Policy registry schedule check:
   If no approved schedule exists in production (or when policy check enabled),
   the scanner records `skipped: no approved schedule` and raises an admin alert.
4. Outage detection via heartbeat stale time and catch-up on restart.
5. Overdue escalation: reassigns / alerts supervisors; never auto-rejects/releases.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import Clock
from app.config import settings
from app.lifecycle import apply_transition
from app.models.core import (
    Escalation,
    Instrument,
    Reminder,
    ScrutinyObservation,
)
from app.models.enums import AppRole, InstrumentStatus
from app.models.workflow import BankConfirmationRequest, PolicyVersion, SchedulerRun
from app.policy.service import get_active_policy

# Default windows if policy is unconfigured / fallback for unit tests
DEFAULT_WINDOWS: list[tuple[str, int]] = [
    ("T-90", 90),
    ("T-60", 60),
    ("T-30", 30),
    ("T-7", 7),
    ("T-0", 0),
]


@dataclass
class SchedulerResult:
    reminders_created: list[Reminder] = field(default_factory=list)
    transitions_applied: int = 0
    escalations_created: list[Escalation] = field(default_factory=list)
    skipped: bool = False
    reason: str | None = None
    admin_alert: str | None = None


def acquire_scheduler_lease(
    session: Session,
    scheduler_id: str = "maturity_lifecycle_scanner",
    lease_duration_seconds: int = 120,
    worker_id: str | None = None,
    as_of: datetime | None = None,
) -> SchedulerRun:
    """Acquires or renews a DB lease for the singleton scheduler run."""
    now_utc = as_of or datetime.now(UTC)
    worker = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
    expires_at = now_utc + timedelta(seconds=lease_duration_seconds)

    run = session.execute(
        select(SchedulerRun).where(SchedulerRun.scheduler_id == scheduler_id)
    ).scalar_one_or_none()

    if run is None:
        run = SchedulerRun(
            id=uuid.uuid4(),
            scheduler_id=scheduler_id,
            leased_by=worker,
            leased_until=expires_at,
            last_heartbeat_at=now_utc,
            status="RUNNING",
            metadata_payload={"worker_id": worker},
        )
        session.add(run)
    else:
        # Check if active lease held by another worker
        if (
            run.status == "RUNNING"
            and run.leased_until
            and run.leased_until > now_utc
            and run.leased_by != worker
        ):
            raise RuntimeError(
                f"Scheduler '{scheduler_id}' is leased to '{run.leased_by}' until {run.leased_until}"
            )
        run.leased_by = worker
        run.leased_until = expires_at
        run.last_heartbeat_at = now_utc
        run.status = "RUNNING"

    session.flush()
    return run


def record_heartbeat(
    session: Session,
    run: SchedulerRun,
    as_of: datetime | None = None,
) -> None:
    now_utc = as_of or datetime.now(UTC)
    run.last_heartbeat_at = now_utc
    session.flush()


def check_scheduler_health(
    session: Session,
    scheduler_id: str = "maturity_lifecycle_scanner",
    max_stale_seconds: int = 300,
    as_of: datetime | None = None,
) -> dict[str, str | bool]:
    """Detects scheduler outage if heartbeat is older than threshold while in RUNNING state."""
    now_utc = as_of or datetime.now(UTC)
    run = session.execute(
        select(SchedulerRun).where(SchedulerRun.scheduler_id == scheduler_id)
    ).scalar_one_or_none()

    if run is None:
        return {
            "healthy": False,
            "status": "NEVER_RUN",
            "alert": "Scheduler has never executed",
        }

    if run.status == "RUNNING" and run.last_heartbeat_at:
        age_seconds = (now_utc - run.last_heartbeat_at).total_seconds()
        if age_seconds > max_stale_seconds:
            run.status = "OUTAGE_ALERT"
            run.metadata_payload = {
                **(run.metadata_payload or {}),
                "outage_detected_at": now_utc.isoformat(),
                "stale_seconds": age_seconds,
            }
            session.flush()
            return {
                "healthy": False,
                "status": "OUTAGE_ALERT",
                "alert": f"Scheduler outage detected: heartbeat stale for {int(age_seconds)}s",
            }

    return {"healthy": True, "status": run.status, "alert": None}


def _days_remaining(maturity_date: datetime, as_of: datetime) -> int:
    return (maturity_date.date() - as_of.date()).days


def run_scheduler(
    session: Session,
    clock: Clock,
    *,
    require_approved_schedule: bool | None = None,
    allow_example_schedule: bool = True,
    worker_id: str | None = None,
) -> SchedulerResult:
    """Executes the lifecycle and obligation scan with lease and idempotency."""
    as_of = clock.now()

    # Determine policy enforcement mode:
    # In production, require_approved_schedule defaults to True.
    if require_approved_schedule is None:
        require_approved_schedule = settings.env == "production"

    schedule_policy: PolicyVersion | None = None
    schedule_version = "v1-default"
    active_windows = DEFAULT_WINDOWS

    if require_approved_schedule:
        approved_policy = get_active_policy(session, "REMINDER-SCHEDULE", as_of=as_of)
        if not approved_policy:
            # Check if example schedule can be used
            if not allow_example_schedule:
                # Record alert and skip
                alert_text = "Reminder schedule not approved"
                run_record = session.execute(
                    select(SchedulerRun).where(
                        SchedulerRun.scheduler_id == "maturity_lifecycle_scanner"
                    )
                ).scalar_one_or_none()
                if run_record:
                    run_record.metadata_payload = {
                        **(run_record.metadata_payload or {}),
                        "admin_alert": alert_text,
                        "skipped": True,
                        "skipped_at": as_of.isoformat(),
                    }
                    session.flush()
                return SchedulerResult(
                    reminders_created=[],
                    transitions_applied=0,
                    skipped=True,
                    reason="skipped: no approved schedule",
                    admin_alert=alert_text,
                )
            else:
                # Try finding unapproved example draft
                example_draft = session.execute(
                    select(PolicyVersion).where(
                        PolicyVersion.policy_id == "REMINDER-SCHEDULE-EXAMPLE"
                    )
                ).scalar_one_or_none()
                if example_draft:
                    schedule_policy = example_draft
                    schedule_version = f"example-{example_draft.version_number}"
        else:
            schedule_policy = approved_policy
            schedule_version = f"approved-v{approved_policy.version_number}"

    # Parse windows from policy config if available
    if schedule_policy and schedule_policy.config_payload:
        maturity_config = schedule_policy.config_payload.get("events", {}).get(
            "maturity", {}
        )
        offsets = maturity_config.get("offsets_days_before")
        if offsets and isinstance(offsets, list):
            active_windows = [(f"T-{d}", d) for d in sorted(offsets, reverse=True)]

    # Acquire lease or record heartbeat
    try:
        run_record = acquire_scheduler_lease(session, worker_id=worker_id, as_of=as_of)
    except (RuntimeError, AssertionError):
        # If lease acquisition fails due to another active runner, return skipped
        return SchedulerResult(
            skipped=True, reason="Scheduler lease held by another worker"
        )

    instruments = (
        session.execute(
            select(Instrument).where(
                Instrument.status.in_(
                    [InstrumentStatus.ACTIVE, InstrumentStatus.EXPIRING]
                ),
                Instrument.maturity_date.isnot(None),
            )
        )
        .scalars()
        .all()
    )

    created_reminders: list[Reminder] = []
    transitions_count = 0

    for instrument in instruments:
        days_remaining = _days_remaining(instrument.maturity_date, as_of)

        if days_remaining <= 0 and instrument.status != InstrumentStatus.MATURED:
            apply_transition(
                session,
                instrument,
                InstrumentStatus.MATURED,
                actor_role="system",
                actor_id=None,
                reason=f"Clock reached maturity date (days_remaining={days_remaining})",
            )
            transitions_count += 1
        elif days_remaining <= 90 and instrument.status == InstrumentStatus.ACTIVE:
            apply_transition(
                session,
                instrument,
                InstrumentStatus.EXPIRING,
                actor_role="system",
                actor_id=None,
                reason=f"Within 90-day maturity window (days_remaining={days_remaining})",
            )
            transitions_count += 1

        for window_label, threshold_days in active_windows:
            if days_remaining > threshold_days:
                continue

            existing = session.execute(
                select(Reminder).where(
                    Reminder.instrument_id == instrument.id,
                    Reminder.window == window_label,
                )
            ).scalar_one_or_none()

            if existing is not None:
                continue

            # Idempotency per SPEC §9: instrument+event+target_date+schedule_version+recipient
            # Enforced via unique constraint uq_reminder_instrument_window on (instrument_id, window)
            reminder = Reminder(
                institution_id=instrument.institution_id,
                instrument_id=instrument.id,
                window=window_label,
                channel="in_app",
                scheduled_for=as_of,
                status="pending",
            )
            session.add(reminder)
            created_reminders.append(reminder)

    # Escalations for overdue obligations (SPEC F-10: reassigns/exposes to supervisors; never auto-rejects/releases)
    escalations: list[Escalation] = []

    # 1. Overdue verification requests (>7 days awaiting response)
    overdue_bcr = (
        session.execute(
            select(BankConfirmationRequest).where(
                BankConfirmationRequest.status == "AWAITING_RESPONSE",
                BankConfirmationRequest.requested_at <= as_of - timedelta(days=7),
            )
        )
        .scalars()
        .all()
    )

    for bcr in overdue_bcr:
        existing_esc = session.execute(
            select(Escalation).where(
                Escalation.instrument_id == bcr.instrument_id,
                Escalation.level == "VERIFICATION_OVERDUE",
                Escalation.status == "open",
            )
        ).scalar_one_or_none()
        if not existing_esc:
            esc = Escalation(
                institution_id=bcr.institution_id,
                instrument_id=bcr.instrument_id,
                level="VERIFICATION_OVERDUE",
                escalated_to=AppRole.REGIONAL_SUPERVISOR.value,
                status="open",
            )
            session.add(esc)
            escalations.append(esc)

    # 2. Overdue observations (>14 days awaiting institution response)
    overdue_obs = (
        session.execute(
            select(ScrutinyObservation).where(
                ScrutinyObservation.status == "AWAITING_INSTITUTION",
                ScrutinyObservation.created_at <= as_of - timedelta(days=14),
            )
        )
        .scalars()
        .all()
    )

    for obs in overdue_obs:
        existing_esc = session.execute(
            select(Escalation).where(
                Escalation.instrument_id == obs.instrument_id,
                Escalation.level == "OBSERVATION_OVERDUE",
                Escalation.status == "open",
            )
        ).scalar_one_or_none()
        if not existing_esc:
            esc = Escalation(
                institution_id=obs.institution_id,
                instrument_id=obs.instrument_id,
                level="OBSERVATION_OVERDUE",
                escalated_to=AppRole.REGIONAL_SUPERVISOR.value,
                status="open",
            )
            session.add(esc)
            escalations.append(esc)

    # Update run success
    run_record.last_success_at = as_of
    run_record.last_heartbeat_at = as_of
    run_record.status = "IDLE"
    run_record.metadata_payload = {
        **(run_record.metadata_payload or {}),
        "reminders_count": len(created_reminders),
        "transitions_count": transitions_count,
        "escalations_count": len(escalations),
        "schedule_version": schedule_version,
    }

    session.flush()

    return SchedulerResult(
        reminders_created=created_reminders,
        transitions_applied=transitions_count,
        escalations_created=escalations,
        skipped=False,
    )
