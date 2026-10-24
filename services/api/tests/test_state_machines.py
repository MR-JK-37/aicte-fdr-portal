import uuid

import pytest
from sqlalchemy import select, text

from app.audit import AuditLog
from app.lifecycle import (
    DOCUMENT_TRANSITIONS,
    INSTRUMENT_TRANSITIONS,
    OBSERVATION_TRANSITIONS,
    IllegalTransitionError,
    apply_transition,
    assert_document_transition_allowed,
    assert_observation_transition_allowed,
    assert_transition_allowed,
)
from app.models import (
    Institution,
    Instrument,
    StateTransition,
)
from app.models.enums import (
    AppRole,
    DocumentStatus,
    InstrumentStatus,
    ObservationStatus,
)
from app.outbox.models import OutboxEvent


# ------------------------------------------------------------------------------
# Machine 1: Exhaustive Tests
# ------------------------------------------------------------------------------
def _all_instrument_legal_edges():
    for from_status, edges in INSTRUMENT_TRANSITIONS.items():
        for to_status, roles in edges.items():
            for role in roles:
                yield (from_status, to_status, role)


@pytest.mark.parametrize(
    "from_status,to_status,role", list(_all_instrument_legal_edges())
)
def test_instrument_every_defined_transition_is_allowed(from_status, to_status, role):
    assert_transition_allowed(from_status, to_status, role)


def test_instrument_undefined_transitions_are_illegal():
    all_statuses = list(InstrumentStatus)
    illegal_count = 0
    for from_status in all_statuses:
        for to_status in all_statuses:
            if to_status in INSTRUMENT_TRANSITIONS.get(from_status, {}):
                continue
            illegal_count += 1
            with pytest.raises(IllegalTransitionError):
                assert_transition_allowed(from_status, to_status, "platform_operator")
    assert illegal_count > 50


# ------------------------------------------------------------------------------
# Machine 3: Observation Exhaustive Tests
# ------------------------------------------------------------------------------
def _all_observation_legal_edges():
    for from_status, edges in OBSERVATION_TRANSITIONS.items():
        for to_status, roles in edges.items():
            for role in roles:
                yield (from_status, to_status, role)


@pytest.mark.parametrize(
    "from_status,to_status,role", list(_all_observation_legal_edges())
)
def test_observation_every_defined_transition_is_allowed(from_status, to_status, role):
    assert_observation_transition_allowed(from_status, to_status, role)


def test_observation_undefined_transitions_are_illegal():
    all_statuses = list(ObservationStatus)
    illegal_count = 0
    for from_status in all_statuses:
        for to_status in all_statuses:
            if to_status in OBSERVATION_TRANSITIONS.get(from_status, {}):
                continue
            illegal_count += 1
            with pytest.raises(IllegalTransitionError):
                assert_observation_transition_allowed(
                    from_status, to_status, "platform_operator"
                )
    assert illegal_count > 15


# ------------------------------------------------------------------------------
# Machine 7: Document Exhaustive Tests
# ------------------------------------------------------------------------------
def _all_document_legal_edges():
    for from_status, edges in DOCUMENT_TRANSITIONS.items():
        for to_status, roles in edges.items():
            for role in roles:
                yield (from_status, to_status, role)


@pytest.mark.parametrize(
    "from_status,to_status,role", list(_all_document_legal_edges())
)
def test_document_every_defined_transition_is_allowed(from_status, to_status, role):
    assert_document_transition_allowed(from_status, to_status, role)


def test_document_undefined_transitions_are_illegal():
    all_statuses = list(DocumentStatus)
    illegal_count = 0
    for from_status in all_statuses:
        for to_status in all_statuses:
            if to_status in DOCUMENT_TRANSITIONS.get(from_status, {}):
                continue
            illegal_count += 1
            with pytest.raises(IllegalTransitionError):
                assert_document_transition_allowed(
                    from_status, to_status, "platform_operator"
                )
    assert illegal_count > 10


# ------------------------------------------------------------------------------
# Atomicity: StateTransition + AuditLog + Outbox
# ------------------------------------------------------------------------------
def test_atomic_transition_writes_all_three_records(db_session):
    inst = Institution(aicte_code=f"AT-{uuid.uuid4().hex[:8]}", name="Atomic Test Inst")
    db_session.add(inst)
    db_session.flush()

    from app.models import AppUser

    user = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Atomic Actor",
        role=AppRole.INSTITUTION_SUBMITTER,
    )
    db_session.add(user)
    db_session.flush()

    instrument = Instrument(
        institution_id=inst.id,
        type="FDR",
        instrument_number="FDR-AT-001",
        amount=500000.0,
        status=InstrumentStatus.DRAFT,
    )
    db_session.add(instrument)
    db_session.flush()

    # Apply DRAFT -> SUBMITTED
    res = apply_transition(
        db_session,
        instrument,
        InstrumentStatus.SUBMITTED,
        actor_role=AppRole.INSTITUTION_SUBMITTER.value,
        actor_id=str(user.id),
        reason="Initial FDR submission by institution",
        reason_code="INSTITUTION_SUBMIT",
        correlation_id="corr-test-123",
    )
    db_session.commit()

    # 1. Check instrument status
    assert instrument.status == InstrumentStatus.SUBMITTED

    # 2. Check state_transitions row
    st = db_session.execute(
        select(StateTransition).where(
            StateTransition.id == uuid.UUID(res.transition_id)
        )
    ).scalar_one()
    assert st.entity_type == "instrument"
    assert st.entity_id == instrument.id
    assert st.from_state == "DRAFT"
    assert st.to_state == "SUBMITTED"
    assert st.reason_code == "INSTITUTION_SUBMIT"
    assert st.correlation_id == "corr-test-123"

    # 3. Check audit_log row
    audit = db_session.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "instrument",
            AuditLog.entity_id == str(instrument.id),
        )
    ).scalar_one()
    assert audit.after["status"] == "SUBMITTED"
    assert audit.after["reason_code"] == "INSTITUTION_SUBMIT"

    # 4. Check outbox row
    outbox = db_session.execute(
        select(OutboxEvent).where(
            OutboxEvent.aggregate_type == "instrument",
            OutboxEvent.aggregate_id == instrument.id,
            OutboxEvent.event_type == "instrument.state_changed",
        )
    ).scalar_one()
    assert outbox.payload["to_state"] == "SUBMITTED"


def test_state_transitions_table_is_append_only(db_session):
    inst = Institution(
        aicte_code=f"TR-{uuid.uuid4().hex[:8]}", name="Trigger Test Inst"
    )
    db_session.add(inst)
    db_session.flush()

    from app.models import AppUser

    user = AppUser(
        institution_id=inst.id,
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"trig-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Trigger Actor",
        role=AppRole.INSTITUTION_SUBMITTER,
    )
    db_session.add(user)
    db_session.flush()

    instrument = Instrument(
        institution_id=inst.id,
        type="FDR",
        instrument_number="FDR-TR-001",
        amount=100000.0,
        status=InstrumentStatus.DRAFT,
    )
    db_session.add(instrument)
    db_session.flush()

    res = apply_transition(
        db_session,
        instrument,
        InstrumentStatus.SUBMITTED,
        actor_role=AppRole.INSTITUTION_SUBMITTER.value,
        actor_id=str(user.id),
        reason="Submitting for append-only trigger check",
        reason_code="CHECK_TRIGGER",
    )
    db_session.commit()

    # Attempting to UPDATE state_transitions must fail by trigger
    with pytest.raises(Exception, match="prohibited"):
        db_session.execute(
            text(
                f"UPDATE state_transitions SET reason_text = 'Tampered' WHERE id = '{res.transition_id}'"
            )
        )
        db_session.flush()
    db_session.rollback()

    # Attempting to DELETE state_transitions must fail by trigger
    with pytest.raises(Exception, match="prohibited"):
        db_session.execute(
            text(f"DELETE FROM state_transitions WHERE id = '{res.transition_id}'")
        )
        db_session.flush()
    db_session.rollback()
