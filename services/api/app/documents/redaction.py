"""Deterministic-token PII redaction applied to OCR text before it is sent
to any LLM provider. This is the lightweight regex-based version; the full
Presidio-based redaction layer with custom recognisers (IFSC/FDR
number/PAN/Aadhaar/mobile/GSTIN/account numbers/institution names) is
specified for the Phase 6 llm_gateway and will replace this module's body
without changing its interface (redact() / rehydrate()) once that gateway
exists — Phase 4 needs *a* redaction step to exist, not the final one.
"""

import re

PATTERNS: dict[str, re.Pattern] = {
    "PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "AADHAAR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "MOBILE": re.compile(r"\b[6-9]\d{9}\b"),
    "GSTIN": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]\b"),
    "ACCOUNT_NUMBER": re.compile(r"\b\d{9,18}\b"),
}


def redact(text: str) -> tuple[str, dict[str, str]]:
    """Replaces each PII match with a deterministic token
    (<<TYPE_n>>) and returns (redacted_text, token_map) so the caller can
    rehydrate the LLM's structured output locally afterward, without the
    LLM ever seeing the real value."""
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


def rehydrate(text: str, token_map: dict[str, str]) -> str:
    for token, original in token_map.items():
        text = text.replace(token, original)
    return text
