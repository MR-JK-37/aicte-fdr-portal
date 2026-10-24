import uuid

from sqlalchemy import select

from app.models import Institution, Instrument
from app.models.enums import InstrumentType
from tests.conftest import session_as


def test_cross_tenant_instrument_read_is_blocked(engine, db_session):
    inst_a = Institution(aicte_code=f"A-{uuid.uuid4().hex[:8]}", name="Institution A")
    inst_b = Institution(aicte_code=f"B-{uuid.uuid4().hex[:8]}", name="Institution B")
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    instrument_a = Instrument(
        institution_id=inst_a.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-A-001",
        amount=100000,
    )
    instrument_b = Instrument(
        institution_id=inst_b.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-B-001",
        amount=200000,
    )
    db_session.add_all([instrument_a, instrument_b])
    db_session.commit()

    # Institution A's own session must see only its own instrument.
    session_a = session_as(engine, "institution", institution_id=str(inst_a.id))
    try:
        visible = session_a.execute(select(Instrument)).scalars().all()
        assert [i.instrument_number for i in visible] == ["FDR-A-001"]

        # A direct lookup by B's instrument id must also return nothing —
        # this is the IDOR-style check, not just the listing view.
        leaked = session_a.execute(
            select(Instrument).where(Instrument.id == instrument_b.id)
        ).scalar_one_or_none()
        assert leaked is None
    finally:
        session_a.rollback()
        session_a.close()

    # Institution B's own session must see only its own instrument.
    session_b = session_as(engine, "institution", institution_id=str(inst_b.id))
    try:
        visible = session_b.execute(select(Instrument)).scalars().all()
        assert [i.instrument_number for i in visible] == ["FDR-B-001"]
    finally:
        session_b.rollback()
        session_b.close()

    # Bureau-side roles see both, by design.
    session_bureau = session_as(engine, "scrutiny_officer")
    try:
        visible = session_bureau.execute(select(Instrument)).scalars().all()
        numbers = {i.instrument_number for i in visible}
        assert {"FDR-A-001", "FDR-B-001"} <= numbers
    finally:
        session_bureau.rollback()
        session_bureau.close()


def test_institution_without_context_sees_nothing(engine, db_session):
    inst = Institution(aicte_code=f"C-{uuid.uuid4().hex[:8]}", name="Institution C")
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-C-001",
        amount=1,
    )
    db_session.add(instrument)
    db_session.commit()

    # 'institution' role with no institution_id set must see nothing —
    # RLS must fail closed, not open.
    bare_session = session_as(engine, "institution", institution_id=None)
    try:
        visible = bare_session.execute(select(Instrument)).scalars().all()
        assert visible == []
    finally:
        bare_session.rollback()
        bare_session.close()
