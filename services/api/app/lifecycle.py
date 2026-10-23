"""Instrument lifecycle state machine.

Every transition names the roles allowed to perform it and requires a
non-empty reason, which is written to the audit log along with the actor.
Transitions not in TRANSITIONS are illegal and rejected unconditionally —
there is no default-allow path.

"system" is a pseudo-role for automated transitions driven by Celery Beat
against the sim clock (ACTIVE->EXPIRING->MATURED as maturity approaches/
passes), not tied to any human app_user.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.models.core import Instrument
from app.models.enums import AppRole, InstrumentStatus

SYSTEM_ROLE = "system"

# from_status -> {to_status: {allowed roles}}
TRANSITIONS: dict[InstrumentStatus, dict[InstrumentStatus, frozenset[str]]] = {
    InstrumentStatus.SUBMITTED: {
        InstrumentStatus.UNDER_SCRUTINY: frozenset({AppRole.SCRUTINY_OFFICER.value}),
    },
    InstrumentStatus.UNDER_SCRUTINY: {
        InstrumentStatus.VERIFIED: frozenset({AppRole.VERIFIER.value}),
        # Sent back to the institution when scrutiny finds a discrepancy.
        InstrumentStatus.SUBMITTED: frozenset({AppRole.SCRUTINY_OFFICER.value}),
    },
    InstrumentStatus.VERIFIED: {
        InstrumentStatus.ACTIVE: frozenset({AppRole.REGIONAL_OFFICER.value}),
    },
    InstrumentStatus.ACTIVE: {
        InstrumentStatus.EXPIRING: frozenset({SYSTEM_ROLE}),
        # Rare but legal: a maturity window close enough that the EXPIRING
        # reminder window never fired before maturity.
        InstrumentStatus.MATURED: frozenset({SYSTEM_ROLE}),
    },
    InstrumentStatus.EXPIRING: {
        InstrumentStatus.MATURED: frozenset({SYSTEM_ROLE}),
    },
    InstrumentStatus.MATURED: {
        InstrumentStatus.RENEWAL_REQUESTED: frozenset({AppRole.INSTITUTION.value}),
        InstrumentStatus.REPLACEMENT_REQUESTED: frozenset({AppRole.INSTITUTION.value}),
        InstrumentStatus.RELEASE_REQUESTED: frozenset({AppRole.INSTITUTION.value}),
    },
    InstrumentStatus.RENEWAL_REQUESTED: {
        InstrumentStatus.ACTIVE: frozenset({AppRole.REGIONAL_OFFICER.value}),
    },
    InstrumentStatus.REPLACEMENT_REQUESTED: {
        # The replacement instrument re-enters scrutiny like a fresh submission.
        InstrumentStatus.UNDER_SCRUTINY: frozenset({AppRole.SCRUTINY_OFFICER.value}),
    },
    InstrumentStatus.RELEASE_REQUESTED: {
        # Approval is gated by maker-checker (app/rules/release.py) in
        # addition to this role check; both must pass.
        InstrumentStatus.RELEASED: frozenset({AppRole.COMPETENT_AUTHORITY.value}),
    },
    InstrumentStatus.RELEASED: {
        InstrumentStatus.DISCHARGED: frozenset({AppRole.BUREAU_ADMIN.value}),
    },
}


class IllegalTransitionError(Exception):
    pass


class UnauthorizedTransitionError(Exception):
    pass


@dataclass
class TransitionResult:
    instrument_id: str
    from_status: InstrumentStatus
    to_status: InstrumentStatus


def assert_transition_allowed(
    from_status: InstrumentStatus, to_status: InstrumentStatus, actor_role: str
) -> None:
    edges = TRANSITIONS.get(from_status, {})
    if to_status not in edges:
        raise IllegalTransitionError(f"{from_status.value} -> {to_status.value} is not a legal transition")
    if actor_role not in edges[to_status]:
        allowed = ", ".join(sorted(edges[to_status]))
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
) -> TransitionResult:
    if not reason or not reason.strip():
        raise ValueError("a non-empty reason is required for every lifecycle transition")

    from_status = instrument.status
    assert_transition_allowed(from_status, to_status, actor_role)

    instrument.status = to_status
    session.flush()

    append_audit_entry(
        session,
        action="instrument.lifecycle_transition",
        entity_type="instrument",
        entity_id=str(instrument.id),
        before={"status": from_status.value},
        after={"status": to_status.value, "reason": reason, "actor_role": actor_role},
        actor_id=actor_id,
        institution_id=str(instrument.institution_id),
    )
    return TransitionResult(str(instrument.id), from_status, to_status)
