import os
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.audit import append_audit_entry, verify_chain

SUPERUSER_DATABASE_URL = os.environ.get(
    "SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)


def test_verify_chain_passes_on_untampered_log(db_session):
    first = None
    for i in range(3):
        entry = append_audit_entry(
            db_session,
            action="instrument.created",
            entity_type="instrument",
            entity_id=str(uuid.uuid4()),
            after={"seq": i},
        )
        first = first or entry
    db_session.commit()

    # Anchored on the first row this test created, so pollution from other
    # test runs sharing this dev DB can't affect the result either way.
    result = verify_chain(db_session, from_id=first.id)
    assert result.ok is True
    assert result.broken_at_id is None


def test_tampering_with_a_row_is_detected(db_session):
    entry = append_audit_entry(
        db_session,
        action="instrument.created",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"amount": 100000},
    )
    append_audit_entry(
        db_session,
        action="instrument.verified",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"amount": 100000},
    )
    db_session.commit()

    # Sanity: the untampered chain verifies, anchored on this test's first row.
    assert verify_chain(db_session, from_id=entry.id).ok is True

    # Simulate an out-of-band tamper: the app's own DB role (fdr_app) cannot
    # do this — it lacks owner privilege on audit_log, which is the point.
    # Only a true DB-owner/superuser connection can disable the immutability
    # trigger, which is exactly the attacker model this test proves against:
    # even a privileged direct-DB tamper is caught by chain verification.
    superuser_engine = create_engine(SUPERUSER_DATABASE_URL, future=True)
    with superuser_engine.begin() as conn:
        conn.execute(text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update"))
        conn.execute(
            text("UPDATE audit_log SET after = :payload WHERE id = :id"),
            {"payload": '{"amount": 999999999}', "id": entry.id},
        )
        conn.execute(text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_update"))
    superuser_engine.dispose()

    result = verify_chain(db_session, from_id=entry.id)
    assert result.ok is False
    assert result.broken_at_id == entry.id


def test_immutability_trigger_blocks_update_by_default(db_session):
    entry = append_audit_entry(
        db_session,
        action="instrument.created",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"amount": 1},
    )
    db_session.commit()

    with pytest.raises(DBAPIError, match="append-only"):
        db_session.execute(
            text("UPDATE audit_log SET action = 'x' WHERE id = :id"), {"id": entry.id}
        )
    db_session.rollback()


def test_immutability_trigger_blocks_delete_by_default(db_session):
    entry = append_audit_entry(
        db_session,
        action="instrument.created",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"amount": 1},
    )
    db_session.commit()

    with pytest.raises(DBAPIError, match="append-only"):
        db_session.execute(
            text("DELETE FROM audit_log WHERE id = :id"), {"id": entry.id}
        )
    db_session.rollback()
