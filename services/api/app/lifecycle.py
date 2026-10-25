"""Instrument, Observation, and Document lifecycle state machines (SPEC §6.1 / §7).

Every transition names the roles allowed to perform it and requires a
non-empty reason, which is written atomically to:
1. The domain entity (`status` updated)
2. `state_transitions` table (append-only trigger protected)
3. `audit_log` (with tamper-evident hash chain)
4. `outbox` (`enqueue_outbox_event` for transactional event publication)

Transitions not in the transition tables are illegal and rejected unconditionally.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.models.core import Document, Instrument, ReleaseRequest, ScrutinyObservation
from app.models.enums import (
    AppRole,
    DocumentStatus,
    InstrumentStatus,
    ObservationStatus,
    ReleaseRequestStatus,
)
from app.models.workflow import StateTransition
from app.outbox.producer import enqueue_outbox_event

SYSTEM_ROLE = "system"

# Legacy role alias mapping so existing tests pass seamlessly
ROLE_ALIASES: dict[str, str] = {
    "bureau_admin": AppRole.PLATFORM_OPERATOR.value,
    "institution": AppRole.INSTITUTION_SUBMITTER.value,
    "verifier": AppRole.FINANCE_VERIFIER.value,
    "regional_officer": AppRole.REGIONAL_SUPERVISOR.value,
    "auditor": AppRole.AUDIT_REVIEWER.value,
}


def normalize_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


# ==============================================================================
# Machine 1: Instrument Lifecycle
# ==============================================================================
# from_status -> {to_status: {allowed roles}}
INSTRUMENT_TRANSITIONS: dict[
    InstrumentStatus, dict[InstrumentStatus, frozenset[str]]
] = {
    InstrumentStatus.DRAFT: {
        InstrumentStatus.SUBMITTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
        InstrumentStatus.CANCELLED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
    },
    InstrumentStatus.SUBMITTED: {
        InstrumentStatus.INTAKE_REVIEW: frozenset(
            {
                AppRole.INTAKE_OFFICER.value,
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        InstrumentStatus.UNDER_SCRUTINY: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.INTAKE_OFFICER.value,
            }
        ),
        InstrumentStatus.SCRUTINY: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.INTAKE_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    InstrumentStatus.INTAKE_REVIEW: {
        InstrumentStatus.SCRUTINY: frozenset(
            {
                AppRole.INTAKE_OFFICER.value,
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        InstrumentStatus.UNDER_SCRUTINY: frozenset(
            {
                AppRole.INTAKE_OFFICER.value,
                AppRole.SCRUTINY_OFFICER.value,
            }
        ),
        InstrumentStatus.RETURNED_FOR_CORRECTION: frozenset(
            {
                AppRole.INTAKE_OFFICER.value,
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    InstrumentStatus.RETURNED_FOR_CORRECTION: {
        InstrumentStatus.SUBMITTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
        InstrumentStatus.CANCELLED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
    },
    InstrumentStatus.UNDER_SCRUTINY: {
        InstrumentStatus.VERIFIED: frozenset(
            {
                AppRole.FINANCE_VERIFIER.value,
                "verifier",
            }
        ),
        InstrumentStatus.SUBMITTED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
            }
        ),
        InstrumentStatus.RETURNED_FOR_CORRECTION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
            }
        ),
    },
    InstrumentStatus.SCRUTINY: {
        InstrumentStatus.ACTIVE_TRACKING: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.FINANCE_VERIFIER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        InstrumentStatus.ACTIVE: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.FINANCE_VERIFIER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        InstrumentStatus.RETURNED_FOR_CORRECTION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    InstrumentStatus.VERIFIED: {
        InstrumentStatus.ACTIVE: frozenset(
            {
                AppRole.REGIONAL_SUPERVISOR.value,
                "regional_officer",
            }
        ),
        InstrumentStatus.ACTIVE_TRACKING: frozenset(
            {
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    InstrumentStatus.ACTIVE: {
        InstrumentStatus.EXPIRING: frozenset({SYSTEM_ROLE}),
        InstrumentStatus.MATURED: frozenset({SYSTEM_ROLE}),
        InstrumentStatus.SUPERSEDED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    InstrumentStatus.ACTIVE_TRACKING: {
        InstrumentStatus.EXPIRING: frozenset({SYSTEM_ROLE}),
        InstrumentStatus.MATURED: frozenset({SYSTEM_ROLE}),
        InstrumentStatus.SUPERSEDED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        InstrumentStatus.CANCELLED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        InstrumentStatus.ARCHIVED: frozenset(
            {
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    InstrumentStatus.EXPIRING: {
        InstrumentStatus.MATURED: frozenset({SYSTEM_ROLE}),
        InstrumentStatus.SUPERSEDED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    InstrumentStatus.MATURED: {
        InstrumentStatus.RENEWAL_REQUESTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                "institution",
            }
        ),
        InstrumentStatus.REPLACEMENT_REQUESTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                "institution",
            }
        ),
        InstrumentStatus.RELEASE_REQUESTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                "institution",
            }
        ),
        InstrumentStatus.SUPERSEDED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    InstrumentStatus.RENEWAL_REQUESTED: {
        InstrumentStatus.ACTIVE: frozenset(
            {
                AppRole.REGIONAL_SUPERVISOR.value,
                "regional_officer",
            }
        ),
        InstrumentStatus.ACTIVE_TRACKING: frozenset(
            {
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        InstrumentStatus.SUPERSEDED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    InstrumentStatus.REPLACEMENT_REQUESTED: {
        InstrumentStatus.UNDER_SCRUTINY: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
            }
        ),
        InstrumentStatus.SCRUTINY: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
            }
        ),
        InstrumentStatus.SUPERSEDED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    InstrumentStatus.RELEASE_REQUESTED: {
        InstrumentStatus.RELEASED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
    },
    InstrumentStatus.RELEASED: {
        InstrumentStatus.DISCHARGED: frozenset(
            {
                AppRole.PLATFORM_OPERATOR.value,
                AppRole.FINANCE_VERIFIER.value,
                "bureau_admin",
            }
        ),
    },
}

TRANSITIONS = INSTRUMENT_TRANSITIONS


# ==============================================================================
# Machine 3: Observation Lifecycle
# ==============================================================================
OBSERVATION_TRANSITIONS: dict[
    ObservationStatus, dict[ObservationStatus, frozenset[str]]
] = {
    ObservationStatus.OPEN: {
        ObservationStatus.AWAITING_INSTITUTION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    ObservationStatus.AWAITING_INSTITUTION: {
        ObservationStatus.RESPONSE_RECEIVED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
    },
    ObservationStatus.RESPONSE_RECEIVED: {
        ObservationStatus.UNDER_REVIEW: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    ObservationStatus.UNDER_REVIEW: {
        ObservationStatus.RESOLVED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        ObservationStatus.AWAITING_INSTITUTION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    ObservationStatus.RESOLVED: {
        ObservationStatus.CLOSED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        ObservationStatus.OPEN: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    ObservationStatus.CLOSED: {
        ObservationStatus.OPEN: frozenset(
            {
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
}


# ==============================================================================
# Machine 7: Document Lifecycle
# ==============================================================================
DOCUMENT_TRANSITIONS: dict[DocumentStatus, dict[DocumentStatus, frozenset[str]]] = {
    DocumentStatus.UPLOAD_INTENT: {
        DocumentStatus.QUARANTINED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.PLATFORM_OPERATOR.value,
                "institution",
            }
        ),
        DocumentStatus.REJECTED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    DocumentStatus.QUARANTINED: {
        DocumentStatus.SCANNING: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        DocumentStatus.REJECTED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
    DocumentStatus.SCANNING: {
        DocumentStatus.ACCEPTED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        DocumentStatus.REJECTED: frozenset(
            {
                SYSTEM_ROLE,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
    },
}


class IllegalTransitionError(Exception):
    pass


class UnauthorizedTransitionError(Exception):
    pass


@dataclass
class TransitionResult:
    entity_id: str
    from_status: str
    to_status: str
    transition_id: str | None = None


def assert_transition_allowed(
    from_status: InstrumentStatus, to_status: InstrumentStatus, actor_role: str
) -> None:
    edges = INSTRUMENT_TRANSITIONS.get(from_status, {})
    if to_status not in edges:
        raise IllegalTransitionError(
            f"{from_status.value} -> {to_status.value} is not a legal transition"
        )

    normalized = normalize_role(actor_role)
    allowed_roles = edges[to_status]
    # Check if either the raw role or normalized role is allowed
    if actor_role not in allowed_roles and normalized not in allowed_roles:
        allowed = ", ".join(sorted(allowed_roles))
        raise UnauthorizedTransitionError(
            f"role '{actor_role}' may not perform {from_status.value} -> {to_status.value} "
            f"(allowed: {allowed})"
        )


def assert_observation_transition_allowed(
    from_status: ObservationStatus, to_status: ObservationStatus, actor_role: str
) -> None:
    edges = OBSERVATION_TRANSITIONS.get(from_status, {})
    if to_status not in edges:
        raise IllegalTransitionError(
            f"{from_status.value} -> {to_status.value} is not a legal observation transition"
        )

    normalized = normalize_role(actor_role)
    allowed_roles = edges[to_status]
    if actor_role not in allowed_roles and normalized not in allowed_roles:
        allowed = ", ".join(sorted(allowed_roles))
        raise UnauthorizedTransitionError(
            f"role '{actor_role}' may not perform {from_status.value} -> {to_status.value} "
            f"(allowed: {allowed})"
        )


def assert_document_transition_allowed(
    from_status: DocumentStatus, to_status: DocumentStatus, actor_role: str
) -> None:
    edges = DOCUMENT_TRANSITIONS.get(from_status, {})
    if to_status not in edges:
        raise IllegalTransitionError(
            f"{from_status.value} -> {to_status.value} is not a legal document transition"
        )

    normalized = normalize_role(actor_role)
    allowed_roles = edges[to_status]
    if actor_role not in allowed_roles and normalized not in allowed_roles:
        allowed = ", ".join(sorted(allowed_roles))
        raise UnauthorizedTransitionError(
            f"role '{actor_role}' may not perform {from_status.value} -> {to_status.value} "
            f"(allowed: {allowed})"
        )


def apply_transition(
    session: Session,
    instrument: Instrument,
    to_status: InstrumentStatus,
    *,
    actor_role: str,
    actor_id: str | None,
    reason: str,
    reason_code: str = "MANUAL_TRANSITION",
    correlation_id: str | None = None,
    evidence_ref: str | None = None,
) -> TransitionResult:
    """Atomically executes an instrument transition:
    1. Updates instrument.status
    2. Inserts append-only state_transitions record
    3. Appends hash-chained audit_log entry
    4. Enqueues outbox event in the same transaction
    """
    if not reason or not reason.strip():
        raise ValueError(
            "a non-empty reason is required for every lifecycle transition"
        )

    from_status = instrument.status
    assert_transition_allowed(from_status, to_status, actor_role)

    instrument.status = to_status
    session.flush()

    actor_uuid = (
        uuid.UUID(actor_id)
        if actor_id and isinstance(actor_id, str) and len(actor_id) == 36
        else (actor_id if isinstance(actor_id, uuid.UUID) else None)
    )

    st_id = uuid.uuid4()
    st = StateTransition(
        id=st_id,
        entity_type="instrument",
        entity_id=instrument.id,
        from_state=from_status.value,
        to_state=to_status.value,
        actor_id=actor_uuid,
        reason_code=reason_code,
        reason_text=reason,
        correlation_id=correlation_id,
        evidence_ref=evidence_ref,
    )
    session.add(st)
    session.flush()

    append_audit_entry(
        session,
        action="instrument.lifecycle_transition",
        entity_type="instrument",
        entity_id=str(instrument.id),
        before={"status": from_status.value},
        after={
            "status": to_status.value,
            "reason": reason,
            "reason_code": reason_code,
            "actor_role": actor_role,
        },
        actor_id=actor_id,
        institution_id=str(instrument.institution_id),
    )

    enqueue_outbox_event(
        session,
        aggregate_type="instrument",
        aggregate_id=instrument.id,
        event_type="instrument.state_changed",
        payload={
            "from_state": from_status.value,
            "to_state": to_status.value,
            "actor_role": actor_role,
            "reason_code": reason_code,
            "reason": reason,
        },
        dedupe_key=f"instrument.state_changed:{instrument.id}:{from_status.value}->{to_status.value}:{st_id.hex[:8]}",
    )

    return TransitionResult(
        str(instrument.id), from_status.value, to_status.value, str(st_id)
    )


def apply_observation_transition(
    session: Session,
    observation: ScrutinyObservation,
    to_status: ObservationStatus,
    *,
    actor_role: str,
    actor_id: str | None,
    reason: str,
    reason_code: str = "OBSERVATION_TRANSITION",
    correlation_id: str | None = None,
) -> TransitionResult:
    """Atomically executes an observation transition (Machine 3)."""
    if not reason or not reason.strip():
        raise ValueError(
            "a non-empty reason is required for every lifecycle transition"
        )

    current_status = (
        ObservationStatus(observation.status)
        if isinstance(observation.status, str)
        else observation.status
    )
    assert_observation_transition_allowed(current_status, to_status, actor_role)

    observation.status = to_status.value
    session.flush()

    actor_uuid = (
        uuid.UUID(actor_id)
        if actor_id and isinstance(actor_id, str) and len(actor_id) == 36
        else (actor_id if isinstance(actor_id, uuid.UUID) else None)
    )

    st_id = uuid.uuid4()
    st = StateTransition(
        id=st_id,
        entity_type="observation",
        entity_id=observation.id,
        from_state=current_status.value,
        to_state=to_status.value,
        actor_id=actor_uuid,
        reason_code=reason_code,
        reason_text=reason,
        correlation_id=correlation_id,
    )
    session.add(st)
    session.flush()

    append_audit_entry(
        session,
        action="observation.lifecycle_transition",
        entity_type="observation",
        entity_id=str(observation.id),
        before={"status": current_status.value},
        after={
            "status": to_status.value,
            "reason": reason,
            "reason_code": reason_code,
            "actor_role": actor_role,
        },
        actor_id=actor_id,
        institution_id=str(observation.institution_id),
    )

    enqueue_outbox_event(
        session,
        aggregate_type="observation",
        aggregate_id=observation.id,
        event_type="observation.state_changed",
        payload={
            "from_state": current_status.value,
            "to_state": to_status.value,
            "actor_role": actor_role,
            "reason_code": reason_code,
            "reason": reason,
        },
        dedupe_key=f"observation.state_changed:{observation.id}:{current_status.value}->{to_status.value}:{st_id.hex[:8]}",
    )

    return TransitionResult(
        str(observation.id), current_status.value, to_status.value, str(st_id)
    )


def apply_document_transition(
    session: Session,
    document: Document,
    to_status: DocumentStatus,
    *,
    actor_role: str,
    actor_id: str | None,
    reason: str,
    reason_code: str = "DOCUMENT_TRANSITION",
    correlation_id: str | None = None,
) -> TransitionResult:
    """Atomically executes a document transition (Machine 7)."""
    if not reason or not reason.strip():
        raise ValueError(
            "a non-empty reason is required for every lifecycle transition"
        )

    current_status = (
        DocumentStatus(document.status)
        if isinstance(document.status, str)
        else document.status
    )
    assert_document_transition_allowed(current_status, to_status, actor_role)

    document.status = to_status.value
    session.flush()

    actor_uuid = (
        uuid.UUID(actor_id)
        if actor_id and isinstance(actor_id, str) and len(actor_id) == 36
        else (actor_id if isinstance(actor_id, uuid.UUID) else None)
    )

    st_id = uuid.uuid4()
    st = StateTransition(
        id=st_id,
        entity_type="document",
        entity_id=document.id,
        from_state=current_status.value,
        to_state=to_status.value,
        actor_id=actor_uuid,
        reason_code=reason_code,
        reason_text=reason,
        correlation_id=correlation_id,
    )
    session.add(st)
    session.flush()

    append_audit_entry(
        session,
        action="document.lifecycle_transition",
        entity_type="document",
        entity_id=str(document.id),
        before={"status": current_status.value},
        after={
            "status": to_status.value,
            "reason": reason,
            "reason_code": reason_code,
            "actor_role": actor_role,
        },
        actor_id=actor_id,
        institution_id=str(document.institution_id),
    )

    enqueue_outbox_event(
        session,
        aggregate_type="document",
        aggregate_id=document.id,
        event_type="document.state_changed",
        payload={
            "from_state": current_status.value,
            "to_state": to_status.value,
            "actor_role": actor_role,
            "reason_code": reason_code,
            "reason": reason,
        },
        dedupe_key=f"document.state_changed:{document.id}:{current_status.value}->{to_status.value}:{st_id.hex[:8]}",
    )

    return TransitionResult(
        str(document.id), current_status.value, to_status.value, str(st_id)
    )


# ==============================================================================
# Machine 5: Release Request Lifecycle (SPEC §2.3, §6.1 / Clause 6.46)
# ==============================================================================
RELEASE_REQUEST_TRANSITIONS: dict[
    ReleaseRequestStatus, dict[ReleaseRequestStatus, frozenset[str]]
] = {
    ReleaseRequestStatus.DRAFT: {
        ReleaseRequestStatus.SUBMITTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
        ReleaseRequestStatus.CANCELLED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
    },
    ReleaseRequestStatus.SUBMITTED: {
        ReleaseRequestStatus.COMPLETENESS_REVIEW: frozenset(
            {
                AppRole.INTAKE_OFFICER.value,
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        ReleaseRequestStatus.SCRUTINY_RECOMMENDATION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        ReleaseRequestStatus.RETURNED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        ReleaseRequestStatus.CANCELLED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
    },
    ReleaseRequestStatus.COMPLETENESS_REVIEW: {
        ReleaseRequestStatus.REQUIRED_CLEARANCES: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        ReleaseRequestStatus.SCRUTINY_RECOMMENDATION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
            }
        ),
        ReleaseRequestStatus.RETURNED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    ReleaseRequestStatus.REQUIRED_CLEARANCES: {
        ReleaseRequestStatus.SCRUTINY_RECOMMENDATION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        ReleaseRequestStatus.RETURNED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        ReleaseRequestStatus.DEFERRED: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    ReleaseRequestStatus.SCRUTINY_RECOMMENDATION: {
        ReleaseRequestStatus.COMPETENT_AUTHORITY_DECISION: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.EXECUTION_PENDING: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.RETURNED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.DEFERRED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.REJECTED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
    },
    ReleaseRequestStatus.COMPETENT_AUTHORITY_DECISION: {
        ReleaseRequestStatus.EXECUTION_PENDING: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.RETURNED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.DEFERRED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
        ReleaseRequestStatus.REJECTED: frozenset(
            {
                AppRole.COMPETENT_AUTHORITY.value,
            }
        ),
    },
    ReleaseRequestStatus.EXECUTION_PENDING: {
        ReleaseRequestStatus.RELEASED_DISCHARGED: frozenset(
            {
                AppRole.FINANCE_VERIFIER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
                AppRole.PLATFORM_OPERATOR.value,
                SYSTEM_ROLE,
            }
        ),
        ReleaseRequestStatus.DEFERRED: frozenset(
            {
                AppRole.FINANCE_VERIFIER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
    ReleaseRequestStatus.RETURNED: {
        ReleaseRequestStatus.SUBMITTED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
        ReleaseRequestStatus.CANCELLED: frozenset(
            {
                AppRole.INSTITUTION_SUBMITTER.value,
                AppRole.ORG_ADMIN.value,
                "institution",
            }
        ),
    },
    ReleaseRequestStatus.DEFERRED: {
        ReleaseRequestStatus.SCRUTINY_RECOMMENDATION: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
        ReleaseRequestStatus.REQUIRED_CLEARANCES: frozenset(
            {
                AppRole.SCRUTINY_OFFICER.value,
                AppRole.REGIONAL_SUPERVISOR.value,
            }
        ),
    },
}


def assert_release_request_transition_allowed(
    from_status: ReleaseRequestStatus,
    to_status: ReleaseRequestStatus,
    actor_role: str,
) -> None:
    edges = RELEASE_REQUEST_TRANSITIONS.get(from_status, {})
    if to_status not in edges:
        raise IllegalTransitionError(
            f"{from_status.value} -> {to_status.value} is not a legal release request transition"
        )

    normalized = normalize_role(actor_role)
    allowed_roles = edges[to_status]
    if actor_role not in allowed_roles and normalized not in allowed_roles:
        allowed = ", ".join(sorted(allowed_roles))
        raise UnauthorizedTransitionError(
            f"role '{actor_role}' may not perform {from_status.value} -> {to_status.value} "
            f"(allowed: {allowed})"
        )


def apply_release_request_transition(
    session: Session,
    release_request: ReleaseRequest,
    to_status: ReleaseRequestStatus,
    *,
    actor_role: str,
    actor_id: str | None,
    reason: str,
    reason_code: str = "RELEASE_TRANSITION",
    correlation_id: str | None = None,
) -> TransitionResult:
    """Atomically executes a release request transition (Machine 5)."""
    if not reason or not reason.strip():
        raise ValueError(
            "a non-empty reason is required for every lifecycle transition"
        )

    current_status = (
        ReleaseRequestStatus(release_request.status)
        if isinstance(release_request.status, str)
        else release_request.status
    )
    assert_release_request_transition_allowed(current_status, to_status, actor_role)

    release_request.status = to_status.value
    session.flush()

    actor_uuid = (
        uuid.UUID(actor_id)
        if actor_id and isinstance(actor_id, str) and len(actor_id) == 36
        else (actor_id if isinstance(actor_id, uuid.UUID) else None)
    )

    st_id = uuid.uuid4()
    st = StateTransition(
        id=st_id,
        entity_type="release_request",
        entity_id=release_request.id,
        from_state=current_status.value,
        to_state=to_status.value,
        actor_id=actor_uuid,
        reason_code=reason_code,
        reason_text=reason,
        correlation_id=correlation_id,
    )
    session.add(st)
    session.flush()

    append_audit_entry(
        session,
        action="release_request.lifecycle_transition",
        entity_type="release_request",
        entity_id=str(release_request.id),
        before={"status": current_status.value},
        after={
            "status": to_status.value,
            "reason": reason,
            "reason_code": reason_code,
            "actor_role": actor_role,
        },
        actor_id=actor_id,
        institution_id=str(release_request.institution_id),
    )

    enqueue_outbox_event(
        session,
        aggregate_type="release_request",
        aggregate_id=release_request.id,
        event_type="release_request.state_changed",
        payload={
            "from_state": current_status.value,
            "to_state": to_status.value,
            "actor_role": actor_role,
            "reason_code": reason_code,
            "reason": reason,
        },
        dedupe_key=f"release_request.state_changed:{release_request.id}:{current_status.value}->{to_status.value}:{st_id.hex[:8]}",
    )

    return TransitionResult(
        str(release_request.id), current_status.value, to_status.value, str(st_id)
    )
