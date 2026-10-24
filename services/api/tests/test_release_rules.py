import uuid

import pytest

from app.models import (
    AppUser,
    Discrepancy,
    Institution,
    Instrument,
    Penalty,
    ReleaseRequest,
    ScrutinyObservation,
)
from app.models.enums import AppRole, InstrumentStatus, InstrumentType
from app.rules.release import (
    MakerCheckerViolation,
    assert_maker_checker,
    check_release_eligibility,
)


def _make_institution_and_instrument(db_session, status=InstrumentStatus.MATURED):
    inst = Institution(
        aicte_code=f"R-{uuid.uuid4().hex[:8]}", name="Release Test Institution"
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-R-{uuid.uuid4().hex[:6]}",
        amount=1,
        status=status,
    )
    db_session.add(instrument)
    db_session.flush()
    return inst, instrument


def test_eligible_when_matured_with_no_blockers(db_session):
    _, instrument = _make_institution_and_instrument(db_session)
    result = check_release_eligibility(db_session, instrument)
    assert result.eligible is True
    assert all(item.passed for item in result.checklist)


def test_not_eligible_when_not_yet_matured(db_session):
    _, instrument = _make_institution_and_instrument(
        db_session, status=InstrumentStatus.ACTIVE
    )
    result = check_release_eligibility(db_session, instrument)
    assert result.eligible is False
    term_item = next(i for i in result.checklist if i.rule_id == "term_served")
    assert term_item.passed is False
    assert term_item.citation == "APH 2024-27, cl. 6.46"


def test_not_eligible_with_open_discrepancy(db_session):
    _, instrument = _make_institution_and_instrument(db_session)
    db_session.add(
        Discrepancy(
            institution_id=instrument.institution_id,
            instrument_id=instrument.id,
            field="amount",
            declared_value="100",
            extracted_value="90",
            severity="high",
            status="open",
        )
    )
    db_session.flush()
    result = check_release_eligibility(db_session, instrument)
    assert result.eligible is False
    item = next(i for i in result.checklist if i.rule_id == "no_open_discrepancies")
    assert item.passed is False


def test_not_eligible_with_pending_scrutiny_observation(db_session):
    _, instrument = _make_institution_and_instrument(db_session)
    db_session.add(
        ScrutinyObservation(
            institution_id=instrument.institution_id,
            instrument_id=instrument.id,
            observation="Needs clarification on tenor",
            status="open",
        )
    )
    db_session.flush()
    result = check_release_eligibility(db_session, instrument)
    assert result.eligible is False
    item = next(i for i in result.checklist if i.rule_id == "no_pending_observations")
    assert item.passed is False


def test_not_eligible_with_unpaid_penalty(db_session):
    _, instrument = _make_institution_and_instrument(db_session)
    db_session.add(
        Penalty(
            institution_id=instrument.institution_id,
            instrument_id=instrument.id,
            type="late_submission",
            amount=1000,
            reason="Late by 45 days",
            status="unpaid",
        )
    )
    db_session.flush()
    result = check_release_eligibility(db_session, instrument)
    assert result.eligible is False
    item = next(i for i in result.checklist if i.rule_id == "no_unpaid_penalties")
    assert item.passed is False


def _make_users(db_session, institution_id):
    requester = AppUser(
        institution_id=institution_id,
        keycloak_sub=f"kc-{uuid.uuid4().hex[:8]}",
        email=f"req-{uuid.uuid4().hex[:8]}@example.test",
        full_name="Requester",
        role=AppRole.INSTITUTION_SUBMITTER,
    )
    scrutiny_officer = AppUser(
        keycloak_sub=f"kc-{uuid.uuid4().hex[:8]}",
        email=f"so-{uuid.uuid4().hex[:8]}@example.test",
        full_name="Scrutiny Officer",
        role=AppRole.SCRUTINY_OFFICER,
    )
    competent_authority = AppUser(
        keycloak_sub=f"kc-{uuid.uuid4().hex[:8]}",
        email=f"ca-{uuid.uuid4().hex[:8]}@example.test",
        full_name="Competent Authority",
        role=AppRole.COMPETENT_AUTHORITY,
    )
    db_session.add_all([requester, scrutiny_officer, competent_authority])
    db_session.flush()
    return requester, scrutiny_officer, competent_authority


def test_maker_checker_blocks_scrutiny_officer_approving_own_file(db_session):
    inst, instrument = _make_institution_and_instrument(db_session)
    requester, scrutiny_officer, _ = _make_users(db_session, inst.id)
    rr = ReleaseRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        requested_by=requester.id,
        scrutiny_officer_id=scrutiny_officer.id,
    )
    db_session.add(rr)
    db_session.flush()

    with pytest.raises(MakerCheckerViolation, match="scrutiny officer"):
        assert_maker_checker(
            approver_id=str(scrutiny_officer.id),
            approver_role="competent_authority",
            release_request=rr,
        )


def test_maker_checker_blocks_requester_self_approval(db_session):
    inst, instrument = _make_institution_and_instrument(db_session)
    requester, scrutiny_officer, _ = _make_users(db_session, inst.id)
    rr = ReleaseRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        requested_by=requester.id,
        scrutiny_officer_id=scrutiny_officer.id,
    )
    db_session.add(rr)
    db_session.flush()

    with pytest.raises(MakerCheckerViolation, match="requester"):
        assert_maker_checker(
            approver_id=str(requester.id),
            approver_role="competent_authority",
            release_request=rr,
        )


def test_maker_checker_blocks_wrong_role():
    rr = ReleaseRequest(
        institution_id=uuid.uuid4(),
        instrument_id=uuid.uuid4(),
    )
    with pytest.raises(MakerCheckerViolation, match="not authorized"):
        assert_maker_checker(
            approver_id=str(uuid.uuid4()),
            approver_role="scrutiny_officer",
            release_request=rr,
        )


def test_maker_checker_allows_independent_competent_authority(db_session):
    inst, instrument = _make_institution_and_instrument(db_session)
    requester, scrutiny_officer, competent_authority = _make_users(db_session, inst.id)
    rr = ReleaseRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        requested_by=requester.id,
        scrutiny_officer_id=scrutiny_officer.id,
    )
    db_session.add(rr)
    db_session.flush()

    # Must not raise.
    assert_maker_checker(
        approver_id=str(competent_authority.id),
        approver_role="competent_authority",
        release_request=rr,
    )
