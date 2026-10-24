import uuid

import pytest
from sqlalchemy import select

from app.audit import AuditLog
from app.lifecycle import (
    TRANSITIONS,
    IllegalTransitionError,
    UnauthorizedTransitionError,
    apply_transition,
    assert_transition_allowed,
)
from app.models import Institution, Instrument
from app.models.enums import AppRole, InstrumentStatus, InstrumentType

ALL_STATUSES = list(InstrumentStatus)


def _all_legal_edges():
    for from_status, edges in TRANSITIONS.items():
        for to_status, roles in edges.items():
            for role in roles:
                yield (from_status, to_status, role)


@pytest.mark.parametrize("from_status,to_status,role", list(_all_legal_edges()))
def test_every_defined_transition_is_allowed_for_its_role(from_status, to_status, role):
    # Must not raise.
    assert_transition_allowed(from_status, to_status, role)


@pytest.mark.parametrize("from_status,to_status,role", list(_all_legal_edges()))
def test_every_defined_transition_rejects_other_roles(from_status, to_status, role):
    other_roles = {r.value for r in AppRole} | {"system"}
    for wrong_role in other_roles - TRANSITIONS[from_status][to_status]:
        with pytest.raises(UnauthorizedTransitionError):
            assert_transition_allowed(from_status, to_status, wrong_role)


def test_all_undefined_transitions_are_illegal():
    """Exhaustively covers every (from, to) pair not explicitly whitelisted —
    the acceptance criterion is "server-side blocking of illegal
    transitions", so this must prove the complement of the allow-list,
    not just a couple of hand-picked examples."""
    checked = 0
    for from_status in ALL_STATUSES:
        for to_status in ALL_STATUSES:
            if to_status in TRANSITIONS.get(from_status, {}):
                continue
            checked += 1
            with pytest.raises(IllegalTransitionError):
                assert_transition_allowed(from_status, to_status, "bureau_admin")
    # Sanity: the state space is large enough that this is a real check,
    # not a vacuous loop.
    assert checked > 50


def test_apply_transition_requires_nonempty_reason(db_session):
    inst = Institution(
        aicte_code=f"L-{uuid.uuid4().hex[:8]}", name="Lifecycle Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-L-001",
        amount=1,
        status=InstrumentStatus.SUBMITTED,
    )
    db_session.add(instrument)
    db_session.flush()

    with pytest.raises(ValueError, match="reason"):
        apply_transition(
            db_session,
            instrument,
            InstrumentStatus.UNDER_SCRUTINY,
            actor_role="scrutiny_officer",
            actor_id=None,
            reason="   ",
        )


def test_apply_transition_writes_audit_entry_and_mutates_status(db_session):
    inst = Institution(
        aicte_code=f"M-{uuid.uuid4().hex[:8]}", name="Lifecycle Test Institution 2"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-M-001",
        amount=1,
        status=InstrumentStatus.SUBMITTED,
    )
    db_session.add(instrument)
    db_session.flush()

    result = apply_transition(
        db_session,
        instrument,
        InstrumentStatus.UNDER_SCRUTINY,
        actor_role="scrutiny_officer",
        actor_id=None,
        reason="Initial scrutiny assignment",
    )
    db_session.commit()

    assert result.from_status == InstrumentStatus.SUBMITTED
    assert result.to_status == InstrumentStatus.UNDER_SCRUTINY
    assert instrument.status == InstrumentStatus.UNDER_SCRUTINY

    entry = (
        db_session.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == "instrument",
                AuditLog.entity_id == str(instrument.id),
            )
            .order_by(AuditLog.id.desc())
        )
        .scalars()
        .first()
    )
    assert entry is not None
    assert entry.after["status"] == "UNDER_SCRUTINY"
    assert entry.after["reason"] == "Initial scrutiny assignment"


def test_apply_transition_rejects_unauthorized_role(db_session):
    inst = Institution(
        aicte_code=f"N-{uuid.uuid4().hex[:8]}", name="Lifecycle Test Institution 3"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number="FDR-N-001",
        amount=1,
        status=InstrumentStatus.SUBMITTED,
    )
    db_session.add(instrument)
    db_session.flush()

    with pytest.raises(UnauthorizedTransitionError):
        apply_transition(
            db_session,
            instrument,
            InstrumentStatus.UNDER_SCRUTINY,
            actor_role="institution",
            actor_id=None,
            reason="Attempting self-approval",
        )
    assert instrument.status == InstrumentStatus.SUBMITTED
