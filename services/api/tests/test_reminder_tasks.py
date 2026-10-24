import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.db import SessionLocal
from app.models import Institution, Instrument
from app.models.enums import InstrumentStatus, InstrumentType
from app.reminders.tasks import process_reminder_ladder


def test_process_reminder_ladder_runs_end_to_end_and_is_idempotent(db_session):
    inst = Institution(
        aicte_code=f"TASK-{uuid.uuid4().hex[:8]}", name="Task Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-TASK-{uuid.uuid4().hex[:6]}",
        amount=500000,
        status=InstrumentStatus.ACTIVE,
        maturity_date=datetime.now(UTC) + timedelta(days=85),
    )
    db_session.add(instrument)
    db_session.commit()  # the task uses its own session/connection — must actually be committed to be visible

    try:
        first = process_reminder_ladder()
        assert first["reminders_created"] >= 1
        assert first["transitions_applied"] >= 1

        second = process_reminder_ladder()
        assert (
            second["reminders_created"] == 0
        )  # idempotent: same instrument, same window, no dupes
    finally:
        # This task commits via its own session, bypassing db_session's
        # rollback-based cleanup — clean up explicitly so this test
        # doesn't leak committed rows into the rest of the suite.
        # audit_log is append-only (Phase 2's immutability trigger) and
        # FK-references institutions, so the institution (and, by
        # extension, anything it owns) can never be deleted once it has
        # audit history — a correct consequence of a real audit trail,
        # not a test bug. Only clean up the leaf-level mutable rows;
        # leave institution/instrument/audit_log as permanent, harmless
        # artifacts of having run this test, same as every other test
        # that calls db_session.commit() already does.
        cleanup = SessionLocal()
        cleanup.execute(text("SELECT set_config('app.role', 'bureau_admin', true)"))
        cleanup.execute(
            text("DELETE FROM notification_log WHERE instrument_id = :id"),
            {"id": str(instrument.id)},
        )
        cleanup.execute(
            text("DELETE FROM reminders WHERE instrument_id = :id"),
            {"id": str(instrument.id)},
        )
        cleanup.commit()
        cleanup.close()
