"""HTTP-level tests for GET /v1/queues/intake and /v1/queues/scrutiny
(app.queues.router). No client ever called these endpoints before mobile's
Tasks screen was wired to them, and no test exercised them either: they
returned every institution's pending onboarding requests and submitted/
in-scrutiny instruments to any caller with VIEW permission, regardless of
the caller's own institution — a cross-tenant data leak (CLAUDE.md
non-negotiable #6: default deny / tenant isolation). Regression guard for
the institution-scoping fix.
"""

import uuid

from fastapi.testclient import TestClient

from app.auth.deps import create_access_token
from app.main import app
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import AppRole, InstrumentStatus, InstrumentType

client = TestClient(app)


def _make_institution_with_submitted_instrument(db_session, *, suffix: str):
    inst = Institution(
        id=uuid.uuid4(),
        aicte_code=f"QUE-{suffix}-{uuid.uuid4().hex[:6]}",
        name=f"Institute of Queue Testing {suffix}",
    )
    db_session.add(inst)
    db_session.flush()

    user = AppUser(
        id=uuid.uuid4(),
        institution_id=inst.id,
        keycloak_sub=f"sub-que-{suffix}-{uuid.uuid4().hex[:8]}",
        email=f"viewer-{suffix}-{uuid.uuid4().hex[:6]}@eng.edu",
        full_name=f"Institution Viewer {suffix}",
        role=AppRole.INSTITUTION_VIEWER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    instrument = Instrument(
        id=uuid.uuid4(),
        institution_id=inst.id,
        type=InstrumentType.FDR,
        status=InstrumentStatus.SUBMITTED,
        instrument_number=f"QUE/{suffix}/0001",
        amount=3500000,
    )
    db_session.add(instrument)
    db_session.commit()
    return inst, user, instrument


def test_intake_queue_scoped_to_own_institution(db_session):
    _inst_a, user_a, instrument_a = _make_institution_with_submitted_instrument(
        db_session, suffix="A"
    )
    _inst_b, user_b, instrument_b = _make_institution_with_submitted_instrument(
        db_session, suffix="B"
    )

    token_a = create_access_token(user_a)
    res = client.get("/v1/queues/intake", headers={"Authorization": f"Bearer {token_a}"})

    assert res.status_code == 200
    case_ids = {row["case_id"] for row in res.json()}
    assert str(instrument_a.id) in case_ids
    assert str(instrument_b.id) not in case_ids

    token_b = create_access_token(user_b)
    res_b = client.get("/v1/queues/intake", headers={"Authorization": f"Bearer {token_b}"})
    case_ids_b = {row["case_id"] for row in res_b.json()}
    assert str(instrument_b.id) in case_ids_b
    assert str(instrument_a.id) not in case_ids_b


def test_scrutiny_queue_scoped_to_own_institution(db_session):
    _inst_a, user_a, instrument_a = _make_institution_with_submitted_instrument(
        db_session, suffix="C"
    )
    instrument_a.status = InstrumentStatus.SCRUTINY
    _inst_b, _user_b, instrument_b = _make_institution_with_submitted_instrument(
        db_session, suffix="D"
    )
    instrument_b.status = InstrumentStatus.SCRUTINY
    db_session.commit()

    token_a = create_access_token(user_a)
    res = client.get("/v1/queues/scrutiny", headers={"Authorization": f"Bearer {token_a}"})

    assert res.status_code == 200
    case_ids = {row["case_id"] for row in res.json()}
    assert str(instrument_a.id) in case_ids
    assert str(instrument_b.id) not in case_ids
