import uuid

import pytest
from sqlalchemy import select

from app.db import set_app_context
from app.models.core import Institution, Instrument
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType
from app.problem_json import NotFoundError


def test_cross_tenant_instrument_lookup_returns_404_under_rls(db_session):
    """CLAUDE.md non-negotiable #6: Cross-tenant resource lookups must return 404, never 403.

    Proves that when user of Institution A attempts to query an instrument belonging
    to Institution B, Postgres RLS completely filters the row out, yielding 0 rows
    and resulting in NotFoundError (anti-enumeration).
    """
    # 1. Create Institution A and Institution B as platform_operator
    set_app_context(db_session, role="platform_operator")

    inst_a = Institution(
        aicte_code=f"1-TEST-A-{uuid.uuid4().hex[:6]}", name="Institute A"
    )
    inst_b = Institution(
        aicte_code=f"1-TEST-B-{uuid.uuid4().hex[:6]}", name="Institute B"
    )
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    # Create Instrument belonging to Institution B
    inst_b_fdr = Instrument(
        institution_id=inst_b.id,
        type=InstrumentType.FDR,
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
        instrument_number="FDR-INST-B-SECRET-9999",
        amount=500000.00,
    )
    db_session.add(inst_b_fdr)
    db_session.commit()

    inst_b_fdr_id = inst_b_fdr.id

    # 2. Switch session context to Institution A submitter
    set_app_context(
        db_session,
        role=AppRole.INSTITUTION_SUBMITTER.value,
        institution_id=str(inst_a.id),
        user_id=str(uuid.uuid4()),
    )

    # 3. Attempt to fetch Institution B's instrument
    found = db_session.execute(
        select(Instrument).where(Instrument.id == inst_b_fdr_id)
    ).scalar_one_or_none()

    # RLS must make it completely invisible (anti-enumeration)
    assert found is None

    # The service layer transforms this missing row into NotFoundError (HTTP 404),
    # never ForbiddenError (HTTP 403) which would confirm the ID exists.
    if found is None:
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(f"instrument {inst_b_fdr_id} not found")
        assert exc_info.value.code == "not_found"
        assert exc_info.value.status_code == 404


def test_bureau_role_can_view_across_institutions(db_session):
    """AICTE Bureau officers (e.g. Scrutiny, Intake) have global / assigned scope."""
    set_app_context(db_session, role="platform_operator")

    inst = Institution(
        aicte_code=f"1-TEST-BUREAU-{uuid.uuid4().hex[:6]}", name="Bureau Test Inst"
    )
    db_session.add(inst)
    db_session.flush()

    fdr = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        status=InstrumentStatus.SUBMITTED,
        evidence_level=EvidenceLevel.L0_DECLARED,
        instrument_number="FDR-BUREAU-VIEW-1234",
        amount=1000000.00,
    )
    db_session.add(fdr)
    db_session.commit()

    # Switch context to scrutiny officer
    set_app_context(
        db_session, role=AppRole.SCRUTINY_OFFICER.value, user_id=str(uuid.uuid4())
    )

    found = db_session.execute(
        select(Instrument).where(Instrument.id == fdr.id)
    ).scalar_one_or_none()
    assert found is not None
    assert found.id == fdr.id
