"""Forgery/Anomaly agent: turns the Phase 4 validation flags and forgery
signals (already computed by deterministic code — app.documents.validation
and app.documents.forgery) into a plain-language explanation for the
officer. Per the brief: "Explain flags in plain language... Flags only;
never auto-reject" — this agent never changes any instrument state, and
the flags it explains were detected by code, not invented by the LLM.
"""

from sqlalchemy.orm import Session

from app.documents.forgery import ForgerySignal
from app.documents.validation import ValidationFlag
from app.llm_gateway.gateway import generate

EXPLAIN_SYSTEM_PROMPT = (
    "You explain document-review flags to a non-technical scrutiny officer in plain language. "
    "You are given a list of flags that were already detected by deterministic rule-based checks — "
    "you do not decide whether anything is suspicious, you only explain the given flags clearly and "
    "suggest what the officer should check next. Never claim a flag that isn't in the list. Never "
    "recommend auto-rejecting the document; only a human decides that."
)


def explain_flags(
    session: Session,
    validation_flags: list[ValidationFlag],
    forgery_signals: list[ForgerySignal],
    *,
    agent_name: str = "forgery-anomaly",
) -> str:
    if not validation_flags and not forgery_signals:
        return "No flags were raised for this document."

    flag_lines = [f"- [{f.severity}] {f.field}: {f.message}" for f in validation_flags]
    signal_lines = [f"- [{s.severity}] {s.signal}: {s.detail}" for s in forgery_signals]
    messages = [
        {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Validation flags:\n"
            + "\n".join(flag_lines or ["(none)"])
            + "\n\nForgery signals:\n"
            + "\n".join(signal_lines or ["(none)"]),
        },
    ]
    result = generate("extraction", messages, agent_name=agent_name, session=session)
    if result.status == "ok":
        return result.content
    # Fail closed to the raw flags themselves rather than silently
    # dropping them — an officer still sees everything, just without the
    # plain-language gloss.
    return "\n".join(flag_lines + signal_lines)
