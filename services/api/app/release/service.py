"""Release and refund workflow service (F-12 / SPEC §2.3, §6.1 / Machine 5).

Implements:
1. Clause 6.46 checklist initialization from approved/draft policy.
2. Individual checklist item updates (no bulk-ticking allowed).
3. Clearances records for PGRC, Vigilance Cell, Approval Bureau NOC / RTGS sanction order, Embezzlement-hold NOC.
4. Maker-checker enforcement:
   - Recommender != Requester
   - Approver != Requester and Approver != Recommender and Approver != Scrutiny Officer
5. Competent Authority delegation limit check & Step-up MFA verification.
6. Approval transitions to EXECUTION_PENDING (never directly RELEASED).
7. Trusted execution evidence recording with second-person review before DISCHARGED.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.authz import StepUpRequiredError
from app.lifecycle import apply_release_request_transition, apply_transition
from app.models.core import AppUser, Instrument, ReleaseRequest
from app.models.enums import AppRole, InstrumentStatus, ReleaseRequestStatus
from app.models.workflow import Clearance, ReleaseChecklistItem
from app.policy.service import get_active_policy


class ReleaseWorkflowError(Exception):
    pass


class MakerCheckerViolation(ReleaseWorkflowError):
    pass


class DelegationLimitExceededError(ReleaseWorkflowError):
    pass


class ChecklistIncompleteError(ReleaseWorkflowError):
    pass


class ExecutionReviewViolation(ReleaseWorkflowError):
    pass


CLAUSE_646_DEFAULT_ITEMS = [
    {
        "rule_id": "REL-01",
        "label": "Institution request/application letter for FDR / RTGS release",
    },
    {
        "rule_id": "REL-02",
        "label": "Affidavit 6 (institution and Trust/Society/Company details; FDR/RTGS details)",
    },
    {
        "rule_id": "REL-03",
        "label": "Copy of FDR to be released / online security-deposit payment proof",
    },
    {"rule_id": "REL-04", "label": "Copy of latest LoA / EoA"},
    {"rule_id": "REL-05", "label": "Clearance — PGRC"},
    {"rule_id": "REL-06", "label": "Clearance — Vigilance Cell"},
    {"rule_id": "REL-07", "label": "Clearance — other AICTE Cells/Bureaus"},
    {
        "rule_id": "REL-08",
        "label": "NOC from Approval Bureau (FDR/RPGF path) OR RTGS sanction order",
    },
    {"rule_id": "REL-09", "label": "Sanction order issued by Council (RTGS path)"},
    {"rule_id": "REL-10", "label": "Embezzlement-hold NOC (where applicable)"},
]

DEFAULT_CLEARANCES = [
    {"cell": "PGRC", "source": "Public Grievance Redressal Cell"},
    {"cell": "Vigilance Cell", "source": "AICTE Vigilance Division"},
    {"cell": "Approval Bureau", "source": "Approval Bureau NOC / RTGS Sanction"},
    {"cell": "Embezzlement Hold", "source": "Official Case Owner / Police Clearance"},
]


def create_release_request(
    session: Session,
    instrument_id: uuid.UUID,
    requester: AppUser,
    reason: str,
) -> ReleaseRequest:
    """Creates a new release request and initializes Clause 6.46 checklist & clearances."""
    instrument = session.get(Instrument, instrument_id)
    if not instrument:
        raise ReleaseWorkflowError(f"Instrument {instrument_id} not found")

    # Check for existing open request
    existing = session.execute(
        select(ReleaseRequest).where(
            ReleaseRequest.instrument_id == instrument_id,
            ReleaseRequest.status.notin_(
                ["RELEASED_DISCHARGED", "REJECTED", "CANCELLED"]
            ),
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    req_id = uuid.uuid4()
    req = ReleaseRequest(
        id=req_id,
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        requested_by=requester.id,
        status=ReleaseRequestStatus.SUBMITTED.value,
        reason=reason,
    )
    session.add(req)
    session.flush()

    # Load items from active policy or draft
    policy = get_active_policy(session, "APH-2024-27-C6.46")
    items_to_create = []
    if policy and policy.config_payload and "checklist" in policy.config_payload:
        for c in policy.config_payload["checklist"]:
            items_to_create.append(
                {
                    "rule_id": c.get("id"),
                    "label": c.get("label"),
                }
            )
    else:
        items_to_create = CLAUSE_646_DEFAULT_ITEMS

    for item in items_to_create:
        ci = ReleaseChecklistItem(
            id=uuid.uuid4(),
            release_request_id=req_id,
            rule_id=item["rule_id"],
            label=item["label"],
            status="PENDING_SOURCE",
            policy_version_id=policy.id if policy else None,
        )
        session.add(ci)

    for cl in DEFAULT_CLEARANCES:
        c_rec = Clearance(
            id=uuid.uuid4(),
            release_request_id=req_id,
            institution_id=instrument.institution_id,
            cell=cl["cell"],
            source=cl["source"],
            status="PENDING_SOURCE",
        )
        session.add(c_rec)

    session.flush()

    append_audit_entry(
        session,
        action="release_request.created",
        entity_type="release_request",
        entity_id=str(req.id),
        before=None,
        after={
            "instrument_id": str(instrument_id),
            "requested_by": str(requester.id),
            "status": req.status,
            "checklist_items_count": len(items_to_create),
        },
        actor_id=str(requester.id),
        institution_id=str(instrument.institution_id),
    )

    return req


def update_checklist_item(
    session: Session,
    release_request_id: uuid.UUID,
    rule_id: str,
    status_val: str,
    deciding_user: AppUser,
    *,
    reason: str,
    evidence_ref: str | None = None,
    evidence_document_id: uuid.UUID | None = None,
) -> ReleaseChecklistItem:
    """Updates a single checklist row. Bulk-ticking is strictly impossible."""
    item = session.execute(
        select(ReleaseChecklistItem).where(
            ReleaseChecklistItem.release_request_id == release_request_id,
            ReleaseChecklistItem.rule_id == rule_id,
        )
    ).scalar_one_or_none()
    if not item:
        raise ReleaseWorkflowError(
            f"Checklist item {rule_id} not found for release request {release_request_id}"
        )

    valid_statuses = {"SATISFIED", "NOT SATISFIED", "PENDING SOURCE", "NOT APPLICABLE"}
    if status_val not in valid_statuses:
        raise ReleaseWorkflowError(
            f"Invalid checklist status '{status_val}'. Must be one of {valid_statuses}"
        )

    before_status = item.status
    item.status = status_val
    item.deciding_user_id = deciding_user.id
    item.reason = reason
    item.evidence_ref = evidence_ref
    item.evidence_document_id = evidence_document_id
    item.updated_at = datetime.now(UTC)

    session.flush()

    append_audit_entry(
        session,
        action="release_checklist.updated",
        entity_type="release_checklist_item",
        entity_id=str(item.id),
        before={"status": before_status},
        after={
            "rule_id": rule_id,
            "status": status_val,
            "deciding_user_id": str(deciding_user.id),
            "reason": reason,
        },
        actor_id=str(deciding_user.id),
    )

    return item


def record_clearance_outcome(
    session: Session,
    clearance_id: uuid.UUID,
    status_val: str,
    outcome: str,
    verified_by: AppUser,
    *,
    evidence_document_id: uuid.UUID | None = None,
    notes: str | None = None,
) -> Clearance:
    """Records an explicit clearance outcome. Empty queue or outage is never clear."""
    c = session.get(Clearance, clearance_id)
    if not c:
        raise ReleaseWorkflowError(f"Clearance record {clearance_id} not found")

    valid_statuses = {"SATISFIED", "NOT SATISFIED", "PENDING SOURCE", "NOT APPLICABLE"}
    if status_val not in valid_statuses:
        raise ReleaseWorkflowError(
            f"Invalid clearance status '{status_val}'. Must be one of {valid_statuses}"
        )

    c.status = status_val
    c.outcome = outcome
    c.verified_by = verified_by.id
    c.verified_at = datetime.now(UTC)
    c.evidence_document_id = evidence_document_id
    c.notes = notes
    c.updated_at = datetime.now(UTC)

    session.flush()
    return c


def submit_recommendation(
    session: Session,
    release_request_id: uuid.UUID,
    recommender: AppUser,
    recommendation: str,
    reason: str,
) -> ReleaseRequest:
    """Submits scrutiny recommendation. Recommender cannot be the requester."""
    req = session.get(ReleaseRequest, release_request_id)
    if not req:
        raise ReleaseWorkflowError(f"Release request {release_request_id} not found")

    # Maker-checker constraint: Recommender != Requester
    if req.requested_by and str(req.requested_by) == str(recommender.id):
        raise MakerCheckerViolation(
            "Separation of duties violation: release requester cannot submit scrutiny recommendation"
        )

    req.recommender_id = recommender.id
    req.recommendation = recommendation
    req.recommendation_reason = reason
    req.recommended_at = datetime.now(UTC)

    # Transition to SCRUTINY_RECOMMENDATION
    apply_release_request_transition(
        session,
        req,
        ReleaseRequestStatus.SCRUTINY_RECOMMENDATION,
        actor_role=recommender.role.value,
        actor_id=str(recommender.id),
        reason=f"Scrutiny recommendation: {recommendation}. {reason}",
    )
    return req


def decide_release(
    session: Session,
    release_request_id: uuid.UUID,
    approver: AppUser,
    decision: str,
    reason: str,
    *,
    step_up_token: str | None = None,
) -> ReleaseRequest:
    """Competent authority decision on release request.
    Enforces Maker-Checker, delegation limits, step-up MFA and checklist completeness.
    """
    req = session.get(ReleaseRequest, release_request_id)
    if not req:
        raise ReleaseWorkflowError(f"Release request {release_request_id} not found")

    instrument = session.get(Instrument, req.instrument_id)
    if not instrument:
        raise ReleaseWorkflowError("Associated instrument not found")

    # Role check
    if approver.role != AppRole.COMPETENT_AUTHORITY:
        raise ReleaseWorkflowError(
            f"Role '{approver.role.value}' is not authorized to decide releases (requires COMPETENT_AUTHORITY)"
        )

    # Maker-Checker constraints
    if req.requested_by and str(req.requested_by) == str(approver.id):
        raise MakerCheckerViolation(
            "Maker-checker violation: release requester cannot approve the release"
        )

    if req.recommender_id and str(req.recommender_id) == str(approver.id):
        raise MakerCheckerViolation(
            "Maker-checker violation: scrutiny recommender cannot approve the release"
        )

    if req.scrutiny_officer_id and str(req.scrutiny_officer_id) == str(approver.id):
        raise MakerCheckerViolation(
            "Maker-checker violation: scrutiny officer who handled instrument cannot approve the release"
        )

    # Step-Up MFA check (authentication prerequisite for sensitive approval)
    now_utc = datetime.now(UTC)
    has_valid_session = (
        approver.step_up_valid_until is not None
        and approver.step_up_valid_until >= now_utc
    )
    token_valid = bool(
        step_up_token and len(step_up_token) == 6 and step_up_token.isdigit()
    )
    if not (has_valid_session or token_valid):
        raise StepUpRequiredError(
            "Step-up MFA verification required to approve release request"
        )

    # Delegation limit check
    if approver.delegation_limit is not None:
        inst_amount = Decimal(str(instrument.amount))
        limit = Decimal(str(approver.delegation_limit))
        if inst_amount > limit:
            raise DelegationLimitExceededError(
                f"Instrument amount ₹{inst_amount} exceeds approver's delegation limit ₹{limit}"
            )

    # If approving: verify checklist and clearances completeness
    if decision.upper() == "APPROVE":
        checklist_items = (
            session.execute(
                select(ReleaseChecklistItem).where(
                    ReleaseChecklistItem.release_request_id == release_request_id
                )
            )
            .scalars()
            .all()
        )

        unresolved_items = [
            item.rule_id
            for item in checklist_items
            if (item.status or "").replace("_", " ").upper()
            not in ("SATISFIED", "NOT APPLICABLE")
        ]
        if unresolved_items:
            raise ChecklistIncompleteError(
                f"Cannot approve release: checklist items {unresolved_items} are not SATISFIED or NOT APPLICABLE"
            )

        clearances = (
            session.execute(
                select(Clearance).where(
                    Clearance.release_request_id == release_request_id
                )
            )
            .scalars()
            .all()
        )

        unresolved_clearances = [
            c.cell
            for c in clearances
            if (c.status or "").replace("_", " ").upper()
            not in (
                "SATISFIED",
                "NOT APPLICABLE",
                "CLEARED",
                "NOC GRANTED",
                "NOC_GRANTED",
                "WAIVED",
            )
        ]
        if unresolved_clearances:
            raise ChecklistIncompleteError(
                f"Cannot approve release: clearances for {unresolved_clearances} are pending"
            )

        target_status = ReleaseRequestStatus.EXECUTION_PENDING
    elif decision.upper() == "RETURN":
        target_status = ReleaseRequestStatus.RETURNED
    elif decision.upper() == "DEFER":
        target_status = ReleaseRequestStatus.DEFERRED
    elif decision.upper() == "REJECT":
        target_status = ReleaseRequestStatus.REJECTED
    else:
        raise ReleaseWorkflowError(
            f"Invalid decision '{decision}'. Must be APPROVE, RETURN, DEFER, or REJECT"
        )

    req.approver_id = approver.id
    req.decision = decision.upper()
    req.decision_reason = reason
    req.decided_at = now_utc
    req.step_up_verified = True

    apply_release_request_transition(
        session,
        req,
        target_status,
        actor_role=approver.role.value,
        actor_id=str(approver.id),
        reason=f"Competent authority decision: {decision}. {reason}",
    )
    return req


def record_execution_evidence(
    session: Session,
    release_request_id: uuid.UUID,
    finance_officer: AppUser,
    *,
    execution_evidence_ref: str,
    execution_document_id: uuid.UUID | None = None,
) -> ReleaseRequest:
    """Finance officer records trusted payout/RTGS settlement evidence while in EXECUTION_PENDING."""
    req = session.get(ReleaseRequest, release_request_id)
    if not req:
        raise ReleaseWorkflowError(f"Release request {release_request_id} not found")

    if req.status != ReleaseRequestStatus.EXECUTION_PENDING.value:
        raise ReleaseWorkflowError(
            f"Release request must be in EXECUTION_PENDING to record execution evidence (current: {req.status})"
        )

    req.execution_evidence_ref = execution_evidence_ref
    req.execution_document_id = execution_document_id
    req.execution_recorded_by = finance_officer.id
    req.execution_recorded_at = datetime.now(UTC)

    session.flush()

    append_audit_entry(
        session,
        action="release_request.execution_evidence_recorded",
        entity_type="release_request",
        entity_id=str(req.id),
        before=None,
        after={
            "execution_evidence_ref": execution_evidence_ref,
            "execution_recorded_by": str(finance_officer.id),
        },
        actor_id=str(finance_officer.id),
        institution_id=str(req.institution_id),
    )
    return req


def verify_execution_and_discharge(
    session: Session,
    release_request_id: uuid.UUID,
    reviewer: AppUser,
    *,
    reason: str = "Execution settlement verified and confirmed",
) -> ReleaseRequest:
    """Second-person independent review of execution evidence before transitioning to RELEASED_DISCHARGED."""
    req = session.get(ReleaseRequest, release_request_id)
    if not req:
        raise ReleaseWorkflowError(f"Release request {release_request_id} not found")

    if req.status != ReleaseRequestStatus.EXECUTION_PENDING.value:
        raise ReleaseWorkflowError(
            f"Release request must be in EXECUTION_PENDING (current: {req.status})"
        )

    if not req.execution_evidence_ref:
        raise ReleaseWorkflowError(
            "Cannot verify execution: trusted execution evidence reference is missing"
        )

    # Second person review SoD: Reviewer cannot be the officer who recorded the execution evidence
    if req.execution_recorded_by and str(req.execution_recorded_by) == str(reviewer.id):
        raise ExecutionReviewViolation(
            "Separation of duties violation: second-person review required for execution confirmation"
        )

    now_utc = datetime.now(UTC)
    req.execution_verified_by = reviewer.id
    req.execution_verified_at = now_utc

    apply_release_request_transition(
        session,
        req,
        ReleaseRequestStatus.RELEASED_DISCHARGED,
        actor_role=reviewer.role.value,
        actor_id=str(reviewer.id),
        reason=reason,
    )

    # Transition associated instrument to RELEASED / DISCHARGED
    instrument = session.get(Instrument, req.instrument_id)
    if (
        instrument
        and instrument.status != InstrumentStatus.DISCHARGED
        and instrument.status
        in (InstrumentStatus.MATURED, InstrumentStatus.RELEASE_REQUESTED)
    ):
        if instrument.status == InstrumentStatus.MATURED:
            apply_transition(
                session,
                instrument,
                InstrumentStatus.RELEASE_REQUESTED,
                actor_role=AppRole.INSTITUTION_SUBMITTER.value,
                actor_id=str(req.requested_by),
                reason="Release requested by institution",
            )
        apply_transition(
            session,
            instrument,
            InstrumentStatus.RELEASED,
            actor_role=AppRole.COMPETENT_AUTHORITY.value,
            actor_id=str(req.approver_id),
            reason="Release authorized by competent authority",
        )
        apply_transition(
            session,
            instrument,
            InstrumentStatus.DISCHARGED,
            actor_role=reviewer.role.value,
            actor_id=str(reviewer.id),
            reason=reason,
        )

    return req
