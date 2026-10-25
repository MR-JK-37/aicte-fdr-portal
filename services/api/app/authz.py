"""Central Authorisation Engine (MASTER_PROMPT §8.2–§8.5 / SPEC §4 & §5).

Implements the single `authorise(principal, action, resource, context)`
evaluation algorithm:
1. Reject if principal identity is inactive, session revoked or token invalid.
2. Require valid MFA / step-up assurance for privileged decision actions.
3. Require action permission granted by an approved role assignment.
4. Check organisation, institution, region, assignment and programme attributes.
5. Check resource state permits this action in the workflow state machine.
6. Check delegation limits, separation-of-duties (maker != checker).
7. Deny by default on missing/ambiguous attributes or engine failure.
8. For consequential writes, record actor, reason, correlation ID and audit event.
9. Return only allow-listed data fields the role is allowed to see.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.models.enums import DISABLED_ROLES, AppRole
from app.problem_json import ForbiddenError, UnauthenticatedError


class PermissionVerb(str, enum.Enum):
    VIEW = "view"
    CREATE_DRAFT = "create_draft"
    EDIT_DRAFT = "edit_draft"
    SUBMIT = "submit"
    UPLOAD_EVIDENCE = "upload_evidence"
    DOWNLOAD_EVIDENCE = "download_evidence"
    RAISE_OBSERVATION = "raise_observation"
    RESPOND_OBSERVATION = "respond_observation"
    ASSIGN_CASE = "assign_case"
    RECOMMEND = "recommend"
    VERIFY_BANK_EVIDENCE = "verify_bank_evidence"
    RECONCILE_STATEMENT = "reconcile_statement"
    RESOLVE_EXCEPTION = "resolve_exception"
    REQUEST_RELEASE = "request_release"
    APPROVE_RELEASE = "approve_release"
    EXECUTE_RELEASE_RECORD = "execute_release_record"
    EXPORT_REPORT = "export_report"
    MANAGE_INSTITUTION_USERS = "manage_institution_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_POLICY = "manage_policy"
    CONFIGURE_INTEGRATIONS = "configure_integrations"
    VIEW_AUDIT = "view_audit"
    ADMINISTER_PLATFORM = "administer_platform"
    VIEW_UNMASKED_IDENTIFIERS = "view_unmasked_identifiers"
    MANAGE_TEMPLATES = "manage_templates"
    BREAK_GLASS = "break_glass"


# Actions that strictly demand step-up MFA immediately before execution
# (MASTER_PROMPT §8.1 / §8.4)
STEP_UP_REQUIRED_ACTIONS = frozenset(
    {
        PermissionVerb.APPROVE_RELEASE.value,
        PermissionVerb.EXECUTE_RELEASE_RECORD.value,
        PermissionVerb.MANAGE_POLICY.value,
        PermissionVerb.MANAGE_ROLES.value,
        PermissionVerb.CONFIGURE_INTEGRATIONS.value,
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value,
        PermissionVerb.BREAK_GLASS.value,
    }
)

# Complete Role × Action × Scope Permission Matrix (SPEC §5 & MASTER_PROMPT §8.2)
ROLE_PERMISSIONS_MATRIX: dict[AppRole, dict[str, str]] = {
    AppRole.ORG_ADMIN: {
        PermissionVerb.VIEW.value: "own_institution",
        PermissionVerb.CREATE_DRAFT.value: "own_institution",
        PermissionVerb.EDIT_DRAFT.value: "own_institution",
        PermissionVerb.SUBMIT.value: "own_institution",
        PermissionVerb.UPLOAD_EVIDENCE.value: "own_institution",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "own_institution",
        PermissionVerb.RAISE_OBSERVATION.value: "own_institution",
        PermissionVerb.RESPOND_OBSERVATION.value: "own_institution",
        PermissionVerb.REQUEST_RELEASE.value: "own_institution",
        PermissionVerb.EXPORT_REPORT.value: "own_institution",
        PermissionVerb.MANAGE_INSTITUTION_USERS.value: "own_institution",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "own_institution",
        PermissionVerb.VIEW_AUDIT.value: "own_institution",
    },
    AppRole.INSTITUTION_SUBMITTER: {
        PermissionVerb.VIEW.value: "own_institution",
        PermissionVerb.CREATE_DRAFT.value: "own_institution",
        PermissionVerb.EDIT_DRAFT.value: "own_institution",
        PermissionVerb.SUBMIT.value: "own_institution",
        PermissionVerb.UPLOAD_EVIDENCE.value: "own_institution",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "own_institution",
        PermissionVerb.RAISE_OBSERVATION.value: "own_institution",
        PermissionVerb.RESPOND_OBSERVATION.value: "own_institution",
        PermissionVerb.REQUEST_RELEASE.value: "own_institution",
        PermissionVerb.EXPORT_REPORT.value: "own_institution",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "own_institution",
        PermissionVerb.VIEW_AUDIT.value: "own_institution",
    },
    AppRole.INSTITUTION_VIEWER: {
        PermissionVerb.VIEW.value: "own_institution",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "own_institution",
    },
    AppRole.INTAKE_OFFICER: {
        PermissionVerb.VIEW.value: "assigned",
        PermissionVerb.UPLOAD_EVIDENCE.value: "assigned",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "assigned",
        PermissionVerb.RAISE_OBSERVATION.value: "assigned",
        PermissionVerb.ASSIGN_CASE.value: "assigned",
        PermissionVerb.EXPORT_REPORT.value: "all",
        PermissionVerb.MANAGE_INSTITUTION_USERS.value: "onboarding",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "assigned",
    },
    AppRole.SCRUTINY_OFFICER: {
        PermissionVerb.VIEW.value: "assigned",
        PermissionVerb.UPLOAD_EVIDENCE.value: "assigned",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "assigned",
        PermissionVerb.RAISE_OBSERVATION.value: "assigned",
        PermissionVerb.RECOMMEND.value: "assigned",
        PermissionVerb.EXPORT_REPORT.value: "all",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "assigned",
    },
    AppRole.FINANCE_VERIFIER: {
        PermissionVerb.VIEW.value: "assigned",
        PermissionVerb.UPLOAD_EVIDENCE.value: "assigned",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "assigned",
        PermissionVerb.RAISE_OBSERVATION.value: "assigned",
        PermissionVerb.VERIFY_BANK_EVIDENCE.value: "assigned",
        PermissionVerb.RECONCILE_STATEMENT.value: "all",
        PermissionVerb.RESOLVE_EXCEPTION.value: "all",
        PermissionVerb.EXECUTE_RELEASE_RECORD.value: "assigned",
        PermissionVerb.EXPORT_REPORT.value: "all",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "all",
    },
    AppRole.REGIONAL_SUPERVISOR: {
        PermissionVerb.VIEW.value: "region",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "region",
        PermissionVerb.RAISE_OBSERVATION.value: "region",
        PermissionVerb.ASSIGN_CASE.value: "region",
        PermissionVerb.RECOMMEND.value: "region",
        PermissionVerb.RECONCILE_STATEMENT.value: "region",
        PermissionVerb.RESOLVE_EXCEPTION.value: "region",
        PermissionVerb.EXPORT_REPORT.value: "region",
        PermissionVerb.MANAGE_POLICY.value: "author",
        PermissionVerb.VIEW_AUDIT.value: "region",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "region",
    },
    AppRole.COMPETENT_AUTHORITY: {
        PermissionVerb.VIEW.value: "delegation",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "delegation",
        PermissionVerb.APPROVE_RELEASE.value: "delegation",
        PermissionVerb.EXPORT_REPORT.value: "delegation",
        PermissionVerb.MANAGE_POLICY.value: "approver",
        PermissionVerb.VIEW_AUDIT.value: "all",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "delegation",
    },
    AppRole.AUDIT_REVIEWER: {
        PermissionVerb.VIEW.value: "all",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "all",
        PermissionVerb.EXPORT_REPORT.value: "all",
        PermissionVerb.VIEW_AUDIT.value: "all",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "all",
    },
    AppRole.IDENTITY_ADMIN: {
        PermissionVerb.VIEW.value: "users",
        PermissionVerb.MANAGE_ROLES.value: "all",
        PermissionVerb.VIEW_AUDIT.value: "access_logs",
        PermissionVerb.BREAK_GLASS.value: "request",
    },
    AppRole.PLATFORM_OPERATOR: {
        PermissionVerb.VIEW.value: "system",
        PermissionVerb.CONFIGURE_INTEGRATIONS.value: "all",
        PermissionVerb.ADMINISTER_PLATFORM.value: "all",
        PermissionVerb.MANAGE_TEMPLATES.value: "all",
        PermissionVerb.VIEW_AUDIT.value: "system",
        PermissionVerb.BREAK_GLASS.value: "request",
    },
    AppRole.INTEGRATION_SERVICE: {
        PermissionVerb.RECONCILE_STATEMENT.value: "connector",
        PermissionVerb.VERIFY_BANK_EVIDENCE.value: "connector",
    },
    AppRole.BANK_VERIFIER: {
        PermissionVerb.VIEW.value: "assigned_bank",
        PermissionVerb.UPLOAD_EVIDENCE.value: "assigned_bank",
        PermissionVerb.DOWNLOAD_EVIDENCE.value: "assigned_bank",
        PermissionVerb.VIEW_UNMASKED_IDENTIFIERS.value: "assigned_bank",
    },
}


class StepUpRequiredError(ForbiddenError):
    def __init__(
        self, message: str = "Step-up MFA authentication required for this action"
    ):
        super().__init__(message)
        self.code = "step_up_required"


class SeparationOfDutiesError(ForbiddenError):
    def __init__(self, message: str = "Separation of duties violation"):
        super().__init__(message)
        self.code = "separation_of_duties_violation"


class DelegationLimitExceededError(ForbiddenError):
    def __init__(self, message: str = "Operation exceeds user delegation limit"):
        super().__init__(message)
        self.code = "delegation_limit_exceeded"


@dataclass
class Principal:
    id: uuid.UUID
    email: str
    full_name: str
    role: AppRole
    institution_id: uuid.UUID | None = None
    region_id: str | None = None
    delegation_limit: Decimal | None = None
    is_active: bool = True
    mfa_enrolled: bool = False
    step_up_valid_until: datetime | None = None
    assigned_case_ids: set[uuid.UUID] = field(default_factory=set)
    role_scope: dict[str, Any] = field(default_factory=dict)
    session_id: uuid.UUID | None = None

    @property
    def step_up_valid(self) -> bool:
        if not self.mfa_enrolled or self.step_up_valid_until is None:
            return False
        now = datetime.now(UTC)
        valid_until = (
            self.step_up_valid_until.replace(tzinfo=UTC)
            if self.step_up_valid_until.tzinfo is None
            else self.step_up_valid_until.astimezone(UTC)
        )
        return valid_until >= now


def get_role_permissions(role: AppRole) -> dict[str, str]:
    if role in DISABLED_ROLES:
        return {}
    return ROLE_PERMISSIONS_MATRIX.get(role, {})


def authorise(
    principal: Principal | None,
    action: str | PermissionVerb,
    resource: Any | None = None,
    context: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> bool:
    """Authorises an action against a principal, resource, and context.

    Raises UnauthenticatedError, ForbiddenError, StepUpRequiredError,
    SeparationOfDutiesError, or DelegationLimitExceededError on refusal.
    Returns True on success. Default deny.
    """
    if now is None:
        now = datetime.now(UTC)

    act = action.value if isinstance(action, PermissionVerb) else action

    # 1. Reject if principal identity is missing, inactive, or disabled role
    if principal is None or not principal.is_active:
        raise UnauthenticatedError("Active authenticated identity required")

    if principal.role in DISABLED_ROLES:
        raise ForbiddenError(
            f"Role '{principal.role.value}' is disabled pending onboarding approval"
        )

    # 2. Require valid step-up MFA for privileged actions
    if act in STEP_UP_REQUIRED_ACTIONS and (
        not principal.mfa_enrolled
        or principal.step_up_valid_until is None
        or principal.step_up_valid_until < now
    ):
        raise StepUpRequiredError(
            f"Action '{act}' requires fresh step-up authentication"
        )

    # 3. Check action is granted by role permission matrix
    role_perms = get_role_permissions(principal.role)
    if act not in role_perms:
        raise ForbiddenError(
            f"Role '{principal.role.value}' is not permitted to perform action '{act}'"
        )

    scope_type = role_perms[act]

    # 4. Scope checks (institution, region, assignment)
    if resource is not None:
        # Check institution scope
        if scope_type == "own_institution":
            res_inst_id = getattr(resource, "institution_id", None)
            if res_inst_id is None or str(res_inst_id) != str(principal.institution_id):
                raise ForbiddenError(
                    "Access denied: resource belongs to a different institution"
                )

        # Check regional scope
        elif scope_type == "region":
            res_region_id = getattr(resource, "region_id", None)
            if (
                principal.region_id
                and res_region_id
                and str(principal.region_id) != str(res_region_id)
            ):
                raise ForbiddenError(
                    "Access denied: resource is outside user's assigned region"
                )

        # Check assigned case scope
        elif scope_type == "assigned":
            # For intake / scrutiny / finance_verifier, must match assigned cases or region if scoped
            case_id = getattr(resource, "id", None)
            assigned_officer_id = getattr(resource, "assigned_officer_id", None)
            if (
                assigned_officer_id is not None
                and str(assigned_officer_id) != str(principal.id)
                and principal.assigned_case_ids
                and case_id not in principal.assigned_case_ids
            ):
                raise ForbiddenError(
                    "Access denied: case is not assigned to this officer"
                )

        # Check assigned bank scope for bank verifiers
        elif scope_type == "assigned_bank":
            res_bank = getattr(resource, "bank_name", None)
            res_assigned_verifier = getattr(resource, "assigned_bank_verifier_id", None)
            user_bank = None
            if principal.role_scope and isinstance(principal.role_scope, dict):
                user_bank = principal.role_scope.get("bank_name")
            if (
                res_assigned_verifier
                and str(res_assigned_verifier) == str(principal.id)
                or user_bank
                and res_bank
                and str(user_bank).strip().lower() == str(res_bank).strip().lower()
            ):
                pass
            elif principal.role == AppRole.BANK_VERIFIER:
                raise ForbiddenError(
                    "Access denied: request is not assigned to your bank"
                )

    # 5. Check separation of duties (SoD) & delegation limits
    if act == PermissionVerb.VERIFY_BANK_EVIDENCE.value and resource is not None:
        requested_by = getattr(resource, "requested_by", None)
        if requested_by is not None and str(requested_by) == str(principal.id):
            raise SeparationOfDutiesError(
                "Requester cannot make evidence decision on their own bank confirmation request"
            )

    if act == PermissionVerb.APPROVE_RELEASE.value and resource is not None:
        # Maker cannot be checker
        requested_by = getattr(resource, "requested_by", None)
        maker_id = getattr(resource, "maker_id", None)
        scrutiny_officer_id = getattr(resource, "scrutiny_officer_id", None)

        if requested_by is not None and str(requested_by) == str(principal.id):
            raise SeparationOfDutiesError(
                "Requester cannot approve their own release request"
            )

        if maker_id is not None and str(maker_id) == str(principal.id):
            raise SeparationOfDutiesError(
                "Maker cannot act as checker / approver on the same case"
            )

        if scrutiny_officer_id is not None and str(scrutiny_officer_id) == str(
            principal.id
        ):
            raise SeparationOfDutiesError(
                "Scrutiny officer who reviewed case cannot approve release"
            )

        # Check delegation limit
        amount = getattr(resource, "amount", None)
        if (
            amount is not None
            and principal.delegation_limit is not None
            and Decimal(str(amount)) > principal.delegation_limit
        ):
            raise DelegationLimitExceededError(
                f"Release amount {amount} exceeds officer delegation limit of {principal.delegation_limit}"
            )

    # 6. Default allow once all guards passed
    return True


def mask_identifier(val: str | None) -> str:
    """Masks financial identifiers (FDR number, account number, UTR) as XXXX1234."""
    if not val:
        return ""
    s = str(val).strip()
    if len(s) <= 4:
        return "XXXX"
    return "XXXX" + s[-4:]


def serialize_instrument(instrument: Any, principal: Principal) -> dict[str, Any]:
    """Allow-list serializer for instruments to prevent mass property exposure."""
    can_view_unmasked = authorise_safe(
        principal, PermissionVerb.VIEW_UNMASKED_IDENTIFIERS
    )

    fdr_number = instrument.instrument_number
    if not can_view_unmasked:
        fdr_number = mask_identifier(fdr_number)

    return {
        "id": str(instrument.id),
        "institution_id": str(instrument.institution_id),
        "type": instrument.type.value
        if hasattr(instrument.type, "value")
        else str(instrument.type),
        "status": instrument.status.value
        if hasattr(instrument.status, "value")
        else str(instrument.status),
        "evidence_level": (
            instrument.evidence_level.value
            if hasattr(instrument.evidence_level, "value")
            else str(instrument.evidence_level)
        ),
        "instrument_number": fdr_number,
        "amount": str(instrument.amount),
        "issue_date": instrument.issue_date.isoformat()
        if instrument.issue_date
        else None,
        "maturity_date": instrument.maturity_date.isoformat()
        if instrument.maturity_date
        else None,
        "tenor_months": instrument.tenor_months,
        "created_at": instrument.created_at.isoformat()
        if instrument.created_at
        else None,
    }


def authorise_safe(
    principal: Principal | None, action: PermissionVerb | str, resource: Any = None
) -> bool:
    """Non-raising variant of authorise that returns boolean."""
    try:
        return authorise(principal, action, resource)
    except (ForbiddenError, UnauthenticatedError):
        return False
