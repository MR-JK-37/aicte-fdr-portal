import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.authz import (
    ROLE_PERMISSIONS_MATRIX,
    PermissionVerb,
    Principal,
    StepUpRequiredError,
    authorise,
)
from app.models.enums import DISABLED_ROLES, AppRole
from app.problem_json import ForbiddenError, UnauthenticatedError


def test_exhaustive_role_action_negative_matrix():
    """Generates the full 13-role x 25-verb negative test matrix.

    Asserts that:
    1. Every (role, verb) pair explicitly in ROLE_PERMISSIONS_MATRIX succeeds (with step-up if required).
    2. Any (role, verb) pair NOT in ROLE_PERMISSIONS_MATRIX strictly raises ForbiddenError.
    3. Disabled roles (e.g. bank_verifier) always raise ForbiddenError.
    """
    valid_until = datetime.now(UTC) + timedelta(minutes=15)

    all_roles = list(AppRole)
    all_verbs = list(PermissionVerb)

    assert len(all_roles) == 13, f"Expected 13 roles, got {len(all_roles)}"
    assert len(all_verbs) == 26, f"Expected 26 permission verbs, got {len(all_verbs)}"

    allowed_count = 0
    denied_count = 0

    for role in all_roles:
        principal = Principal(
            id=uuid.uuid4(),
            email=f"{role.value}@example.com",
            full_name=f"User {role.value}",
            role=role,
            is_active=True,
            mfa_enrolled=True,
            step_up_valid_until=valid_until,
            delegation_limit=Decimal("100000000.00"),
        )

        expected_perms = ROLE_PERMISSIONS_MATRIX.get(role, {})
        is_disabled = role in DISABLED_ROLES

        for verb in all_verbs:
            act = verb.value
            is_expected_allowed = (act in expected_perms) and not is_disabled

            if is_expected_allowed:
                # Should authorise successfully
                assert authorise(principal, verb) is True
                allowed_count += 1
            else:
                # Must raise ForbiddenError
                with pytest.raises(ForbiddenError):
                    authorise(principal, verb)
                denied_count += 1

    total_checks = len(all_roles) * len(all_verbs)
    assert allowed_count + denied_count == total_checks
    assert total_checks == 13 * 26
    print(
        f"Role x Action Matrix verified: {allowed_count} allowed, {denied_count} denied out of {total_checks}"
    )


def test_inactive_principal_denied():
    principal = Principal(
        id=uuid.uuid4(),
        email="inactive@example.com",
        full_name="Inactive User",
        role=AppRole.ORG_ADMIN,
        is_active=False,
    )
    with pytest.raises(UnauthenticatedError):
        authorise(principal, PermissionVerb.VIEW)


def test_step_up_required_actions_without_step_up():
    """Privileged actions in STEP_UP_REQUIRED_ACTIONS must raise StepUpRequiredError if step-up is missing."""
    principal = Principal(
        id=uuid.uuid4(),
        email="operator@example.com",
        full_name="Platform Operator",
        role=AppRole.PLATFORM_OPERATOR,
        is_active=True,
        mfa_enrolled=False,
        step_up_valid_until=None,
    )

    with pytest.raises(StepUpRequiredError):
        authorise(principal, PermissionVerb.CONFIGURE_INTEGRATIONS)
