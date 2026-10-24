import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.authz import (
    PermissionVerb,
    Principal,
    StepUpRequiredError,
    authorise,
)
from app.models.enums import AppRole


def test_every_action_in_step_up_required_demands_fresh_step_up():
    """MASTER_PROMPT §8.1 / §8.4: Step-up MFA is mandatory immediately before:

    approve/reject release, execute release record, change policy, grant/revoke roles,
    change connector state, unmask identifiers in bulk, break-glass.
    """
    now = datetime.now(UTC)

    # 1. Test Competent Authority trying to approve release without step-up
    ca_principal = Principal(
        id=uuid.uuid4(),
        email="ca@example.com",
        full_name="Competent Authority",
        role=AppRole.COMPETENT_AUTHORITY,
        is_active=True,
        mfa_enrolled=True,
        step_up_valid_until=None,  # No fresh step-up
        delegation_limit=Decimal("50000000.00"),
    )

    with pytest.raises(StepUpRequiredError) as exc:
        authorise(ca_principal, PermissionVerb.APPROVE_RELEASE, now=now)
    assert exc.value.code == "step_up_required"

    # Step up expired 1 minute ago
    ca_principal.step_up_valid_until = now - timedelta(minutes=1)
    with pytest.raises(StepUpRequiredError):
        authorise(ca_principal, PermissionVerb.APPROVE_RELEASE, now=now)

    # Valid step up (valid for next 10 minutes)
    ca_principal.step_up_valid_until = now + timedelta(minutes=10)
    assert authorise(ca_principal, PermissionVerb.APPROVE_RELEASE, now=now) is True


def test_platform_operator_configure_integrations_step_up():
    now = datetime.now(UTC)
    operator = Principal(
        id=uuid.uuid4(),
        email="operator@example.com",
        full_name="Platform Operator",
        role=AppRole.PLATFORM_OPERATOR,
        is_active=True,
        mfa_enrolled=False,
        step_up_valid_until=None,
    )

    with pytest.raises(StepUpRequiredError):
        authorise(operator, PermissionVerb.CONFIGURE_INTEGRATIONS, now=now)

    # Enrolled in MFA and stepped up
    operator.mfa_enrolled = True
    operator.step_up_valid_until = now + timedelta(minutes=15)
    assert authorise(operator, PermissionVerb.CONFIGURE_INTEGRATIONS, now=now) is True


def test_identity_admin_manage_roles_step_up():
    now = datetime.now(UTC)
    admin = Principal(
        id=uuid.uuid4(),
        email="id_admin@example.com",
        full_name="Identity Admin",
        role=AppRole.IDENTITY_ADMIN,
        is_active=True,
        mfa_enrolled=True,
        step_up_valid_until=None,
    )

    with pytest.raises(StepUpRequiredError):
        authorise(admin, PermissionVerb.MANAGE_ROLES, now=now)

    admin.step_up_valid_until = now + timedelta(minutes=5)
    assert authorise(admin, PermissionVerb.MANAGE_ROLES, now=now) is True
