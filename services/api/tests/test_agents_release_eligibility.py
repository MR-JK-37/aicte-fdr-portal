import uuid

from app.agents.release_eligibility import (
    ApprovalDecision,
    resume_release_review,
    start_release_review,
)
from app.models import AppUser, Institution, Instrument, ReleaseRequest
from app.models.enums import AppRole, InstrumentStatus, InstrumentType


def _make_instrument(db_session, status):
    inst = Institution(
        aicte_code=f"RE-{uuid.uuid4().hex[:8]}",
        name="Release-Eligibility Test Institution",
    )
    db_session.add(inst)
    db_session.flush()
    instrument = Instrument(
        institution_id=inst.id,
        type=InstrumentType.FDR,
        instrument_number=f"FDR-RE-{uuid.uuid4().hex[:6]}",
        amount=500000,
        status=status,
    )
    db_session.add(instrument)
    db_session.flush()
    return inst, instrument


def _make_users(db_session, institution_id):
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
    db_session.add_all([scrutiny_officer, competent_authority])
    db_session.flush()
    return scrutiny_officer, competent_authority


def test_ineligible_instrument_never_reaches_interrupt(db_session):
    inst, instrument = _make_instrument(
        db_session, InstrumentStatus.ACTIVE
    )  # not yet matured
    rr = ReleaseRequest(institution_id=inst.id, instrument_id=instrument.id)
    db_session.add(rr)
    db_session.flush()

    result = start_release_review(
        db_session, instrument, rr, thread_id=str(uuid.uuid4())
    )
    assert "__interrupt__" not in result
    assert result["outcome"] == "not_eligible"
    assert instrument.status == InstrumentStatus.ACTIVE  # untouched


def test_eligible_instrument_pauses_for_human_approval(db_session):
    inst, instrument = _make_instrument(db_session, InstrumentStatus.RELEASE_REQUESTED)
    rr = ReleaseRequest(institution_id=inst.id, instrument_id=instrument.id)
    db_session.add(rr)
    db_session.flush()

    result = start_release_review(
        db_session, instrument, rr, thread_id=str(uuid.uuid4())
    )
    assert "__interrupt__" in result
    payload = result["__interrupt__"][0].value
    assert payload["instrument_id"] == str(instrument.id)
    assert all(item["passed"] for item in payload["checklist"])
    # Nothing committed yet — the graph is genuinely paused, not faked.
    assert instrument.status == InstrumentStatus.RELEASE_REQUESTED


def test_resume_with_approval_releases_the_instrument(db_session):
    inst, instrument = _make_instrument(db_session, InstrumentStatus.RELEASE_REQUESTED)
    scrutiny_officer, competent_authority = _make_users(db_session, inst.id)
    rr = ReleaseRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        scrutiny_officer_id=scrutiny_officer.id,
    )
    db_session.add(rr)
    db_session.flush()

    thread_id = str(uuid.uuid4())
    start_release_review(db_session, instrument, rr, thread_id=thread_id)

    result = resume_release_review(
        db_session,
        instrument,
        rr,
        thread_id=thread_id,
        decision=ApprovalDecision(
            approve=True,
            approver_id=str(competent_authority.id),
            approver_role="competent_authority",
            reason="Checklist clear, approving release",
        ),
    )
    assert result["outcome"] == "released"
    assert instrument.status == InstrumentStatus.RELEASED


def test_resume_blocks_scrutiny_officer_approving_own_file(db_session):
    inst, instrument = _make_instrument(db_session, InstrumentStatus.RELEASE_REQUESTED)
    scrutiny_officer, _ = _make_users(db_session, inst.id)
    rr = ReleaseRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        scrutiny_officer_id=scrutiny_officer.id,
    )
    db_session.add(rr)
    db_session.flush()

    thread_id = str(uuid.uuid4())
    start_release_review(db_session, instrument, rr, thread_id=thread_id)

    result = resume_release_review(
        db_session,
        instrument,
        rr,
        thread_id=thread_id,
        decision=ApprovalDecision(
            approve=True,
            approver_id=str(scrutiny_officer.id),  # same person who handled scrutiny
            approver_role="competent_authority",
            reason="trying to approve my own file",
        ),
    )
    assert result["outcome"].startswith("rejected_maker_checker")
    assert instrument.status == InstrumentStatus.RELEASE_REQUESTED  # not released


def test_resume_with_rejection_does_not_release(db_session):
    inst, instrument = _make_instrument(db_session, InstrumentStatus.RELEASE_REQUESTED)
    scrutiny_officer, competent_authority = _make_users(db_session, inst.id)
    rr = ReleaseRequest(
        institution_id=inst.id,
        instrument_id=instrument.id,
        scrutiny_officer_id=scrutiny_officer.id,
    )
    db_session.add(rr)
    db_session.flush()

    thread_id = str(uuid.uuid4())
    start_release_review(db_session, instrument, rr, thread_id=thread_id)

    result = resume_release_review(
        db_session,
        instrument,
        rr,
        thread_id=thread_id,
        decision=ApprovalDecision(
            approve=False,
            approver_id=str(competent_authority.id),
            approver_role="competent_authority",
            reason="Discrepancy found on re-check",
        ),
    )
    assert result["outcome"] == "rejected_by_approver"
    assert instrument.status == InstrumentStatus.RELEASE_REQUESTED
