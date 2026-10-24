import enum


class InstrumentType(str, enum.Enum):
    ONLINE_SD = "ONLINE_SD"
    FDR = "FDR"
    RPGF_FDR = "RPGF_FDR"
    BG = "BG"
    E_BG = "E_BG"
    SURETY_BOND = "SURETY_BOND"


class InstrumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    INTAKE_REVIEW = "INTAKE_REVIEW"
    UNDER_SCRUTINY = "UNDER_SCRUTINY"
    SCRUTINY = "SCRUTINY"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"
    VERIFIED = "VERIFIED"
    ACTIVE = "ACTIVE"
    ACTIVE_TRACKING = "ACTIVE_TRACKING"
    EXPIRING = "EXPIRING"
    MATURED = "MATURED"
    RENEWAL_REQUESTED = "RENEWAL_REQUESTED"
    REPLACEMENT_REQUESTED = "REPLACEMENT_REQUESTED"
    RELEASE_REQUESTED = "RELEASE_REQUESTED"
    RELEASED = "RELEASED"
    DISCHARGED = "DISCHARGED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class ObservationStatus(str, enum.Enum):
    OPEN = "OPEN"
    AWAITING_INSTITUTION = "AWAITING_INSTITUTION"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class DocumentStatus(str, enum.Enum):
    UPLOAD_INTENT = "UPLOAD_INTENT"
    QUARANTINED = "QUARANTINED"
    SCANNING = "SCANNING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ReleaseRequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    COMPLETENESS_REVIEW = "COMPLETENESS_REVIEW"
    REQUIRED_CLEARANCES = "REQUIRED_CLEARANCES"
    SCRUTINY_RECOMMENDATION = "SCRUTINY_RECOMMENDATION"
    COMPETENT_AUTHORITY_DECISION = "COMPETENT_AUTHORITY_DECISION"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    RELEASED_DISCHARGED = "RELEASED_DISCHARGED"
    RETURNED = "RETURNED"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ClearanceStatus(str, enum.Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT SATISFIED"
    PENDING_SOURCE = "PENDING SOURCE"
    NOT_APPLICABLE = "NOT APPLICABLE"


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    RETIRED = "retired"
    BLOCKED = "BLOCKED"


class NotificationCategory(str, enum.Enum):
    CRITICAL_WORKFLOW = "critical_workflow"
    DEADLINE = "deadline"
    SECURITY_ACCOUNT = "security_account"
    OPERATIONS = "operations"
    DIGEST = "digest"


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    WEB_PUSH = "web_push"


class NotificationStatus(str, enum.Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PROVIDER_ACCEPTED = "PROVIDER_ACCEPTED"
    PROVIDER_FAILED = "PROVIDER_FAILED"
    DEVICE_RECEIVED = "DEVICE_RECEIVED"
    OPENED = "OPENED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACTIONED = "ACTIONED"
    EXPIRED = "EXPIRED"
    DEAD_LETTER = "DEAD_LETTER"


class DevicePlatform(str, enum.Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


class PushProvider(str, enum.Enum):
    FCM = "fcm"
    APNS = "apns"
    WEBPUSH = "webpush"


class EvidenceLevel(str, enum.Enum):
    L0_DECLARED = "L0_DECLARED"
    L1_EXTRACTED = "L1_EXTRACTED"
    L2_BANK_CONFIRMED = "L2_BANK_CONFIRMED"
    L3_LEDGER_RECONCILED = "L3_LEDGER_RECONCILED"


class AppRole(str, enum.Enum):
    """13-role model (MASTER_PROMPT §1.3 / §8.2), replacing the Phase 0
    8-role model. See docs/MASTER_PROMPT.md §8.2 for the verb matrix these
    roles are granted against (app/authz.py + the role_permissions table,
    migration e1a1f2b3c4d5).

    Mapping from the old 8-role model (kept here as a durable record of
    the Phase 1 migration, not for runtime use):
      institution        -> institution_submitter (write-side actions kept
                             the old actor); institution_viewer and
                             org_admin are new, finer-grained splits of the
                             same institution-side user base.
      scrutiny_officer    -> scrutiny_officer (unchanged)
      verifier            -> finance_verifier
      regional_officer    -> regional_supervisor
      competent_authority -> competent_authority (unchanged)
      bureau_admin        -> platform_operator (the "all-powerful bureau
                             admin" uses of the old role, e.g. the
                             DISCHARGED transition and the admin test
                             fixture); identity_admin is a new, narrower
                             split for user/role administration only.
      bank_user           -> bank_verifier (stays `disabled` — see below)
      auditor             -> audit_reviewer
    intake_officer and integration_service are new roles with no Phase 0
    equivalent (F-02 onboarding intake, and machine-to-machine callers).
    """

    ORG_ADMIN = "org_admin"
    INSTITUTION_SUBMITTER = "institution_submitter"
    INSTITUTION_VIEWER = "institution_viewer"
    INTAKE_OFFICER = "intake_officer"
    SCRUTINY_OFFICER = "scrutiny_officer"
    FINANCE_VERIFIER = "finance_verifier"
    REGIONAL_SUPERVISOR = "regional_supervisor"
    COMPETENT_AUTHORITY = "competent_authority"
    AUDIT_REVIEWER = "audit_reviewer"
    IDENTITY_ADMIN = "identity_admin"
    PLATFORM_OPERATOR = "platform_operator"
    INTEGRATION_SERVICE = "integration_service"
    # MASTER_PROMPT §1.3: "Participating Bank Verifier (conditional,
    # disabled until onboarding is approved)". Modelled so the schema and
    # role_permissions seed are ready, but no endpoint grants it yet
    # (bank onboarding does not exist until the Phase 3 bank-verifier
    # portal ships) — see DISABLED_ROLES below and MASTER_PROMPT §3.
    BANK_VERIFIER = "bank_verifier"


# Active role set; BANK_VERIFIER enabled in Phase 3
DISABLED_ROLES: tuple[AppRole, ...] = ()


# Roles with bureau-side (cross-institution) visibility under RLS: AICTE
# staff and system/service identities, as opposed to a single
# institution's own users or the (currently disabled) bank-side role.
BUREAU_SIDE_ROLES = (
    AppRole.INTAKE_OFFICER,
    AppRole.SCRUTINY_OFFICER,
    AppRole.FINANCE_VERIFIER,
    AppRole.REGIONAL_SUPERVISOR,
    AppRole.COMPETENT_AUTHORITY,
    AppRole.AUDIT_REVIEWER,
    AppRole.IDENTITY_ADMIN,
    AppRole.PLATFORM_OPERATOR,
    AppRole.INTEGRATION_SERVICE,
)

# Institution-side roles: scoped to their own institution_id under RLS.
INSTITUTION_SIDE_ROLES = (
    AppRole.ORG_ADMIN,
    AppRole.INSTITUTION_SUBMITTER,
    AppRole.INSTITUTION_VIEWER,
)
