"""Server-built navigation manifest (R2 continuation) — GET /v1/me/navigation.

AUTH_ROLES_MATRIX.md §1 is the source of truth for which role sees which nav
items; this module is that table turned into data the clients render from.
Hard rule this exists to enforce: "role names are never hard-coded in UI logic
except for copy" (AUTH_ROLES_MATRIX.md §2.3) — the client asks the server what
it can see, instead of a client-side role→screens map.

Routes/icon keys here are logical identifiers, not final URLs/assets — R5/R6
build the actual screens and icon set this points at. A route with no screen
built yet is still correct to list: the manifest describes what the role is
*entitled* to see, and the client's job is to render an honest "coming soon"
or 404, not to silently omit it (that would make the manifest an inaccurate
description of the permission model, which is the thing it exists to be
accurate about).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.authz import PermissionVerb
from app.models.enums import AppRole


@dataclass(frozen=True)
class NavItem:
    key: str
    label_key: str  # i18n key, not display text — clients localise
    icon_key: str
    route: str
    required_permission: str | None = None  # None = visible to anyone with this landing


@dataclass(frozen=True)
class RoleNavigation:
    landing_route: str
    web_sidebar: tuple[NavItem, ...]
    mobile_tabs: tuple[NavItem, ...]


_HOME = NavItem("home", "nav.home", "home", "/home")
_INBOX = NavItem("inbox", "nav.inbox", "inbox", "/inbox")
_PROFILE = NavItem("profile", "nav.profile", "profile", "/profile")
_HELP = NavItem("help", "nav.help", "help", "/help")
_REPORTS = NavItem(
    "reports", "nav.reports", "reports", "/reports", PermissionVerb.EXPORT_REPORT.value
)
_SEARCH = NavItem(
    "search", "nav.search", "search", "/search", PermissionVerb.VIEW.value
)

_NAVIGATION: dict[AppRole, RoleNavigation] = {
    AppRole.ORG_ADMIN: RoleNavigation(
        "/home",
        (
            _HOME,
            NavItem(
                "deposits",
                "nav.deposits",
                "instrument",
                "/deposits",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "documents",
                "nav.documents",
                "document",
                "/documents",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "observations",
                "nav.observations",
                "observation",
                "/observations",
                PermissionVerb.RESPOND_OBSERVATION.value,
            ),
            NavItem(
                "renewals",
                "nav.renewals",
                "renewal",
                "/renewals",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "releases",
                "nav.releases",
                "release",
                "/releases",
                PermissionVerb.REQUEST_RELEASE.value,
            ),
            NavItem(
                "users",
                "nav.users",
                "users",
                "/institution/users",
                PermissionVerb.MANAGE_INSTITUTION_USERS.value,
            ),
            _REPORTS,
            _HELP,
        ),
        (
            _HOME,
            NavItem("deposits", "nav.deposits", "instrument", "/deposits"),
            _INBOX,
            _PROFILE,
        ),
    ),
    AppRole.INSTITUTION_SUBMITTER: RoleNavigation(
        "/home",
        (
            _HOME,
            NavItem(
                "deposits",
                "nav.deposits",
                "instrument",
                "/deposits",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "documents",
                "nav.documents",
                "document",
                "/documents",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "observations",
                "nav.observations",
                "observation",
                "/observations",
                PermissionVerb.RESPOND_OBSERVATION.value,
            ),
            NavItem(
                "renewals",
                "nav.renewals",
                "renewal",
                "/renewals",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "releases",
                "nav.releases",
                "release",
                "/releases",
                PermissionVerb.REQUEST_RELEASE.value,
            ),
            _HELP,
        ),
        (
            _HOME,
            NavItem("deposits", "nav.deposits", "instrument", "/deposits"),
            _INBOX,
            _PROFILE,
        ),
    ),
    AppRole.INSTITUTION_VIEWER: RoleNavigation(
        "/home",
        (
            _HOME,
            NavItem(
                "deposits",
                "nav.deposits",
                "instrument",
                "/deposits",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "maturity_calendar",
                "nav.maturity_calendar",
                "calendar",
                "/maturity-calendar",
                PermissionVerb.VIEW.value,
            ),
            _HELP,
        ),
        (
            _HOME,
            NavItem("deposits", "nav.deposits", "instrument", "/deposits"),
            _INBOX,
            _PROFILE,
        ),
    ),
    AppRole.INTAKE_OFFICER: RoleNavigation(
        "/intake-queue",
        (
            _HOME,
            NavItem(
                "intake_queue",
                "nav.intake_queue",
                "queue",
                "/intake-queue",
                PermissionVerb.ASSIGN_CASE.value,
            ),
            NavItem(
                "onboarding_requests",
                "nav.onboarding_requests",
                "onboarding",
                "/onboarding-requests",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "institutions",
                "nav.institutions",
                "institution",
                "/institutions",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "instruments",
                "nav.instruments",
                "instrument",
                "/instruments",
                PermissionVerb.VIEW.value,
            ),
            _SEARCH,
            _REPORTS,
        ),
        (
            _HOME,
            NavItem("queue", "nav.queue", "queue", "/intake-queue"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.SCRUTINY_OFFICER: RoleNavigation(
        "/my-queue",
        (
            _HOME,
            NavItem(
                "my_queue",
                "nav.my_queue",
                "queue",
                "/my-queue",
                PermissionVerb.VIEW.value,
            ),
            NavItem("cases", "nav.cases", "case", "/cases", PermissionVerb.VIEW.value),
            NavItem(
                "document_review",
                "nav.document_review",
                "document",
                "/document-review",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "observations",
                "nav.observations",
                "observation",
                "/observations",
                PermissionVerb.RAISE_OBSERVATION.value,
            ),
            _SEARCH,
            _REPORTS,
        ),
        (
            _HOME,
            NavItem("cases", "nav.cases", "case", "/cases"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.FINANCE_VERIFIER: RoleNavigation(
        "/verification-requests",
        (
            _HOME,
            NavItem(
                "verification_requests",
                "nav.verification_requests",
                "verify",
                "/verification-requests",
                PermissionVerb.VERIFY_BANK_EVIDENCE.value,
            ),
            NavItem(
                "statements",
                "nav.statements",
                "statement",
                "/statements",
                PermissionVerb.RECONCILE_STATEMENT.value,
            ),
            NavItem(
                "exceptions",
                "nav.exceptions",
                "exception",
                "/exceptions",
                PermissionVerb.RESOLVE_EXCEPTION.value,
            ),
            NavItem(
                "release_execution",
                "nav.release_execution",
                "release",
                "/release-execution",
                PermissionVerb.EXECUTE_RELEASE_RECORD.value,
            ),
            _REPORTS,
        ),
        (
            _HOME,
            NavItem("verify", "nav.verify", "verify", "/verification-requests"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.REGIONAL_SUPERVISOR: RoleNavigation(
        "/workload-board",
        (
            _HOME,
            NavItem(
                "workload_board",
                "nav.workload_board",
                "board",
                "/workload-board",
                PermissionVerb.ASSIGN_CASE.value,
            ),
            NavItem("cases", "nav.cases", "case", "/cases", PermissionVerb.VIEW.value),
            NavItem(
                "releases_recommend",
                "nav.releases_recommend",
                "release",
                "/releases/recommend",
                PermissionVerb.RECOMMEND.value,
            ),
            _REPORTS,
            NavItem(
                "reminder_schedule",
                "nav.reminder_schedule",
                "schedule",
                "/reminder-schedule",
                PermissionVerb.VIEW.value,
            ),
        ),
        (
            _HOME,
            NavItem("cases", "nav.cases", "case", "/cases"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.COMPETENT_AUTHORITY: RoleNavigation(
        "/decisions",
        (
            _HOME,
            NavItem(
                "decisions",
                "nav.decisions",
                "decision",
                "/decisions",
                PermissionVerb.APPROVE_RELEASE.value,
            ),
            NavItem(
                "release_requests",
                "nav.release_requests",
                "release",
                "/release-requests",
                PermissionVerb.VIEW.value,
            ),
            _REPORTS,
        ),
        (
            _HOME,
            NavItem("decisions", "nav.decisions", "decision", "/decisions"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.AUDIT_REVIEWER: RoleNavigation(
        "/audit-timeline",
        (
            _HOME,
            NavItem(
                "audit_timeline",
                "nav.audit_timeline",
                "audit",
                "/audit-timeline",
                PermissionVerb.VIEW_AUDIT.value,
            ),
            NavItem(
                "access_logs",
                "nav.access_logs",
                "logs",
                "/access-logs",
                PermissionVerb.VIEW_AUDIT.value,
            ),
            NavItem(
                "chain_verification",
                "nav.chain_verification",
                "chain",
                "/chain-verification",
                PermissionVerb.VIEW_AUDIT.value,
            ),
            NavItem(
                "policy_versions",
                "nav.policy_versions",
                "policy",
                "/policy-versions",
                PermissionVerb.VIEW.value,
            ),
            NavItem(
                "control_evidence_export",
                "nav.control_evidence_export",
                "export",
                "/control-evidence-export",
                PermissionVerb.EXPORT_REPORT.value,
            ),
        ),
        (
            _HOME,
            NavItem("audit", "nav.audit", "audit", "/audit-timeline"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.IDENTITY_ADMIN: RoleNavigation(
        "/access-admin",
        (
            _HOME,
            NavItem(
                "users",
                "nav.users",
                "users",
                "/users",
                PermissionVerb.MANAGE_ROLES.value,
            ),
            NavItem(
                "role_assignments",
                "nav.role_assignments",
                "roles",
                "/role-assignments",
                PermissionVerb.MANAGE_ROLES.value,
            ),
            NavItem(
                "recertification",
                "nav.recertification",
                "recert",
                "/recertification",
                PermissionVerb.MANAGE_ROLES.value,
            ),
            NavItem(
                "sessions",
                "nav.sessions",
                "sessions",
                "/admin/sessions",
                PermissionVerb.MANAGE_ROLES.value,
            ),
            NavItem(
                "invitations",
                "nav.invitations",
                "invite",
                "/invitations",
                PermissionVerb.MANAGE_INSTITUTION_USERS.value,
            ),
        ),
        (
            _HOME,
            NavItem("access", "nav.access", "access", "/access-admin"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.PLATFORM_OPERATOR: RoleNavigation(
        "/system-health",
        (
            _HOME,
            NavItem(
                "system_health",
                "nav.system_health",
                "health",
                "/system-health",
                PermissionVerb.ADMINISTER_PLATFORM.value,
            ),
            NavItem(
                "connectors",
                "nav.connectors",
                "connector",
                "/connectors",
                PermissionVerb.CONFIGURE_INTEGRATIONS.value,
            ),
            NavItem(
                "scheduler",
                "nav.scheduler",
                "scheduler",
                "/scheduler",
                PermissionVerb.ADMINISTER_PLATFORM.value,
            ),
            NavItem(
                "dlq",
                "nav.dlq",
                "dlq",
                "/dead-letter-queue",
                PermissionVerb.ADMINISTER_PLATFORM.value,
            ),
            NavItem(
                "feature_registry",
                "nav.feature_registry",
                "feature",
                "/feature-registry",
                PermissionVerb.ADMINISTER_PLATFORM.value,
            ),
            NavItem(
                "policy_registry_read",
                "nav.policy_registry_read",
                "policy",
                "/policy-registry",
                PermissionVerb.VIEW.value,
            ),
        ),
        (
            _HOME,
            NavItem("system", "nav.system", "system", "/system-health"),
            _INBOX,
            NavItem("more", "nav.more", "more", "/more"),
        ),
    ),
    AppRole.BANK_VERIFIER: RoleNavigation(
        "/assigned-requests",
        (
            NavItem(
                "assigned_requests",
                "nav.assigned_requests",
                "verify",
                "/assigned-requests",
                PermissionVerb.VERIFY_BANK_EVIDENCE.value,
            ),
            NavItem(
                "responses",
                "nav.responses",
                "response",
                "/responses",
                PermissionVerb.UPLOAD_EVIDENCE.value,
            ),
            _HELP,
        ),
        (
            NavItem("requests", "nav.requests", "verify", "/assigned-requests"),
            _INBOX,
            _PROFILE,
        ),
    ),
}

# INTEGRATION_SERVICE is a machine identity (AUTH_ROLES_MATRIX.md §1: "— / —") — no UI,
# intentionally absent from _NAVIGATION; get_navigation_for_role returns an empty
# manifest rather than a KeyError for it, same as for any role with no table.


def get_navigation_for_role(role: AppRole) -> RoleNavigation:
    return _NAVIGATION.get(
        role, RoleNavigation("/home", (_HOME, _HELP), (_HOME, _PROFILE))
    )
