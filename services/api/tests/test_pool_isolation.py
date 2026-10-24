import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import settings
from app.db import set_app_context
from app.models.core import Institution, Instrument
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType


def test_connection_pool_size_1_isolation_and_missing_context_zero_rows():
    """MASTER_PROMPT §4 spike S-05 & §8.5: Connection pool context isolation test.

    Uses pool_size=1, max_overflow=0 so every session reuses the exact same physical
    PostgreSQL connection.
    Proves:
    1. Tenant A session sees only Tenant A rows.
    2. Tenant B session sees only Tenant B rows (Tenant A rows do not leak across pool reuse).
    3. Session with missing/unauthenticated context sees 0 rows (default deny).
    """
    # Create engine strictly with pool_size=1, max_overflow=0
    pool_engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        future=True,
    )
    SessionFactory = sessionmaker(bind=pool_engine, future=True, expire_on_commit=False)

    # 1. Setup Tenant A and Tenant B records using platform_operator
    with SessionFactory() as setup_session:
        set_app_context(setup_session, role="platform_operator")
        inst_a = Institution(
            aicte_code=f"1-POOL-A-{uuid.uuid4().hex[:6]}", name="Tenant A"
        )
        inst_b = Institution(
            aicte_code=f"1-POOL-B-{uuid.uuid4().hex[:6]}", name="Tenant B"
        )
        setup_session.add_all([inst_a, inst_b])
        setup_session.flush()

        inst_a_id = inst_a.id
        inst_b_id = inst_b.id

        fdr_a = Instrument(
            institution_id=inst_a_id,
            type=InstrumentType.FDR,
            status=InstrumentStatus.ACTIVE,
            evidence_level=EvidenceLevel.L2_BANK_CONFIRMED,
            instrument_number="FDR-A-100",
            amount=100000.00,
        )
        fdr_b = Instrument(
            institution_id=inst_b_id,
            type=InstrumentType.FDR,
            status=InstrumentStatus.ACTIVE,
            evidence_level=EvidenceLevel.L2_BANK_CONFIRMED,
            instrument_number="FDR-B-200",
            amount=200000.00,
        )
        setup_session.add_all([fdr_a, fdr_b])
        setup_session.commit()

    # 2. Query as Tenant A (physical connection checkout 1)
    with SessionFactory() as session_a:
        set_app_context(
            session_a,
            role=AppRole.INSTITUTION_SUBMITTER.value,
            institution_id=str(inst_a_id),
            user_id=str(uuid.uuid4()),
        )
        instruments_a = session_a.execute(select(Instrument)).scalars().all()
        # Must see only Tenant A's instrument
        assert len(instruments_a) == 1
        assert instruments_a[0].institution_id == inst_a_id
        assert instruments_a[0].instrument_number == "FDR-A-100"

    # Connection returned to pool

    # 3. Query as Tenant B on the REUSED physical connection (checkout 2)
    with SessionFactory() as session_b:
        set_app_context(
            session_b,
            role=AppRole.INSTITUTION_SUBMITTER.value,
            institution_id=str(inst_b_id),
            user_id=str(uuid.uuid4()),
        )
        instruments_b = session_b.execute(select(Instrument)).scalars().all()
        # Must see only Tenant B's instrument — zero leakage from Tenant A!
        assert len(instruments_b) == 1
        assert instruments_b[0].institution_id == inst_b_id
        assert instruments_b[0].instrument_number == "FDR-B-200"

    # Connection returned to pool

    # 4. Query with MISSING context on the REUSED physical connection (checkout 3)
    with SessionFactory() as unauthed_session:
        # No set_app_context called — default empty GUCs
        instruments_unauthed = (
            unauthed_session.execute(select(Instrument)).scalars().all()
        )
        # RLS must default deny: 0 rows returned!
        assert len(instruments_unauthed) == 0

    pool_engine.dispose()
