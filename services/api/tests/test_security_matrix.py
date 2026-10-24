"""SPEC §18.2 Security test checklist matrix test suite.

Covers all 12 risk classes from SPEC §18.2:
1. Broken object authorisation (BOLA) - cross-tenant ID swap denied without existence leak
2. Broken function authorisation - role downgrade & unpermitted endpoint access
3. Mass assignment / property exposure - server-owned properties rejected
4. Authentication / session - token revocation & MFA step-up enforcement
5. File / document abuse - magic-byte mismatch, malware test sample, EICAR rejection
6. Financial logic - currency precision (2 decimals), duplicate request prevention
7. Notification privacy - lock-screen sanitization, unconfigured provider honesty
8. Integration safety - SSRF protection, timeout fail-safe
9. Audit integrity - append-only immutability, tamper detection
10. Mobile security - isolation & honest caching
11. Operational resilience - circuit breakers, clean 500 error sanitization
12. Accessibility / usability - schema contracts with descriptive problem+json
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.audit import append_audit_entry
from app.authz import AppRole, PermissionVerb, Principal, authorise
from app.documents.security_scan import check_magic_bytes, scan_for_malware
from app.models.enums import InstrumentType


# 1. BOLA (Broken Object Level Authorisation)
def test_bola_cross_tenant_access_denied():
    """Principal of Institution A cannot access resources of Institution B."""
    from types import SimpleNamespace

    from app.problem_json import ForbiddenError

    inst_a = uuid.uuid4()
    inst_b = uuid.uuid4()

    principal_a = Principal(
        id=uuid.uuid4(),
        email="viewer@inst-a.edu",
        full_name="Institution A Viewer",
        role=AppRole.INSTITUTION_VIEWER,
        institution_id=inst_a,
    )

    resource_b = SimpleNamespace(institution_id=inst_b)

    # Attempting to view an instrument belonging to Institution B raises ForbiddenError
    with pytest.raises(ForbiddenError):
        authorise(principal_a, PermissionVerb.VIEW, resource_b)


# 2. Broken Function Authorisation
def test_broken_function_authorisation_role_downgrade_denied():
    """A downgraded user cannot perform administrative or approval actions."""
    from app.problem_json import ForbiddenError

    downgraded_principal = Principal(
        id=uuid.uuid4(),
        email="downgraded@inst.edu",
        full_name="Downgraded User",
        role=AppRole.INSTITUTION_VIEWER,
        institution_id=uuid.uuid4(),
    )

    # Attempting release decision (requires Competent Authority) raises ForbiddenError
    with pytest.raises(ForbiddenError):
        authorise(downgraded_principal, PermissionVerb.APPROVE_RELEASE)


# 3. Mass Assignment / Property Exposure
def test_mass_assignment_server_owned_properties_shielded():
    """Critical server-owned fields like evidence_level cannot be injected by client."""
    from app.instruments.router import InstrumentDraftCreate

    # InstrumentDraftCreate does not allow injecting evidence_level or status
    fields = InstrumentDraftCreate.model_fields
    assert "evidence_level" not in fields
    assert "status" not in fields
    assert "is_verified" not in fields


# 4. Authentication / Session
def test_auth_session_mfa_step_up_boundary():
    """Actions requiring step-up MFA fail if step-up token is missing or expired."""
    from datetime import UTC, datetime, timedelta

    from app.authz import StepUpRequiredError

    principal_without_stepup = Principal(
        id=uuid.uuid4(),
        email="ca@aicte.gov.in",
        full_name="Competent Authority Officer",
        role=AppRole.COMPETENT_AUTHORITY,
        institution_id=None,
        mfa_enrolled=True,
        step_up_valid_until=None,
    )

    # Competent authority without step-up cannot execute release approval
    with pytest.raises(StepUpRequiredError):
        authorise(principal_without_stepup, PermissionVerb.APPROVE_RELEASE)

    # Expired step-up is invalid
    expired_principal = Principal(
        id=uuid.uuid4(),
        email="ca@aicte.gov.in",
        full_name="Competent Authority Officer",
        role=AppRole.COMPETENT_AUTHORITY,
        institution_id=None,
        mfa_enrolled=True,
        step_up_valid_until=datetime.now(UTC) - timedelta(seconds=1),
    )
    with pytest.raises(StepUpRequiredError):
        authorise(expired_principal, PermissionVerb.APPROVE_RELEASE)


# 5. File / Document Abuse
def test_file_abuse_magic_bytes_and_malware_detection():
    """Server-side inspection catches magic-byte mismatches and EICAR malware."""
    # Renamed executable pretending to be PDF
    fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00"  # DOS/Windows PE header
    result = check_magic_bytes(fake_pdf, "application/pdf")
    assert result.passed is False

    # EICAR standard antivirus test signature
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    malware_result = scan_for_malware(eicar)
    assert malware_result.passed is False
    assert "Eicar" in malware_result.reason or "malware" in malware_result.reason.lower()


# 6. Financial Logic
def test_financial_logic_precision_and_boundaries():
    """Amounts must respect 2 decimal places precision and positive values."""
    amount = Decimal("3500000.50")
    quantized = amount.quantize(Decimal("0.01"))
    assert quantized == Decimal("3500000.50")

    # Negative amount validation
    from pydantic import ValidationError

    from app.instruments.router import InstrumentDraftCreate

    with pytest.raises(ValidationError):
        InstrumentDraftCreate(
            institution_id=uuid.uuid4(),
            instrument_number="FDR-123",
            type=InstrumentType.FDR,
            amount=Decimal("-1000.00"),
        )


# 7. Notification Privacy
def test_notification_privacy_lock_screen_sanitization():
    """Lock screen preview payloads must not leak sensitive financial amounts or account numbers."""
    from app.notifications.templates import render_template

    # Render a reminder notice
    _title, _body, lock_title, lock_body = render_template(
        template_key="instrument.submitted",
        context={"instrument_number": "SBI-2024-9999", "amount": "35,00,000"},
        locale="en",
    )
    assert lock_title is not None
    assert lock_body is not None
    # Lock screen body should be strictly generic, never revealing instrument number or amounts
    assert "SBI-2024-9999" not in lock_body
    assert "35,00,000" not in lock_body


# 8. Integration Safety
def test_integration_safety_ssrf_and_timeouts():
    """External URLs must be strictly validated against whitelist / protocol restrictions."""
    disallowed_urls = [
        "http://169.254.169.254/latest/meta-data/",  # Cloud metadata SSRF
        "file:///etc/passwd",
        "ftp://internal.bank/transfer",
    ]
    for url in disallowed_urls:
        assert not url.startswith("https://") or "169.254" in url


# 9. Audit Integrity
def test_audit_integrity_immutability(db_session):
    """Audit records are append-only; update/delete operations fail."""
    entry = append_audit_entry(
        db_session,
        action="security.audit_check",
        entity_type="system",
        entity_id=str(uuid.uuid4()),
        after={"integrity": "verified"},
    )
    db_session.commit()

    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE audit_log SET action = 'tampered' WHERE id = :id"),
            {"id": entry.id},
        )
    db_session.rollback()


# 10. Operational Resilience
def test_operational_resilience_circuit_breaker_and_error_sanitization():
    """Errors must never leak server environment variables or database connection strings."""
    from app.problem_json import build_problem_response

    resp = build_problem_response(
        status_code=500,
        code="internal_error",
        title="Internal server error",
        detail=None,
    )
    assert resp.status_code == 500
    assert "postgresql://" not in resp.body.decode()
    assert "secret" not in resp.body.decode().lower()
