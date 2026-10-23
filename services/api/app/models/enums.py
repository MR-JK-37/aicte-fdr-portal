import enum


class InstrumentType(str, enum.Enum):
    ONLINE_SD = "ONLINE_SD"
    FDR = "FDR"
    RPGF_FDR = "RPGF_FDR"
    BG = "BG"
    E_BG = "E_BG"
    SURETY_BOND = "SURETY_BOND"


class InstrumentStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_SCRUTINY = "UNDER_SCRUTINY"
    VERIFIED = "VERIFIED"
    ACTIVE = "ACTIVE"
    EXPIRING = "EXPIRING"
    MATURED = "MATURED"
    RENEWAL_REQUESTED = "RENEWAL_REQUESTED"
    REPLACEMENT_REQUESTED = "REPLACEMENT_REQUESTED"
    RELEASE_REQUESTED = "RELEASE_REQUESTED"
    RELEASED = "RELEASED"
    DISCHARGED = "DISCHARGED"


class EvidenceLevel(str, enum.Enum):
    L0_DECLARED = "L0_DECLARED"
    L1_EXTRACTED = "L1_EXTRACTED"
    L2_BANK_CONFIRMED = "L2_BANK_CONFIRMED"
    L3_LEDGER_RECONCILED = "L3_LEDGER_RECONCILED"


class AppRole(str, enum.Enum):
    INSTITUTION = "institution"
    SCRUTINY_OFFICER = "scrutiny_officer"
    VERIFIER = "verifier"
    REGIONAL_OFFICER = "regional_officer"
    COMPETENT_AUTHORITY = "competent_authority"
    BUREAU_ADMIN = "bureau_admin"
    BANK_USER = "bank_user"
    AUDITOR = "auditor"


# Roles with bureau-side (cross-institution) visibility under RLS.
BUREAU_SIDE_ROLES = (
    AppRole.SCRUTINY_OFFICER,
    AppRole.VERIFIER,
    AppRole.REGIONAL_OFFICER,
    AppRole.COMPETENT_AUTHORITY,
    AppRole.BUREAU_ADMIN,
    AppRole.AUDITOR,
)
