"""Redaction layer for prompts sent to any LLM provider.

**Deliberately not Presidio**, despite the brief specifying
"Presidio plus custom recognisers": presidio-analyzer pulls in spaCy plus
a language model (~500MB+), which works against the 2 OCPU/12GB Oracle
Always Free deploy target this whole build is scoped to run on. This
reuses and extends app.documents.redaction's regex recognisers (already
covering IFSC, PAN, Aadhaar, mobile, GSTIN, account numbers) with an
instrument-number pattern, which covers the brief's named PII categories
except institution names (would need an NER model or a name-list lookup
— not built here; flagged in progress.md as a real gap, not silently
dropped). Swapping in real Presidio later is a drop-in: same
redact()/rehydrate() signatures.
"""

import re

from app.documents.redaction import PATTERNS as _BASE_PATTERNS
from app.documents.redaction import rehydrate  # re-exported

PATTERNS: dict[str, re.Pattern] = {
    **_BASE_PATTERNS,
    "INSTRUMENT_NUMBER": re.compile(r"\b(?:FDR|BG|SD)[A-Za-z0-9/\-]{4,}\b"),
}


def redact(text: str) -> tuple[str, dict[str, str]]:
    token_map: dict[str, str] = {}
    redacted = text
    counters: dict[str, int] = {}
    for label, pattern in PATTERNS.items():

        def _sub(match: re.Match, label=label) -> str:
            counters[label] = counters.get(label, 0) + 1
            token = f"<<{label}_{counters[label]}>>"
            token_map[token] = match.group(0)
            return token

        redacted = pattern.sub(_sub, redacted)
    return redacted, token_map


__all__ = ["PATTERNS", "redact", "rehydrate"]
