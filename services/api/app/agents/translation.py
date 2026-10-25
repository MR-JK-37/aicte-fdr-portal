"""Machine-translation draft agent (F-27 / SPEC §14.1 / config/LLM_PROVIDERS.yaml).

Translates public UI strings and approved notification templates into Indian
languages (e.g. Hindi, Tamil) for human review.
Rules:
- Tier P only (public strings, never case/institution data).
- Post-check: ICU message placeholders (e.g. {amount}, {instrument_number})
  MUST be strictly preserved in the translated text.
- Catalog status: drafts are saved as 'machine_draft'; production shows ONLY
  'reviewed' strings in that locale and falls back to English otherwise.
- On exhausted or gateway unavailable: retains English source text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.llm_gateway.gateway import generate, is_gateway_disabled

PLACEHOLDER_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class TranslationDraftPayload(BaseModel):
    target_language: str
    translated_text: str = Field(
        description="Translated text with ICU placeholders intact"
    )
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


@dataclass
class TranslationDraftResult:
    status: str  # "machine_draft" | "unavailable" | "fallback_english"
    source_text: str
    target_language: str
    translated_text: str
    placeholders_preserved: bool
    requires_human_review: bool = True
    disclaimer: str = "Draft translation for human review only — not certified."


def extract_icu_placeholders(text: str) -> set[str]:
    """Finds all {param} tokens in the source text."""
    return set(PLACEHOLDER_REGEX.findall(text))


def verify_icu_placeholders_preserved(source: str, translation: str) -> bool:
    """Post-check: Asserts that every placeholder in the source text
    is also present in the translated text."""
    source_tokens = extract_icu_placeholders(source)
    trans_tokens = extract_icu_placeholders(translation)
    return source_tokens == trans_tokens


def generate_translation_draft(
    source_text: str,
    target_language: str,
    *,
    session: Session | None = None,
    agent_name: str = "translation-draft-agent",
) -> TranslationDraftResult:
    """Generates a machine-translated draft of a public UI string for human review."""
    if is_gateway_disabled():
        return TranslationDraftResult(
            status="fallback_english",
            source_text=source_text,
            target_language=target_language,
            translated_text=source_text,  # on_exhausted: keep_english
            placeholders_preserved=True,
            requires_human_review=False,
            disclaimer="AI gateway unavailable; showing authoritative English text.",
        )

    placeholders = extract_icu_placeholders(source_text)
    placeholder_instruction = ""
    if placeholders:
        ph_list = ", ".join(f"{{{p}}}" for p in sorted(placeholders))
        placeholder_instruction = f" MANDATORY: Preserve exact placeholders verbatim: {ph_list}. Do not translate or alter them."

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a translation assistant translating public UI strings into {target_language}. "
                "Respond with accurate, natural Indian administrative terminology. "
                "Respond in JSON matching the schema." + placeholder_instruction
            ),
        },
        {
            "role": "user",
            "content": f"Source text: {source_text}",
        },
    ]

    result = generate(
        "translation_draft",
        messages,
        tier="P",
        response_schema=TranslationDraftPayload,
        agent_name=agent_name,
        session=session,
    )

    if result.status != "ok" or result.parsed is None:
        # Fall back to English
        return TranslationDraftResult(
            status="fallback_english",
            source_text=source_text,
            target_language=target_language,
            translated_text=source_text,
            placeholders_preserved=True,
            requires_human_review=False,
            disclaimer="Translation draft unavailable; showing authoritative English text.",
        )

    parsed: TranslationDraftPayload = result.parsed  # type: ignore

    # Post-check: ICU placeholders preserved
    if not verify_icu_placeholders_preserved(source_text, parsed.translated_text):
        return TranslationDraftResult(
            status="fallback_english",
            source_text=source_text,
            target_language=target_language,
            translated_text=source_text,
            placeholders_preserved=False,
            requires_human_review=False,
            disclaimer="Translation draft rejected: ICU placeholders corrupted; showing authoritative English text.",
        )

    return TranslationDraftResult(
        status="machine_draft",
        source_text=source_text,
        target_language=target_language,
        translated_text=parsed.translated_text,
        placeholders_preserved=True,
        requires_human_review=True,
        disclaimer="Draft translation for human review only — not certified.",
    )
