"""Document Intelligence agent: the real LLM-backed implementation of
the `FDRExtractor` protocol Phase 4 built for exactly this swap
(app/documents/extraction.py's `RegexFDRExtractor` was always labelled a
placeholder for this). Extracts structured fields from OCR'd, already-
redacted text via the LLM gateway — never raw document bytes, and never
with tool/function-calling access (the brief: "no-tool extraction
agents" as a prompt-injection defence), per the extraction task class's
Tier P routing.

Per the brief's hard rule: this agent extracts into a structured record
that an officer must confirm (see app.documents.pipeline.confirm_extraction)
— it never raises evidence_level itself.
"""

from sqlalchemy.orm import Session

from app.documents.extraction import FDRExtractedFields
from app.llm_gateway.gateway import generate

EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured fields from OCR text of an Indian Fixed Deposit Receipt (FDR) or "
    "similar security-deposit instrument. Extract ONLY what is literally present in the text — "
    "never infer, guess, or fill in a plausible-looking value. Leave a field null if it is not "
    "clearly present. Respond with JSON matching the given schema."
)


class LLMGatewayExtractor:
    """Drop-in replacement for RegexFDRExtractor — same `extract(text) ->
    FDRExtractedFields` contract — backed by a real LLM call instead of
    regex. Requires a DB session only to log the call to agent_runs."""

    def __init__(
        self, session: Session | None = None, agent_name: str = "document-intelligence"
    ):
        self.session = session
        self.agent_name = agent_name

    def extract(self, text: str) -> FDRExtractedFields:
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"OCR text:\n{text}"},
        ]
        result = generate(
            "extraction",
            messages,
            response_schema=FDRExtractedFields,
            agent_name=self.agent_name,
            session=self.session,
        )
        if result.status == "ok" and result.parsed is not None:
            return result.parsed
        # Fail closed to an all-empty record (every field requires officer
        # review regardless) rather than raising mid-pipeline — the
        # pipeline's downstream validation/officer-confirm step is exactly
        # the human check this empty result routes the file into.
        return FDRExtractedFields()
