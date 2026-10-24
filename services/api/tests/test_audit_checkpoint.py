import os
import uuid

from sqlalchemy import create_engine, text

from app.audit import (
    DEV_PUBLIC_KEY,
    DEV_SIGNING_KEY,
    append_audit_entry,
    create_checkpoint,
    verify_chain,
    verify_checkpoint,
)
from app.db import set_app_context

SUPERUSER_DATABASE_URL = os.environ.get(
    "SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)


def _reset_audit_tables(session=None):
    if session:
        session.rollback()
    engine = create_engine(SUPERUSER_DATABASE_URL, future=True)
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE audit_checkpoints, audit_log RESTART IDENTITY CASCADE")
        )
    engine.dispose()


def test_audit_hash_chain_and_signed_checkpoint(db_session):
    _reset_audit_tables(db_session)
    set_app_context(db_session, role="platform_operator")

    # Create 3 audit entries
    e1 = append_audit_entry(
        db_session,
        action="instrument.create_draft",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"status": "draft", "amount": "100000.00"},
    )
    append_audit_entry(
        db_session,
        action="instrument.submit",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"status": "submitted"},
    )
    e3 = append_audit_entry(
        db_session,
        action="instrument.scrutiny",
        entity_type="instrument",
        entity_id=str(uuid.uuid4()),
        after={"status": "scrutiny"},
    )
    db_session.commit()

    # Verify hash chain
    chain_res = verify_chain(db_session)
    assert chain_res.ok is True
    assert chain_res.broken_at_id is None

    # Create a checkpoint
    checkpoint = create_checkpoint(db_session, signing_key=DEV_SIGNING_KEY)
    assert checkpoint is not None
    assert checkpoint.checkpoint_index == 1
    assert checkpoint.event_count == 3
    assert checkpoint.first_event_id == e1.id
    assert checkpoint.last_event_id == e3.id
    assert checkpoint.chain_root_hash == e3.row_hash
    db_session.commit()

    # Verify checkpoint signature
    assert verify_checkpoint(checkpoint, DEV_PUBLIC_KEY) is True

    # Tampering with checkpoint signature must fail verification
    checkpoint.signature = "aW52YWxpZC1zaWduYXR1cmU="
    assert verify_checkpoint(checkpoint, DEV_PUBLIC_KEY) is False


def test_tamper_detection_in_audit_chain(db_session):
    _reset_audit_tables(db_session)
    set_app_context(db_session, role="platform_operator")

    # Create 2 entries
    e1 = append_audit_entry(
        db_session,
        action="action_1",
        entity_type="type_1",
        entity_id="1",
        after={"val": 1},
    )
    e1_id = e1.id
    append_audit_entry(
        db_session,
        action="action_2",
        entity_type="type_2",
        entity_id="2",
        after={"val": 2},
    )
    db_session.commit()

    assert verify_chain(db_session).ok is True
    db_session.commit()

    # Tamper with row_hash of e1 directly (simulating out-of-band DB tamper)
    engine = create_engine(SUPERUSER_DATABASE_URL, future=True)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update"))
        conn.execute(
            text(
                "UPDATE audit_log SET row_hash = 'tampered_hash_value_12345678901234567890123456789012' WHERE id = :id"
            ),
            {"id": e1_id},
        )
        conn.execute(text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_update"))
    engine.dispose()

    # Chain verification MUST detect the tamper
    res = verify_chain(db_session)
    assert res.ok is False
    assert res.broken_at_id == e1_id

    # Reset audit tables so subsequent verifications start with a clean chain
    _reset_audit_tables(db_session)
