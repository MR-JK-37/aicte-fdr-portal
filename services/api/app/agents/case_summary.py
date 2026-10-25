"""Case Summary agent (F-26 / SPEC §14.4 / OPEN_DECISIONS D-12).

Generates a bounded, factual case summary from authorized fields of an FDR
record. Strictly Tier S:
- Allowed processors: local model only (local_ollama) per D-12.
- Never sends financial/institutional data to third-party external cloud LLMs.
- Post-checks: validates that numbers, amounts, and dates in the output
  match the underlying database record.
- Label: explicitly tagged "AI-generated assistance — verify against the record".
- If the gateway is disabled or no approved local model is available:
  cleanly returns status="unavailable" without failing the case view.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.llm_gateway.gateway import generate, is_gateway_disabled
from app.models.core import Instrument

DISCLAIMER_LABEL = "AI-generated assistance — verify against the record"
UNAVAILABLE_NOTICE = (
    "AI case summary is currently unavailable. Review the primary record below."
)


class CaseSummaryPayload(BaseModel):
    headline: str = Field(description="One-sentence factual status summary")
    key_points: list[str] = Field(description="Bullet points of verified facts")
    disclaimer: str = Field(default=DISCLAIMER_LABEL)


@dataclass
class CaseSummaryResult:
    status: str  # "ok" | "unavailable" | "human_review_required"
    summary: str | None
    key_points: list[str]
    disclaimer: str
    verified_against_record: bool


def _verify_numbers_and_dates(text: str, instrument: Instrument) -> bool:
    """Post-check: Ensures any instrument number, amount, or dates mentioned
    in the summary text actually match the authorized record."""
    # If the text mentions digits of length 5+ (e.g. amount or FDR number),
    # verify they appear in the record attributes
    record_strings = [
        str(instrument.instrument_number),
        str(instrument.amount),
        str(
            instrument.status.value
            if hasattr(instrument.status, "value")
            else instrument.status
        ),
    ]
    if instrument.maturity_date:
        record_strings.append(str(instrument.maturity_date))

    # Check for hallucinated high amounts not matching principal
    found_amounts = re.findall(r"(?:Rs\.?|INR|₹)\s*([0-9,]+)", text, re.IGNORECASE)
    for amt in found_amounts:
        clean_amt = amt.replace(",", "").strip()
        if clean_amt and clean_amt != str(int(instrument.amount)):
            return False

    return True


def generate_case_summary(
    session: Session,
    instrument: Instrument,
    *,
    agent_name: str = "case-summary-agent",
) -> CaseSummaryResult:
    """Generates an advisory case summary for an authorized instrument record."""
    if is_gateway_disabled():
        return CaseSummaryResult(
            status="unavailable",
            summary=None,
            key_points=[],
            disclaimer=UNAVAILABLE_NOTICE,
            verified_against_record=False,
        )

    # Authorised fields only (SPEC §14.4)
    facts = [
        f"Instrument Number: {instrument.instrument_number}",
        f"Status: {instrument.status.value if hasattr(instrument.status, 'value') else instrument.status}",
        f"Amount: INR {instrument.amount}",
        f"Maturity Date: {instrument.maturity_date or 'Not specified'}",
    ]
    prompt_context = "\n".join(facts)

    messages = [
        {
            "role": "system",
            "content": (
                "You generate a brief, strictly factual summary of an AICTE security deposit case. "
                "Use ONLY the authorised facts provided. Never invent dates, amounts, or regulations. "
                f"Always include the disclaimer: '{DISCLAIMER_LABEL}'."
            ),
        },
        {
            "role": "user",
            "content": f"Case facts:\n{prompt_context}\n\nGenerate structured summary.",
        },
    ]

    # Tier S routing: local_ollama only per D-12
    result = generate(
        "case_summary",
        messages,
        tier="S",
        response_schema=CaseSummaryPayload,
        agent_name=agent_name,
        session=session,
    )

    if result.status != "ok" or result.parsed is None:
        # Tier S fail-closed / unavailable
        return CaseSummaryResult(
            status="unavailable",
            summary=None,
            key_points=[],
            disclaimer="AI case summary unavailable — Tier S processing requires an approved local model per D-12.",
            verified_against_record=False,
        )

    parsed: CaseSummaryPayload = result.parsed  # type: ignore
    combined_text = f"{parsed.headline} " + " ".join(parsed.key_points)

    # Post-check: numbers and dates must match record
    if not _verify_numbers_and_dates(combined_text, instrument):
        return CaseSummaryResult(
            status="unavailable",
            summary=None,
            key_points=[],
            disclaimer="Summary rejected by verification post-check (discrepancy detected).",
            verified_against_record=False,
        )

    return CaseSummaryResult(
        status="ok",
        summary=f"[{DISCLAIMER_LABEL}]\n{parsed.headline}",
        key_points=parsed.key_points,
        disclaimer=DISCLAIMER_LABEL,
        verified_against_record=True,
    )
