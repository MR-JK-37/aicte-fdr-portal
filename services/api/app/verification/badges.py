"""Evidence-level badge metadata (L0-L3), shared contract for the web UI
(Phase 9) and API responses. Colour tokens match the design spec's single
cyan accent + colour-blind-safe status rule: status is never colour-only,
every badge also carries a short label and an icon name.
"""

from app.models.enums import EvidenceLevel

BADGES: dict[EvidenceLevel, dict] = {
    EvidenceLevel.L0_DECLARED: {
        "label": "L0 Declared",
        "icon": "file-text",
        "tone": "neutral",
    },
    EvidenceLevel.L1_EXTRACTED: {
        "label": "L1 Document-extracted",
        "icon": "file-search",
        "tone": "info",
    },
    EvidenceLevel.L2_BANK_CONFIRMED: {
        "label": "L2 Bank-confirmed",
        "icon": "badge-check",
        "tone": "success",
    },
    EvidenceLevel.L3_LEDGER_RECONCILED: {
        "label": "L3 Ledger-reconciled",
        "icon": "shield-check",
        "tone": "success",
    },
}


def badge_for(level: EvidenceLevel) -> dict:
    return BADGES[level]
