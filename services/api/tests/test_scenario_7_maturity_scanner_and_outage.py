"""SPEC §18.1 Scenario 7 / PS Scenarios: Validity Tracking & Approaching Maturity.

Scenario 7 Requirements:
1. No approved schedule => explicit admin alert, records 'skipped: no approved schedule',
   never invents reminders.
2. Maturity scanner runs twice and creates exactly one logical reminder per schedule key (idempotency).
3. Transitions: ACTIVE -> EXPIRING at 90 days, EXPIRING -> MATURED when date reached.
4. Scheduler outage is detectable (stale heartbeat -> OUTAGE_ALERT) and recoverable on restart.
5. Overdue escalation exposes/reassigns to supervisors; never auto-rejects or releases.
"""

import uuid
from datetime import timedelta

from sqlalchemy import select

from app.models.core import (
    AppUser,
    Institution,
    Instrument,
    Reminder,
    ScrutinyObservation,
)
from app.models.enums import AppRole, InstrumentStatus, InstrumentType
from app.models.workflow import BankConfirmationRequest, PolicyVersion, SchedulerRun
from app.reminders.scheduler import (
    acquire_scheduler_lease,
    check_scheduler_health,
    run_scheduler,
)


def _create_institution_and_instrument(db_session, clock, days_to_maturity=85, status=InstrumentStatus.ACTIVE):
    inst = Institution(
        aicte_code=f"SCEN7-{uuid.uuid4().hex[:8]}",
        name="Scenario 7 Test Technical Institute",
    )
    db_session.add(inst)
    db_session.flush()

    as_of = clock.now()
    maturity = as_of + timedelta(days=days_to_maturity)

    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-S7-{uuid.uuid4().hex[:6]}",
        amount=1500000.0,
        status=status,
        issue_date=as_of - timedelta(days=365 * 3),
        maturity_date=maturity,
        tenor_months=36,
    )
    db_session.add(instrument)
    db_session.flush()
    return inst, instrument


def test_scenario_7_no_approved_schedule_raises_admin_alert_and_skips(db_session, clock):
    """SPEC F-10: No approved schedule => no invented one.
    Dashboard shows admin alert 'Reminder schedule not approved' and
    the scanner records 'skipped: no approved schedule'.
    """
    _, instrument = _create_institution_and_instrument(db_session, clock, days_to_maturity=60)

    # Clean up any approved reminder schedule
    existing_policies = db_session.execute(
        select(PolicyVersion).where(PolicyVersion.policy_id == "REMINDER-SCHEDULE")
    ).scalars().all()
    for p in existing_policies:
        db_session.delete(p)
    db_session.flush()

    # Run scheduler requiring approved schedule with example schedule disallowed
    result = run_scheduler(
        db_session,
        clock,
        require_approved_schedule=True,
        allow_example_schedule=False,
    )

    assert result.skipped is True
    assert result.reason == "skipped: no approved schedule"
    assert result.admin_alert == "Reminder schedule not approved"
    assert len(result.reminders_created) == 0

    # Ensure zero reminders were invented in the database
    reminders = db_session.execute(
        select(Reminder).where(Reminder.instrument_id == instrument.id)
    ).scalars().all()
    assert len(reminders) == 0


def test_scenario_7_maturity_scanner_idempotency_and_transitions(db_session, clock):
    """SPEC §18.1 Scenario 7:
    Maturity scanner runs twice and creates one logical reminder per schedule key;
    advances instrument from ACTIVE -> EXPIRING at T-90, and EXPIRING -> MATURED at T-0.
    """
    _, instrument = _create_institution_and_instrument(db_session, clock, days_to_maturity=85)

    # First run: approaching maturity (85 days left -> T-90 due)
    first_result = run_scheduler(db_session, clock)
    assert first_result.skipped is False
    assert instrument.status == InstrumentStatus.EXPIRING
    assert any(r.instrument_id == instrument.id and r.window == "T-90" for r in first_result.reminders_created)

    # Second run immediately after: must be completely idempotent (0 duplicate reminders)
    second_result = run_scheduler(db_session, clock)
    assert second_result.skipped is False
    assert len([r for r in second_result.reminders_created if r.instrument_id == instrument.id]) == 0

    # Verify DB row count is strictly 1
    stored_reminders = db_session.execute(
        select(Reminder).where(Reminder.instrument_id == instrument.id)
    ).scalars().all()
    assert len(stored_reminders) == 1
    assert stored_reminders[0].window == "T-90"

    # Fast forward clock to maturity date (T-0)
    clock.advance(days=86)
    matured_result = run_scheduler(db_session, clock)

    assert instrument.status == InstrumentStatus.MATURED
    # Windows T-60, T-30, T-7, T-0 created (T-90 was already created)
    windows = {r.window for r in matured_result.reminders_created if r.instrument_id == instrument.id}
    assert windows == {"T-60", "T-30", "T-7", "T-0"}

    # Running third time after maturity must also be idempotent
    third_result = run_scheduler(db_session, clock)
    assert len([r for r in third_result.reminders_created if r.instrument_id == instrument.id]) == 0


def test_scenario_7_scheduler_outage_detection_and_recovery(db_session, clock):
    """SPEC §18.1 Scenario 7 & F-10:
    Scheduler outage is detectable by stale heartbeat and recovered by catch-up on restart.
    """
    scheduler_id = "maturity_lifecycle_scanner"

    # Worker 1 acquires lease
    now_utc = clock.now()
    run = acquire_scheduler_lease(db_session, scheduler_id=scheduler_id, worker_id="worker-node-1", as_of=now_utc)
    assert run.status == "RUNNING"
    assert run.leased_by == "worker-node-1"

    # Worker crashes: time advances 10 minutes (600s) without heartbeat
    dead_time = now_utc + timedelta(seconds=600)
    health = check_scheduler_health(db_session, scheduler_id=scheduler_id, max_stale_seconds=300, as_of=dead_time)

    assert health["healthy"] is False
    assert health["status"] == "OUTAGE_ALERT"
    assert "Scheduler outage detected" in str(health["alert"])

    # Worker 2 restarts and catches up: lease expired, acquires lease and executes
    worker2_result = run_scheduler(db_session, clock, worker_id="worker-node-2")
    assert worker2_result.skipped is False

    # Status is now IDLE, last_success_at recorded
    reloaded_run = db_session.execute(
        select(SchedulerRun).where(SchedulerRun.scheduler_id == scheduler_id)
    ).scalar_one()
    assert reloaded_run.status == "IDLE"
    assert reloaded_run.last_success_at is not None


def test_scenario_7_overdue_obligations_escalation_does_not_alter_business_state(db_session, clock):
    """SPEC F-10:
    Overdue escalation reassigns/exposes to supervisors only;
    it never rejects, forfeits or releases.
    """
    inst, instrument = _create_institution_and_instrument(db_session, clock, days_to_maturity=200)
    as_of = clock.now()

    # 1. Overdue bank confirmation request (10 days old, awaiting response)
    officer = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"officer-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="Scrutiny Officer",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    db_session.add(officer)
    db_session.flush()

    bcr = BankConfirmationRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        bank_name="State Bank of India",
        tracking_number=f"TRK-{uuid.uuid4().hex[:8]}",
        status="AWAITING_RESPONSE",
        requested_by=officer.id,
        requested_at=as_of - timedelta(days=10),
    )
    db_session.add(bcr)

    # 2. Overdue scrutiny observation (20 days old, awaiting institution)
    obs = ScrutinyObservation(
        institution_id=inst.id,
        instrument_id=instrument.id,
        officer_id=officer.id,
        observation="Amount mismatch on submitted FDR certificate",
        status="AWAITING_INSTITUTION",
        created_at=as_of - timedelta(days=20),
    )
    db_session.add(obs)
    db_session.flush()

    # Run scheduler
    result = run_scheduler(db_session, clock)

    # Escalations created to regional_supervisor
    levels = {e.level for e in result.escalations_created if e.instrument_id == instrument.id}
    assert "VERIFICATION_OVERDUE" in levels
    assert "OBSERVATION_OVERDUE" in levels

    # CRITICAL INVARIANT: Business states remained untouched
    assert bcr.status == "AWAITING_RESPONSE"  # Never auto-rejected
    assert obs.status == "AWAITING_INSTITUTION"  # Never auto-closed
    assert instrument.status == InstrumentStatus.ACTIVE  # Never auto-forfeited or released
