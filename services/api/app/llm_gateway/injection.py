"""Prompt-injection defence for text pulled from untrusted documents
(OCR'd FDR scans an institution uploaded — exactly the "prompt injection
via documents" risk the brief's risk register names).

Two layers, per the brief ("rasterise PDFs, no-tool extraction agents,
delimiters, injection classifier"):
1. Documents are already rasterised + OCR'd (app/documents/ocr.py) rather
   than having their embedded text/JS extracted directly — that alone
   defeats most injection vectors that rely on non-visible document
   structure (hidden layers, embedded scripts, metadata fields).
2. `classify_injection_risk` calls Groq's actually-available
   meta-llama/llama-prompt-guard-2-86m model — a real, verified,
   purpose-built classifier for this, not a prompt hack — with a regex
   heuristic fallback when no provider is configured, so the check still
   does *something* offline/in tests.
"""

import re

from app.llm_gateway.client import ProviderCallError, call_chat_completion
from app.llm_gateway.registry import load_registry

# Fallback heuristic only — used when the classifier model is
# unavailable. The real signal is the model call below.
_SUSPICIOUS_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"disregard (the|your) (system|previous) prompt", re.IGNORECASE),
    re.compile(r"reveal (your|the) (system )?prompt", re.IGNORECASE),
]


def heuristic_injection_flags(text: str) -> list[str]:
    return [p.pattern for p in _SUSPICIOUS_PATTERNS if p.search(text)]


def classify_injection_risk(text: str) -> dict:
    """Returns {"method": ..., "flagged": bool, "detail": ...}. Falls back
    to the regex heuristic if the classifier provider/model isn't
    available (no key, network error) — never raises, since this is a
    defensive check that must not itself become an availability risk for
    the extraction pipeline it's protecting."""
    registry = load_registry()
    groq = registry.get("groq")
    if groq and groq.has_key and groq.model("meta-llama/llama-prompt-guard-2-86m"):
        try:
            result = call_chat_completion(
                groq,
                "meta-llama/llama-prompt-guard-2-86m",
                [{"role": "user", "content": text[:2000]}],
            )
            label = result.content.strip().upper()
            return {
                "method": "llama-prompt-guard-2-86m",
                "flagged": "INJECTION" in label or "JAILBREAK" in label,
                "detail": label,
            }
        except ProviderCallError:
            pass  # fall through to heuristic

    flags = heuristic_injection_flags(text)
    return {"method": "regex_heuristic", "flagged": bool(flags), "detail": flags}
