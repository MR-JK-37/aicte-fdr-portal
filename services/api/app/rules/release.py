"""Release-eligibility checklist and maker-checker enforcement.

Eligibility citations: the one quote given verbatim in the source blueprint
("APH 2024-27, cl. 6.46", Blueprint.txt line 371, as the Compliance RAG
agent's example citation format) is used for the term-served rule. The
other rules' clause citations are not in the blueprint and are left as
"citation_pending" rather than invented — the real RAG agent (Phase 6)
resolves these against the actual APH text; this checker's job is the
structural eligibility logic, not sourcing clause text.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Discrepancy, Penalty, ReleaseRequest, ScrutinyObservation
from app.models.enums import InstrumentStatus


@dataclass
class ChecklistItem:
    rule_id: str
    passed: bool
    detail: str
    citation: str


@dataclass
class EligibilityResult:
    eligible: bool
    checklist: list[ChecklistItem]


def check_release_eligibility(session: Session, instrument) -> EligibilityResult:
    checklist: list[ChecklistItem] = []

    term_served = instrument.status in (
        InstrumentStatus.MATURED,
        InstrumentStatus.RELEASE_REQUESTED,
    )
    checklist.append(
        ChecklistItem(
            rule_id="term_served",
            passed=term_served,
            detail="Instrument has reached maturity"
            if term_served
            else "Instrument has not yet matured",
            citation="APH 2024-27, cl. 6.46",
        )
    )

    open_discrepancies = (
        session.execute(
            select(Discrepancy).where(
                Discrepancy.instrument_id == instrument.id, Discrepancy.status == "open"
            )
        )
        .scalars()
        .all()
    )
    checklist.append(
        ChecklistItem(
            rule_id="no_open_discrepancies",
            passed=len(open_discrepancies) == 0,
            detail=f"{len(open_discrepancies)} open discrepancy/ies"
            if open_discrepancies
            else "No open discrepancies",
            citation="citation_pending",
        )
    )

    open_observations = (
        session.execute(
            select(ScrutinyObservation).where(
                ScrutinyObservation.instrument_id == instrument.id,
                ScrutinyObservation.status == "open",
            )
        )
        .scalars()
        .all()
    )
    checklist.append(
        ChecklistItem(
            rule_id="no_pending_observations",
            passed=len(open_observations) == 0,
            detail=f"{len(open_observations)} pending scrutiny observation(s)"
            if open_observations
            else "No pending scrutiny observations",
            citation="citation_pending",
        )
    )

    unpaid_penalties = (
        session.execute(
            select(Penalty).where(
                Penalty.instrument_id == instrument.id, Penalty.status == "unpaid"
            )
        )
        .scalars()
        .all()
    )
    checklist.append(
        ChecklistItem(
            rule_id="no_unpaid_penalties",
            passed=len(unpaid_penalties) == 0,
            detail=f"{len(unpaid_penalties)} unpaid penalty/ies"
            if unpaid_penalties
            else "No unpaid penalties",
            citation="citation_pending",
        )
    )

    return EligibilityResult(
        eligible=all(item.passed for item in checklist), checklist=checklist
    )


class MakerCheckerViolation(Exception):
    pass


def assert_maker_checker(
    *,
    approver_id: str,
    approver_role: str,
    release_request: ReleaseRequest,
) -> None:
    """The four-eyes rule: the approver must hold the competent_authority
    role, must not be the person who made the release request, and must
    not be the scrutiny officer who handled this instrument's file."""
    if approver_role != "competent_authority":
        raise MakerCheckerViolation(
            f"role '{approver_role}' is not authorized to approve a release"
        )

    if release_request.requested_by is not None and str(
        release_request.requested_by
    ) == str(approver_id):
        raise MakerCheckerViolation(
            "the release requester cannot also approve the release"
        )

    if release_request.scrutiny_officer_id is not None and str(
        release_request.scrutiny_officer_id
    ) == str(approver_id):
        raise MakerCheckerViolation(
            "the scrutiny officer who handled this instrument cannot approve its release (maker-checker)"
        )
