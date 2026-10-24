"""SPEC §18.1 Scenario 9 / PS Scenario: Authorised Release Processing.

Scenario 9 Requirements:
1. Release checklist blocks or defers incomplete cases (unresolved items block APPROVE).
2. Checklist rows cannot be bulk-ticked; each row is individually resolved.
3. Same-person maker/checker denied at API and DB (recommender != requester, approver != requester/recommender).
4. Competent Authority delegation limit checked: out-of-delegation denied.
5. Approval without step-up MFA denied.
6. Approval transitions to EXECUTION_PENDING (never directly RELEASED).
7. Trusted execution evidence recorded by finance officer; second-person independent
   review required to transition to RELEASED_DISCHARGED.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.authz import StepUpRequiredError
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import (
    AppRole,
    InstrumentStatus,
    InstrumentType,
    ReleaseRequestStatus,
)
from app.models.workflow import Clearance, ReleaseChecklistItem
from app.release.service import (
    ChecklistIncompleteError,
    DelegationLimitExceededError,
    ExecutionReviewViolation,
    MakerCheckerViolation,
    create_release_request,
    decide_release,
    record_clearance_outcome,
    record_execution_evidence,
    submit_recommendation,
    update_checklist_item,
    verify_execution_and_discharge,
)


def _setup_actors(db_session):
    inst = Institution(
        aicte_code=f"SCEN9-{uuid.uuid4().hex[:8]}",
        name="Scenario 9 Release Engineering Institute",
    )
    db_session.add(inst)
    db_session.flush()

    requester = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        institution_id=inst.id,
        email=f"inst-{uuid.uuid4().hex[:6]}@college.edu",
        full_name="College Registrar",
        role=AppRole.INSTITUTION_SUBMITTER,
        is_active=True,
    )
    scrutiny_officer = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"scrutiny-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Scrutiny Officer",
        role=AppRole.SCRUTINY_OFFICER,
        is_active=True,
    )
    competent_authority = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"ca-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Advisor Competent Authority",
        role=AppRole.COMPETENT_AUTHORITY,
        delegation_limit=Decimal("5000000.00"),  # ₹ 50 Lakh limit
        is_active=True,
    )
    finance_officer = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"finance-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Finance Officer",
        role=AppRole.FINANCE_VERIFIER,
        is_active=True,
    )
    finance_reviewer = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        email=f"fin-rev-{uuid.uuid4().hex[:6]}@aicte.gov.in",
        full_name="AICTE Finance Senior Officer",
        role=AppRole.FINANCE_VERIFIER,
        is_active=True,
    )
    db_session.add_all([requester, scrutiny_officer, competent_authority, finance_officer, finance_reviewer])
    db_session.flush()

    return inst, requester, scrutiny_officer, competent_authority, finance_officer, finance_reviewer


def _create_instrument(db_session, inst, amount=3500000.0):
    now = datetime.now(UTC)
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-REL-{uuid.uuid4().hex[:6]}",
        amount=amount,
        status=InstrumentStatus.MATURED,
        issue_date=now - timedelta(days=365 * 10),
        maturity_date=now - timedelta(days=10),
        tenor_months=120,
    )
    db_session.add(instrument)
    db_session.flush()
    return instrument


def test_scenario_9_checklist_incomplete_blocks_approval(db_session):
    """SPEC §18.1 Scenario 9: Release checklist blocks incomplete cases."""
    inst, requester, scrutiny_officer, ca, _, _ = _setup_actors(db_session)
    instrument = _create_instrument(db_session, inst)

    # 1. Create release request
    req = create_release_request(db_session, instrument.id, requester, reason="10-year term complete")
    assert req.status == ReleaseRequestStatus.SUBMITTED.value

    # Scrutiny submits recommendation
    submit_recommendation(db_session, req.id, scrutiny_officer, "APPROVE", reason="Initial docs look OK")

    # Step-up session established
    ca.step_up_valid_until = datetime.now(UTC) + timedelta(minutes=15)

    # Attempting to approve while checklist items and clearances are PENDING_SOURCE must fail
    with pytest.raises(ChecklistIncompleteError) as exc:
        decide_release(db_session, req.id, ca, "APPROVE", reason="Premature approval attempt")
    assert "checklist items" in str(exc.value) or "clearances" in str(exc.value)


def test_scenario_9_same_person_maker_checker_strictly_denied(db_session):
    """SPEC §18.1 Scenario 9: Same-person maker/checker denied at API and DB level."""
    inst, requester, scrutiny_officer, ca, _, _ = _setup_actors(db_session)
    instrument = _create_instrument(db_session, inst)

    req = create_release_request(db_session, instrument.id, requester, reason="Term fulfilled")

    # Requester cannot submit scrutiny recommendation
    with pytest.raises(MakerCheckerViolation):
        submit_recommendation(db_session, req.id, requester, "APPROVE", reason="Recommending my own release")

    # Scrutiny officer submits recommendation
    submit_recommendation(db_session, req.id, scrutiny_officer, "APPROVE", reason="Documents satisfied")

    ca.step_up_valid_until = datetime.now(UTC) + timedelta(minutes=15)

    # Scrutiny recommender cannot also act as approver
    scrutiny_as_approver = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        id=scrutiny_officer.id,
        email=scrutiny_officer.email,
        full_name=scrutiny_officer.full_name,
        role=AppRole.COMPETENT_AUTHORITY,
        delegation_limit=Decimal("10000000.00"),
        step_up_valid_until=datetime.now(UTC) + timedelta(minutes=15),
        is_active=True,
    )
    with pytest.raises(MakerCheckerViolation) as exc:
        decide_release(db_session, req.id, scrutiny_as_approver, "APPROVE", reason="Self approving")
    assert "recommender cannot approve" in str(exc.value)

    # Requester cannot act as approver even with CA role
    requester_as_approver = AppUser(
        keycloak_sub=f"sub-{uuid.uuid4().hex[:8]}",
        id=requester.id,
        email=requester.email,
        full_name=requester.full_name,
        role=AppRole.COMPETENT_AUTHORITY,
        delegation_limit=Decimal("10000000.00"),
        step_up_valid_until=datetime.now(UTC) + timedelta(minutes=15),
        is_active=True,
    )
    with pytest.raises(MakerCheckerViolation) as exc:
        decide_release(db_session, req.id, requester_as_approver, "APPROVE", reason="Self approving")
    assert "requester cannot approve" in str(exc.value)


def test_scenario_9_delegation_limit_and_step_up_enforcement(db_session):
    """SPEC §18.1 Scenario 9: Delegation limit and step-up MFA enforced."""
    inst, requester, scrutiny_officer, ca, _, _ = _setup_actors(db_session)
    # Instrument amount ₹ 60 Lakh (exceeds CA delegation limit ₹ 50 Lakh)
    expensive_inst = _create_instrument(db_session, inst, amount=6000000.0)

    req = create_release_request(db_session, expensive_inst.id, requester, reason="Term complete")
    submit_recommendation(db_session, req.id, scrutiny_officer, "APPROVE", reason="Clearances ready")

    # 1. Test missing step-up MFA
    ca.step_up_valid_until = None
    with pytest.raises(StepUpRequiredError):
        decide_release(db_session, req.id, ca, "APPROVE", reason="No step up")

    # 2. Test delegation limit exceeded
    ca.step_up_valid_until = datetime.now(UTC) + timedelta(minutes=15)
    with pytest.raises(DelegationLimitExceededError) as exc:
        decide_release(db_session, req.id, ca, "APPROVE", reason="Exceeds limit")
    assert "exceeds approver's delegation limit" in str(exc.value)


def test_scenario_9_end_to_end_authorised_release_and_execution_proof(db_session):
    """SPEC §18.1 Scenario 9 & PS Scenario 'authorised release':
    Full chain: checklist satisfied -> recommendation -> CA decision ->
    EXECUTION_PENDING -> finance officer records payment proof ->
    independent second-person review -> RELEASED_DISCHARGED.
    """
    inst, requester, scrutiny_officer, ca, fin_officer, fin_reviewer = _setup_actors(db_session)
    instrument = _create_instrument(db_session, inst, amount=3500000.0)

    # 1. Create request
    req = create_release_request(db_session, instrument.id, requester, reason="10-year term complete")
    assert req.status == ReleaseRequestStatus.SUBMITTED.value

    # 2. Satisfy all checklist items individually (no bulk ticking)
    checklist_rows = db_session.execute(
        select(ReleaseChecklistItem).where(ReleaseChecklistItem.release_request_id == req.id)
    ).scalars().all()

    for item in checklist_rows:
        update_checklist_item(
            db_session,
            req.id,
            item.rule_id,
            "SATISFIED",
            scrutiny_officer,
            reason=f"Verified official evidence for {item.rule_id}",
            evidence_ref=f"EVID-{uuid.uuid4().hex[:8]}",
        )

    # 3. Satisfy all clearances explicitly
    clearance_rows = db_session.execute(
        select(Clearance).where(Clearance.release_request_id == req.id)
    ).scalars().all()

    for cl in clearance_rows:
        record_clearance_outcome(
            db_session,
            cl.id,
            "SATISFIED",
            outcome="NOC_GRANTED",
            verified_by=scrutiny_officer,
            notes=f"Official clearance issued by {cl.cell}",
        )

    # 4. Scrutiny recommendation
    submit_recommendation(db_session, req.id, scrutiny_officer, "APPROVE", reason="All checklist & clearances satisfied")
    assert req.status == ReleaseRequestStatus.SCRUTINY_RECOMMENDATION.value

    # 5. Competent Authority decision with Step-up MFA
    ca.step_up_valid_until = datetime.now(UTC) + timedelta(minutes=15)
    decide_release(db_session, req.id, ca, "APPROVE", reason="All compliance criteria fulfilled")

    # CRITICAL INVARIANT: status is EXECUTION_PENDING, NOT released!
    assert req.status == ReleaseRequestStatus.EXECUTION_PENDING.value
    assert instrument.status != InstrumentStatus.DISCHARGED

    # 6. Finance officer records trusted execution evidence
    record_execution_evidence(
        db_session,
        req.id,
        fin_officer,
        execution_evidence_ref="UTR-RTGS-20261024-99887766",
    )
    assert req.execution_evidence_ref == "UTR-RTGS-20261024-99887766"

    # 7. SoD: Finance officer who recorded execution cannot review/discharge it
    with pytest.raises(ExecutionReviewViolation):
        verify_execution_and_discharge(db_session, req.id, fin_officer)

    # 8. Second person (independent finance reviewer) confirms execution evidence
    discharged_req = verify_execution_and_discharge(
        db_session,
        req.id,
        fin_reviewer,
        reason="Bank settlement reference verified against treasury account statement",
    )

    assert discharged_req.status == ReleaseRequestStatus.RELEASED_DISCHARGED.value

    # Instrument is now properly DISCHARGED
    reloaded_inst = db_session.get(Instrument, instrument.id)
    assert reloaded_inst.status == InstrumentStatus.DISCHARGED
