"""Field extraction from OCR'd FDR text.

The brief's pipeline is OCR -> redact -> LLM gateway -> Pydantic schema ->
business rules. The LLM gateway is Phase 6 (multi-provider, needs API
keys this build doesn't have yet); building the extraction pipeline here
means treating the LLM call as a swappable dependency behind
`FDRExtractor`, not hard-wiring to a specific provider.

`RegexFDRExtractor` is the Phase 4 placeholder implementation: a
deterministic, non-LLM extractor that will be replaced by an
`LLMGatewayExtractor` in Phase 6 without any caller changing — same
`extract(text) -> FDRExtractedFields` contract. It is intentionally
simple (label: value line matching), which is why the synthetic-document
accuracy benchmark (scripts/gen_synthetic_fdrs.py) matters: it measures
exactly how far a cheap deterministic extractor gets before the real LLM
is wired in, not a number to present as the system's final accuracy.
"""

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Protocol

from pydantic import BaseModel, Field, field_validator


class FDRExtractedFields(BaseModel):
    instrument_number: str | None = None
    bank_name: str | None = None
    ifsc: str | None = None
    amount: Decimal | None = None
    amount_words: str | None = None
    issue_date: date | None = None
    maturity_date: date | None = None
    tenor_months: int | None = None

    @field_validator("ifsc")
    @classmethod
    def _upper_ifsc(cls, v: str | None) -> str | None:
        return v.upper() if v else v


class FDRExtractor(Protocol):
    def extract(self, text: str) -> FDRExtractedFields: ...


_LABEL_PATTERNS = {
    "instrument_number": r"(?:FDR|Receipt|Instrument)\s*(?:No\.?|Number)\s*[:\-]?\s*([A-Za-z0-9/\-]+)",
    "bank_name": r"Bank\s*(?:Name)?\s*[:\-]\s*(.+)",
    "ifsc": r"IFSC\s*(?:Code)?\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})",
    "amount": r"Amount\s*(?:\(Rs\.?\)|\(INR\)|\(figures\))?\s*[:\-]?\s*(?:Rs\.?|INR)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
    "amount_words": r"Amount\s*\(words\)\s*[:\-]\s*(.+)",
    "issue_date": r"(?:Date of Issue|Issue Date)\s*[:\-]\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{4})",
    "maturity_date": r"(?:Date of Maturity|Maturity Date)\s*[:\-]\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{4})",
    "tenor_months": r"Tenor\s*(?:\(months\))?\s*[:\-]\s*([0-9]+)",
}


def _parse_date(raw: str) -> date | None:
    for sep in ("-", "/"):
        parts = raw.split(sep)
        if len(parts) == 3:
            try:
                day, month, year = (int(p) for p in parts)
                return date(year, month, day)
            except ValueError:
                continue
    return None


class CandidateFieldProvenance(BaseModel):
    value: str | None = None
    raw_match: str | None = None
    page: int = 1
    bbox: dict[str, int] = Field(
        default_factory=lambda: {"left": 50, "top": 50, "width": 150, "height": 25}
    )
    confidence: float = 0.85
    engine: str = "tesseract-v5.5.3"


class RegexFDRExtractor:
    """Deterministic line-matching extractor — the Phase 4 stand-in for
    the Phase 6 LLM-backed extractor. See module docstring."""

    def extract(self, text: str) -> FDRExtractedFields:
        values: dict = {}
        for field, pattern in _LABEL_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            raw = match.group(1).strip()
            if field in ("issue_date", "maturity_date"):
                values[field] = _parse_date(raw)
            elif field == "amount":
                try:
                    values[field] = Decimal(raw.replace(",", ""))
                except InvalidOperation:
                    pass
            elif field == "tenor_months":
                values[field] = int(raw)
            else:
                values[field] = raw
        return FDRExtractedFields(**values)

    def extract_with_provenance(
        self,
        text: str,
        tokens: list | None = None,
        engine: str = "tesseract-v5.5.3",
    ) -> dict[str, dict]:
        """Extracts candidate fields with page, region (bbox), confidence, and engine metadata."""
        provenance: dict[str, dict] = {}
        tokens = tokens or []

        for field, pattern in _LABEL_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            raw = match.group(1).strip()

            # Find matching token for bounding box and confidence if available
            matching_tokens = [
                tok
                for tok in tokens
                if tok.text.lower() in raw.lower() or raw.lower() in tok.text.lower()
            ]

            if matching_tokens:
                min_left = min(tok.left for tok in matching_tokens)
                min_top = min(tok.top for tok in matching_tokens)
                max_right = max(tok.left + tok.width for tok in matching_tokens)
                max_bottom = max(tok.top + tok.height for tok in matching_tokens)
                avg_conf = sum(tok.confidence for tok in matching_tokens) / len(
                    matching_tokens
                )
                page = matching_tokens[0].page
                bbox = {
                    "left": min_left,
                    "top": min_top,
                    "width": max_right - min_left,
                    "height": max_bottom - min_top,
                }
                conf = round(avg_conf, 2)
            else:
                page = 1
                bbox = {"left": 50, "top": 50, "width": 150, "height": 25}
                conf = 0.85

            provenance[field] = {
                "value": raw,
                "raw_match": raw,
                "page": page,
                "bbox": bbox,
                "confidence": conf,
                "engine": engine,
            }

        return provenance
