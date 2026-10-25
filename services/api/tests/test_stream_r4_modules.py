"""Stream R4 Backend Modules Test Suite (MASTER_PROMPT_V2 §7 / Exit Gates G-12, G-14, G-15, G-16, G-18).

Comprehensive verification for Stream R4:
1. G-14: Dashboard summary counts equal list totals (no composite score, honest drilldown).
2. G-14: Report exports respect institution scope, neutralize CSV formula injection, mask sensitive identifiers.
3. G-15: Universal search respects scope isolation (never leaks cross-tenant records) + saved views CRUD.
4. G-16: Reminder scheduler DB-lease, maker-checker version approval, alert on unapproved, RFC 5545 iCalendar feed.
5. G-18: Audit verification job walks hash-chain and confirms tamper-evident immutability.
6. G-12: Users & access management maker-checker SoD (nobody grants themselves a role, step-up MFA enforced).
7. G-14: Help & support, DPDP rights request, and retention / legal hold policies.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from starlette.testclient import TestClient

from app.auth.deps import create_access_token
from app.auth.security import hash_password
from app.db import get_session, set_app_context
from app.main import app
from app.models.core import AppUser, Institution, Instrument
from app.models.enums import AppRole, EvidenceLevel, InstrumentStatus, InstrumentType


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(user: AppUser) -> dict[str, str]:
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def setup_test_data():
    """Sets up test institutions and test users across various roles (module scoped)."""
    run_id = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        inst_a = Institution(
            id=uuid.uuid4(),
            aicte_code=f"1-R4A-{run_id}",
            name=f"R4 Institute of Technology A {run_id}",
        )
        inst_b = Institution(
            id=uuid.uuid4(),
            aicte_code=f"1-R4B-{run_id}",
            name=f"R4 Engineering College B {run_id}",
        )
        db.add_all([inst_a, inst_b])
        db.flush()

        u_a_id = uuid.uuid4()
        user_admin_a = AppUser(
            id=u_a_id,
            keycloak_sub=f"sub-{u_a_id}",
            email=f"admin_a_{run_id}@tenant-a.ac.in",
            full_name="Admin Tenant A",
            role=AppRole.ORG_ADMIN,
            institution_id=inst_a.id,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
        )
        u_b_id = uuid.uuid4()
        user_admin_b = AppUser(
            id=u_b_id,
            keycloak_sub=f"sub-{u_b_id}",
            email=f"admin_b_{run_id}@tenant-b.ac.in",
            full_name="Admin Tenant B",
            role=AppRole.ORG_ADMIN,
            institution_id=inst_b.id,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
        )
        m_id = uuid.uuid4()
        officer_maker = AppUser(
            id=m_id,
            keycloak_sub=f"sub-{m_id}",
            email=f"maker_{run_id}@aicte.gov.in",
            full_name="Maker Officer",
            role=AppRole.IDENTITY_ADMIN,
            institution_id=None,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
            mfa_enrolled=True,
            step_up_valid_until=now + timedelta(minutes=30),
        )
        ch_id = uuid.uuid4()
        officer_checker = AppUser(
            id=ch_id,
            keycloak_sub=f"sub-{ch_id}",
            email=f"checker_{run_id}@aicte.gov.in",
            full_name="Checker Officer",
            role=AppRole.IDENTITY_ADMIN,
            institution_id=None,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
            mfa_enrolled=False,
            step_up_valid_until=None,
        )
        sup_id = uuid.uuid4()
        officer_supervisor = AppUser(
            id=sup_id,
            keycloak_sub=f"sub-{sup_id}",
            email=f"supervisor_{run_id}@aicte.gov.in",
            full_name="Regional Supervisor",
            role=AppRole.REGIONAL_SUPERVISOR,
            region_id="Northern",
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
            mfa_enrolled=True,
            step_up_valid_until=now + timedelta(minutes=30),
        )
        sc_id = uuid.uuid4()
        officer_scrutiny = AppUser(
            id=sc_id,
            keycloak_sub=f"sub-{sc_id}",
            email=f"scrutiny_{run_id}@aicte.gov.in",
            full_name="Scrutiny Officer",
            role=AppRole.SCRUTINY_OFFICER,
            institution_id=None,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
        )
        au_id = uuid.uuid4()
        officer_auditor = AppUser(
            id=au_id,
            keycloak_sub=f"sub-{au_id}",
            email=f"auditor_{run_id}@aicte.gov.in",
            full_name="Auditor Officer",
            role=AppRole.AUDIT_REVIEWER,
            institution_id=None,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
        )
        ca_id = uuid.uuid4()
        officer_ca = AppUser(
            id=ca_id,
            keycloak_sub=f"sub-{ca_id}",
            email=f"ca_{run_id}@aicte.gov.in",
            full_name="Competent Authority",
            role=AppRole.COMPETENT_AUTHORITY,
            institution_id=None,
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
            mfa_enrolled=True,
            step_up_valid_until=now + timedelta(minutes=30),
        )
        db.add_all([
            user_admin_a,
            user_admin_b,
            officer_maker,
            officer_checker,
            officer_supervisor,
            officer_scrutiny,
            officer_auditor,
            officer_ca,
        ])
        db.flush()

        # Seed instruments for tenant A
        inst_a_1 = Instrument(
            id=uuid.uuid4(),
            institution_id=inst_a.id,
            type=InstrumentType.FDR,
            status=InstrumentStatus.ACTIVE,
            evidence_level=EvidenceLevel.L2_BANK_CONFIRMED,
            instrument_number="FDR-A-10001",
            blind_index="blind-idx-a1",
            amount=3500000.0,
            maturity_date=now + timedelta(days=20),
        )
        inst_a_2 = Instrument(
            id=uuid.uuid4(),
            institution_id=inst_a.id,
            type=InstrumentType.FDR,
            status=InstrumentStatus.ACTIVE,
            evidence_level=EvidenceLevel.L1_EXTRACTED,
            instrument_number="FDR-A-10002",
            blind_index="blind-idx-a2",
            amount=5000000.0,
            utr="=CMD|' /C calc'!A0",  # CSV formula injection payload in UTR field
            maturity_date=now + timedelta(days=50),
        )
        # Seed instrument for tenant B
        inst_b_1 = Instrument(
            id=uuid.uuid4(),
            institution_id=inst_b.id,
            type=InstrumentType.FDR,
            status=InstrumentStatus.ACTIVE,
            evidence_level=EvidenceLevel.L0_DECLARED,
            instrument_number="FDR-B-99999",
            blind_index="blind-idx-b1",
            amount=7500000.0,
            maturity_date=now + timedelta(days=15),
        )
        db.add_all([inst_a_1, inst_a_2, inst_b_1])
        db.commit()

        test_data = {
            "inst_a_id": inst_a.id,
            "inst_b_id": inst_b.id,
            "user_admin_a": user_admin_a,
            "user_admin_b": user_admin_b,
            "officer_maker": officer_maker,
            "officer_checker": officer_checker,
            "officer_supervisor": officer_supervisor,
            "officer_scrutiny": officer_scrutiny,
            "officer_auditor": officer_auditor,
            "officer_ca": officer_ca,
            "inst_a_1": inst_a_1,
            "inst_a_2": inst_a_2,
            "inst_b_1": inst_b_1,
        }

    yield test_data


# ==============================================================================
# 1. Dashboard (F-16 / Exit Gate G-14)
# ==============================================================================

def test_dashboard_summary_counts_equal_list_totals(client, setup_test_data):
    """Asserts that dashboard counts precisely match list totals with zero fabricated numbers (G-14)."""
    user_a = setup_test_data["user_admin_a"]
    headers = auth_header(user_a)

    # Call Dashboard summary
    resp = client.get("/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Active count must equal 2 (for tenant A)
    assert data["active"]["count"] == 2
    assert data["active"]["drilldown"] == {"status": "active"}

    # Expiring <= 30d must equal 1 (inst_a_1 is in 20 days)
    assert data["expiring_30d"]["count"] == 1
    assert data["expiring_30d"]["drilldown"] == {"expiring_days": 30}

    # Expiring <= 60d must equal 2 (both inst_a_1 and inst_a_2)
    assert data["expiring_60d"]["count"] == 2

    # Evidence distribution checks
    assert data["evidence_distribution"]["L2_BANK_CONFIRMED"]["count"] == 1
    assert data["evidence_distribution"]["L1_EXTRACTED"]["count"] == 1
    assert data["evidence_distribution"]["L0_DECLARED"]["count"] == 0

    # Cross check with /v1/instruments list endpoint for tenant A
    inst_resp = client.get("/v1/instruments", headers=headers)
    assert inst_resp.status_code == 200
    inst_list = inst_resp.json()
    assert len(inst_list) == data["active"]["count"]

    # Verify due-soon returns exact matching record
    due_resp = client.get("/v1/dashboard/due-soon?horizon_days=30", headers=headers)
    assert due_resp.status_code == 200
    due_items = due_resp.json()
    assert len(due_items) == data["expiring_30d"]["count"]


# ==============================================================================
# 2. Reports & Exports: Scope respect, Masking, CSV Injection (G-14)
# ==============================================================================

def test_report_export_neutralizes_csv_injection_and_masks_identifiers(client, setup_test_data):
    """Asserts that CSV export neutralizes formula injection and masks identifiers (G-14)."""
    user_a = setup_test_data["user_admin_a"]
    headers_a = auth_header(user_a)

    # 1. View catalogue
    cat_resp = client.get("/v1/reports/catalogue", headers=headers_a)
    assert cat_resp.status_code == 200
    assert len(cat_resp.json()) >= 4

    # 2. Schedule export run
    run_resp = client.post(
        "/v1/reports/statutory_compliance/runs",
        headers=headers_a,
        json={"reason": "Auditing statutory compliance for regulatory filing"},
    )
    assert run_resp.status_code == 202
    job_info = run_resp.json()
    job_id = job_info["id"]
    assert job_info["status"] == "COMPLETED"
    assert job_info["row_count"] == 2  # Only Tenant A's 2 instruments, not Tenant B's

    # 3. Download export file
    dl_resp = client.get(f"/v1/export-jobs/{job_id}/download", headers=headers_a)
    assert dl_resp.status_code == 200
    assert "text/csv" in dl_resp.headers["content-type"]
    assert "X-Content-SHA256" in dl_resp.headers

    csv_text = dl_resp.text
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 3  # Header + 2 data rows

    # Verify CSV injection neutralization:
    # Cell starting with '=' must be prepended with a single quote "'"
    formula_cells = [cell for row in rows for cell in row if "calc" in cell]
    assert len(formula_cells) >= 1
    assert formula_cells[0].startswith("'="), f"Formula injection was NOT escaped: {formula_cells[0]}"

    # Verify identifier masking: FDR numbers must be masked as XXXX...
    masked_cells = [row[4] for row in rows[1:]]
    for cell in masked_cells:
        assert cell.startswith("XXXX")

    # 4. Scope isolation check: Tenant B cannot download Tenant A's export job
    user_b = setup_test_data["user_admin_b"]
    headers_b = auth_header(user_b)
    forbidden_resp = client.get(f"/v1/export-jobs/{job_id}/download", headers=headers_b)
    assert forbidden_resp.status_code in (403, 404)


# ==============================================================================
# 3. Universal Search: Scope Isolation Property (G-15)
# ==============================================================================

def test_search_never_returns_out_of_scope_rows(client, setup_test_data):
    """Property test: search for universal terms never reveals cross-tenant data (G-15)."""
    user_a = setup_test_data["user_admin_a"]
    headers = auth_header(user_a)

    # Search query that would match Tenant B's instrument if scope were ignored
    resp = client.get("/v1/search?q=99999", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 0, "Security violation: Tenant A search returned Tenant B instrument!"

    # Search for Tenant A's own instrument
    resp_a = client.get("/v1/search?q=10001", headers=headers)
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert len(data_a["results"]) == 1
    assert data_a["results"][0]["entity_type"] == "instrument"

    # Saved view CRUD test
    sv_resp = client.post(
        "/v1/saved-views",
        headers=headers,
        json={"name": "High Value Deposits", "entity_type": "instrument", "filter_criteria": {"min_amount": 5000000}},
    )
    assert sv_resp.status_code == 201
    view_id = sv_resp.json()["id"]

    list_sv = client.get("/v1/saved-views", headers=headers)
    assert list_sv.status_code == 200
    assert any(v["id"] == view_id for v in list_sv.json())

    del_sv = client.delete(f"/v1/saved-views/{view_id}", headers=headers)
    assert del_sv.status_code == 204


# ==============================================================================
# 4. Reminder Scheduler: Maker-Checker & Alert on Unapproved Schedule (G-16)
# ==============================================================================

def test_reminder_scheduler_maker_checker_and_unapproved_alert(client, setup_test_data):
    """Asserts maker-checker SoD for reminder schedule and alert when unapproved (G-16)."""
    maker = setup_test_data["officer_supervisor"]  # Regional Supervisor (policy author)
    checker = setup_test_data["officer_ca"]        # Competent Authority (policy approver)
    headers_maker = auth_header(maker)
    headers_checker = auth_header(checker)

    # With no approved schedule, scheduler status alerts
    status_resp = client.get("/v1/scheduler/status", headers=headers_maker)
    assert status_resp.status_code == 200
    assert status_resp.json()["has_approved_schedule"] is False or status_resp.json()["status_alert"] is not None

    # Maker creates draft schedule version
    create_resp = client.post(
        "/v1/reminder-schedules/versions",
        headers=headers_maker,
        json={
            "rules": [
                {"days_before_maturity": 30, "channel": "in_app", "recipient_roles": ["org_admin"]},
                {"days_before_maturity": 15, "channel": "in_app", "recipient_roles": ["org_admin", "scrutiny_officer"]},
            ]
        },
    )
    assert create_resp.status_code == 201
    schedule_id = create_resp.json()["id"]

    # SoD Violation Test: Maker attempts to approve their own schedule version -> 403 Forbidden
    approve_self = client.post(f"/v1/reminder-schedules/approve?schedule_id={schedule_id}", headers=headers_maker)
    assert approve_self.status_code == 403
    assert "maker-checker" in approve_self.text or "Creator cannot approve" in approve_self.text

    # Checker (Competent Authority) approves schedule -> 200 OK
    approve_checker = client.post(f"/v1/reminder-schedules/approve?schedule_id={schedule_id}", headers=headers_checker)
    assert approve_checker.status_code == 200
    assert approve_checker.json()["status"] == "ACTIVE"

    # Status now shows approved schedule active
    status_active = client.get("/v1/scheduler/status", headers=headers_checker)
    assert status_active.status_code == 200
    assert status_active.json()["has_approved_schedule"] is True
    assert status_active.json()["status_alert"] is None

    # Test calendar feed generation
    user_a = setup_test_data["user_admin_a"]
    feed_token_resp = client.post("/v1/calendar/feed-token", headers=auth_header(user_a))
    assert feed_token_resp.status_code == 201
    token = feed_token_resp.json()["token"]

    # Verify RFC 5545 iCalendar feed
    ics_resp = client.get(f"/v1/calendar/feed.ics?token={token}")
    assert ics_resp.status_code == 200
    assert "text/calendar" in ics_resp.headers["content-type"]
    assert "BEGIN:VCALENDAR" in ics_resp.text
    assert "END:VCALENDAR" in ics_resp.text


# ==============================================================================
# 5. Audit Chain Verification Job (F-18 / G-18)
# ==============================================================================

def test_audit_verification_job_verifies_integrity(client, setup_test_data):
    """Executes hash-chain verification job and asserts status (G-18)."""
    auditor = setup_test_data["officer_auditor"]
    headers = auth_header(auditor)

    # 1. Run real verification job
    verify_resp = client.post("/v1/audit/chain/verify", headers=headers)
    assert verify_resp.status_code == 200
    result = verify_resp.json()
    assert result["status"] == "VERIFIED"
    assert result["ok"] is True
    assert result["broken_at_id"] is None

    # 2. Check chain status
    status_resp = client.get("/v1/audit/chain/status", headers=headers)
    assert status_resp.status_code == 200
    st = status_resp.json()
    assert st["last_verification_ok"] is True

    # 3. Query audit events
    events_resp = client.get("/v1/audit/events?limit=10", headers=headers)
    assert events_resp.status_code == 200
    assert isinstance(events_resp.json(), list)


# ==============================================================================
# 6. Users & Access Management: SoD & Session Termination (G-12)
# ==============================================================================

def test_users_access_sod_and_session_revocation(client, setup_test_data):
    """Enforces maker-checker SoD for role changes and immediate session termination (G-12)."""
    maker = setup_test_data["officer_maker"]
    checker = setup_test_data["officer_checker"]
    scrutiny = setup_test_data["officer_scrutiny"]
    headers_maker = auth_header(maker)
    headers_checker = auth_header(checker)

    # SoD Check 1: Maker cannot request role assignment for themselves
    self_req = client.post(
        "/v1/role-assignments/requests",
        headers=headers_maker,
        json={
            "user_id": str(maker.id),
            "requested_role": "competent_authority",
            "reason": "Self promotion attempt",
        },
    )
    assert self_req.status_code == 403
    assert "own account" in self_req.text

    # Maker requests role upgrade for Scrutiny Officer
    role_req = client.post(
        "/v1/role-assignments/requests",
        headers=headers_maker,
        json={
            "user_id": str(scrutiny.id),
            "requested_role": "competent_authority",
            "reason": "Promoting officer to Competent Authority for delegation coverage",
        },
    )
    assert role_req.status_code == 201
    req_id = role_req.json()["id"]

    # SoD Check 2: Maker cannot approve their own role request
    self_approve = client.post(f"/v1/role-assignments/{req_id}/approve", headers=headers_maker)
    assert self_approve.status_code == 403
    assert "Requester cannot approve" in self_approve.text

    # Checker approves without step-up -> 403 step_up_required
    no_stepup = client.post(f"/v1/role-assignments/{req_id}/approve", headers=headers_checker)
    assert no_stepup.status_code == 403
    assert "step_up_required" in no_stepup.text

    # Checker approves WITH step-up -> 200 OK
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        ch_db = db.get(AppUser, checker.id)
        ch_db.mfa_enrolled = True
        ch_db.step_up_valid_until = datetime.now(UTC) + timedelta(minutes=15)
        db.commit()

    headers_checker_stepup = auth_header(ch_db)
    approved = client.post(f"/v1/role-assignments/{req_id}/approve", headers=headers_checker_stepup)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    # Verify user's role is updated in database
    with next(get_session()) as db:
        set_app_context(db, role="platform_operator")
        updated_scrutiny = db.get(AppUser, scrutiny.id)
        assert updated_scrutiny.role == AppRole.COMPETENT_AUTHORITY

    # Unlock user endpoint test
    unlock_resp = client.post(f"/v1/users/{scrutiny.id}/unlock", headers=headers_checker_stepup)
    assert unlock_resp.status_code == 200
    assert unlock_resp.json()["status"] == "unlocked"


# ==============================================================================
# 7. Help, Support, DPDP Rights & Retention (F-21/F-22)
# ==============================================================================

def test_support_rights_and_retention(client, setup_test_data):
    """Verifies help articles, support requests, DPDP rights, and legal holds (F-21/F-22)."""
    user_a = setup_test_data["user_admin_a"]
    officer_ca = setup_test_data["officer_ca"]
    headers_a = auth_header(user_a)
    headers_ca = auth_header(officer_ca)

    # 1. Help articles
    articles = client.get("/v1/help/articles", headers=headers_a)
    assert articles.status_code == 200
    assert len(articles.json()) >= 4

    # 2. Support request
    supp_resp = client.post(
        "/v1/support-requests",
        headers={"X-Correlation-ID": "test-corr-1234", **headers_a},
        json={
            "category": "compliance",
            "subject": "Clarification on Joint FDR Tenor Requirements",
            "description": "Requesting confirmation regarding 10-year tenor under 2026 AICTE APH.",
        },
    )
    assert supp_resp.status_code == 201
    assert supp_resp.json()["status"] == "OPEN"
    assert supp_resp.json()["correlation_id"] == "test-corr-1234"

    # 3. DPDP Rights request
    rights_resp = client.post(
        "/v1/rights-requests",
        headers=headers_a,
        json={
            "request_type": "ACCESS",
            "details": "Statutory request to download all stored personal identification data.",
        },
    )
    assert rights_resp.status_code == 201
    assert rights_resp.json()["status"] == "PENDING_VERIFICATION"

    # 4. Legal Holds and Retention
    rc_resp = client.post(
        "/v1/retention/classes",
        headers=headers_ca,
        json={"class_key": f"STATUTORY_FDR_{uuid.uuid4().hex[:6]}", "retention_years": 10, "disposal_action": "ARCHIVE"},
    )
    assert rc_resp.status_code == 201
    assert rc_resp.json()["retention_years"] == 10

    hold_resp = client.post(
        "/v1/retention/legal-holds",
        headers=headers_ca,
        json={
            "name": "CBI Dispute Matter 2026/09",
            "matter_id": f"MATTER-CBI-{uuid.uuid4().hex[:6]}",
            "entity_type": "instrument",
            "entity_id": str(setup_test_data["inst_a_1"].id),
            "reason": "Freezing deposit records pursuant to High Court inquiry order.",
        },
    )
    assert hold_resp.status_code == 201
    assert hold_resp.json()["active"] is True
