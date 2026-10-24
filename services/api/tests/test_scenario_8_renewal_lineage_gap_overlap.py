"""SPEC §18.1 Scenario 8 / PS Scenario: Renewal and Replacement Lineage.

Scenario 8 Requirements:
1. Renewal/replacement produces a linked record (instrument_lineage).
2. Old instrument remains historically complete and queryable.
3. Date gap/overlap requires explicit policy handling:
   - If successor issue date > predecessor maturity date: gap days computed.
     If gap > allowed, automatically flags discrepancy and creates draft observation.
   - If successor issue date < predecessor maturity date: overlap days computed.
4. Old instrument transitions to SUPERSEDED only when new instrument reaches
   ACTIVE_TRACKING under approved checks.
5. DAG cycles (self-link or circular dependencies like A -> B -> A) are strictly rejected.
"""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.lifecycle import apply_transition
from app.models.core import (
    AppUser,
    Discrepancy,
    Institution,
    Instrument,
    ScrutinyObservation,
)
from app.models.enums import AppRole, InstrumentStatus, InstrumentType
from app.renewals.service import (
    LineageCycleError,
    create_instrument_lineage,
    get_lineage_graph,
    on_successor_reaches_active,
)


def _setup_institution_and_officer(db_session):
    inst = Institution(
        aicte_code=f"SCEN8-{uuid.uuid4().hex[:8]}",
        name="Scenario 8 Engineering College",
    )
    db_session.add(inst)
    db_session.flush()

    officer = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"scrutiny-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="Scrutiny Officer S8",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    db_session.add(officer)
    db_session.flush()

    return inst, officer


def _make_instrument(db_session, inst, *, number, issue_date, maturity_date, status=InstrumentStatus.MATURED):
    inst_rec = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=number,
        amount=2500000.0,
        status=status,
        issue_date=issue_date,
        maturity_date=maturity_date,
        tenor_months=36,
    )
    db_session.add(inst_rec)
    db_session.flush()
    return inst_rec


def test_scenario_8_renewal_lineage_linkage_and_history_preserved(db_session, clock):
    """SPEC F-11: Both records remain queryable; lineage graph visual on web and mobile."""
    inst, officer = _setup_institution_and_officer(db_session)
    now = clock.now()

    # Predecessor: issued 3 years ago, matured today
    inst_a = _make_instrument(
        db_session, inst,
        number="FDR-PRED-001",
        issue_date=now - timedelta(days=365 * 3),
        maturity_date=now,
        status=InstrumentStatus.MATURED,
    )

    # Successor renewal: issued today, matures in 3 years
    inst_b = _make_instrument(
        db_session, inst,
        number="FDR-SUCC-002",
        issue_date=now,
        maturity_date=now + timedelta(days=365 * 3),
        status=InstrumentStatus.SUBMITTED,
    )

    # Create lineage link
    lineage = create_instrument_lineage(
        db_session,
        predecessor_id=inst_a.id,
        successor_id=inst_b.id,
        relationship_type="RENEWAL",
        policy_allowed_gap_days=0,
        created_by=officer,
    )

    assert lineage is not None
    assert lineage.gap_days == 0
    assert lineage.overlap_days == 0
    assert lineage.is_gap_discrepancy is False

    # Historical record is preserved and queryable
    reloaded_a = db_session.get(Instrument, inst_a.id)
    assert reloaded_a is not None
    assert reloaded_a.instrument_number == "FDR-PRED-001"
    assert reloaded_a.status == InstrumentStatus.MATURED

    # Graph endpoint returns connected DAG
    graph = get_lineage_graph(db_session, inst_a.id)
    assert graph["instrument_id"] == str(inst_a.id)
    assert len(graph["successors"]) == 1
    assert graph["successors"][0]["instrument_number"] == "FDR-SUCC-002"


def test_scenario_8_gap_exceeding_policy_creates_discrepancy_and_observation(db_session, clock):
    """SPEC F-11: policy handles gap/overlap (observation if gap > allowed)."""
    inst, officer = _setup_institution_and_officer(db_session)
    now = clock.now()

    # Predecessor matured 45 days ago
    inst_a = _make_instrument(
        db_session, inst,
        number="FDR-GAP-OLD",
        issue_date=now - timedelta(days=365 * 3),
        maturity_date=now - timedelta(days=45),
        status=InstrumentStatus.MATURED,
    )

    # Successor issued today (45 days gap!)
    inst_b = _make_instrument(
        db_session, inst,
        number="FDR-GAP-NEW",
        issue_date=now,
        maturity_date=now + timedelta(days=365 * 3),
        status=InstrumentStatus.SUBMITTED,
    )

    # Link with policy limit of 15 days
    lineage = create_instrument_lineage(
        db_session,
        predecessor_id=inst_a.id,
        successor_id=inst_b.id,
        relationship_type="RENEWAL",
        policy_allowed_gap_days=15,
        created_by=officer,
    )

    assert lineage.gap_days == 45
    assert lineage.overlap_days == 0
    assert lineage.is_gap_discrepancy is True

    # Check Discrepancy was automatically raised
    disc = db_session.execute(
        select(Discrepancy).where(Discrepancy.instrument_id == inst_b.id)
    ).scalar_one()
    assert disc.field == "renewal_gap_days"
    assert disc.severity == "HIGH"
    assert disc.status == "open"

    # Check ScrutinyObservation was created
    obs = db_session.execute(
        select(ScrutinyObservation).where(ScrutinyObservation.instrument_id == inst_b.id)
    ).scalar_one()
    assert "45 days detected" in obs.observation
    assert obs.status == "OPEN"


def test_scenario_8_date_overlap_calculated_correctly(db_session, clock):
    """SPEC F-11: overlap calculation when new instrument is issued before old matures."""
    inst, officer = _setup_institution_and_officer(db_session)
    now = clock.now()

    # Predecessor matures in 30 days
    inst_a = _make_instrument(
        db_session, inst,
        number="FDR-OVERLAP-OLD",
        issue_date=now - timedelta(days=365 * 3),
        maturity_date=now + timedelta(days=30),
        status=InstrumentStatus.EXPIRING,
    )

    # Successor issued today (30 days overlap)
    inst_b = _make_instrument(
        db_session, inst,
        number="FDR-OVERLAP-NEW",
        issue_date=now,
        maturity_date=now + timedelta(days=365 * 3),
        status=InstrumentStatus.SUBMITTED,
    )

    lineage = create_instrument_lineage(
        db_session,
        predecessor_id=inst_a.id,
        successor_id=inst_b.id,
        relationship_type="RENEWAL",
        policy_allowed_gap_days=0,
        created_by=officer,
    )

    assert lineage.gap_days == 0
    assert lineage.overlap_days == 30
    assert lineage.is_gap_discrepancy is False


def test_scenario_8_old_instrument_superseded_only_when_new_reaches_active(db_session, clock):
    """SPEC F-11: old instrument transitions SUPERSEDED only when the new one
    reaches ACTIVE_TRACKING under the approved checks.
    """
    inst, officer = _setup_institution_and_officer(db_session)
    now = clock.now()

    inst_old = _make_instrument(
        db_session, inst,
        number="FDR-OLD-001",
        issue_date=now - timedelta(days=365 * 3),
        maturity_date=now,
        status=InstrumentStatus.MATURED,
    )

    inst_new = _make_instrument(
        db_session, inst,
        number="FDR-NEW-002",
        issue_date=now,
        maturity_date=now + timedelta(days=365 * 3),
        status=InstrumentStatus.SUBMITTED,
    )

    create_instrument_lineage(db_session, inst_old.id, inst_new.id, created_by=officer)

    # While new instrument is SUBMITTED or INTAKE_REVIEW, old instrument stays MATURED
    assert inst_old.status == InstrumentStatus.MATURED

    # Move new instrument through lifecycle: SUBMITTED -> INTAKE_REVIEW -> SCRUTINY -> ACTIVE_TRACKING
    apply_transition(db_session, inst_new, InstrumentStatus.INTAKE_REVIEW, actor_role=AppRole.INTAKE_OFFICER.value, actor_id=str(officer.id), reason="Intake passed")
    apply_transition(db_session, inst_new, InstrumentStatus.SCRUTINY, actor_role=AppRole.SCRUTINY_OFFICER.value, actor_id=str(officer.id), reason="Scrutiny review complete")
    apply_transition(db_session, inst_new, InstrumentStatus.ACTIVE_TRACKING, actor_role=AppRole.REGIONAL_SUPERVISOR.value, actor_id=str(officer.id), reason="Active tracking approved")

    # Successor reached ACTIVE_TRACKING: trigger lineage hook
    superseded = on_successor_reaches_active(db_session, inst_new, actor_role="system")

    assert len(superseded) == 1
    assert superseded[0].id == inst_old.id
    assert inst_old.status == InstrumentStatus.SUPERSEDED


def test_scenario_8_dag_cycle_rejection(db_session, clock):
    """SPEC §18.1 Scenario 8 & F-11: cycles and orphans rejected at DB/service level."""
    inst, officer = _setup_institution_and_officer(db_session)
    now = clock.now()

    inst_a = _make_instrument(db_session, inst, number="FDR-DAG-A", issue_date=now, maturity_date=now + timedelta(days=365))
    inst_b = _make_instrument(db_session, inst, number="FDR-DAG-B", issue_date=now, maturity_date=now + timedelta(days=365))
    inst_c = _make_instrument(db_session, inst, number="FDR-DAG-C", issue_date=now, maturity_date=now + timedelta(days=365))

    # Self-link rejection (A -> A)
    with pytest.raises(LineageCycleError):
        create_instrument_lineage(db_session, inst_a.id, inst_a.id, created_by=officer)

    # Link A -> B
    create_instrument_lineage(db_session, inst_a.id, inst_b.id, created_by=officer)

    # Link B -> C
    create_instrument_lineage(db_session, inst_b.id, inst_c.id, created_by=officer)

    # Cycle attempt: C -> A must be strictly rejected
    with pytest.raises(LineageCycleError) as exc:
        create_instrument_lineage(db_session, inst_c.id, inst_a.id, created_by=officer)
    assert "circular dependency" in str(exc.value)

    # Direct reverse attempt: B -> A must be strictly rejected
    with pytest.raises(LineageCycleError) as exc:
        create_instrument_lineage(db_session, inst_b.id, inst_a.id, created_by=officer)
    assert "circular dependency" in str(exc.value)
