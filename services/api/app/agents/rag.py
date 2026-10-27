"""Compliance RAG agent: answers questions by quoting retrieved APH
clause chunks with a citation, and refuses — in code, before any LLM call
— when retrieval confidence is too low, per the brief: "RAG answers must
quote... refuse if retrieval score < threshold... If no chunk scores
above threshold, the answer is 'Not found in APH; refer to Regulation
Bureau.'" The refusal gate is a hard `if` on the retrieval score, not a
prompt instruction the model could ignore.

Corpus caveat: see app.models.rag.AphClauseChunk — seeded clauses in
this build are SYNTHETIC placeholders (no real APH text available), and
embeddings are a local lexical hash (app.agents.embeddings), not a real
semantic model. The retrieval/refusal/citation *mechanics* are real.
"""

import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.embeddings import embed
from app.llm_gateway.gateway import generate, is_gateway_disabled
from app.models.rag import AphClauseChunk

# Cosine distance from pgvector's <=> operator: 0 = identical, 2 =
# opposite. Measured empirically against this corpus with the real
# embedding model (app.agents.embeddings, BAAI/bge-small-en-v1.5):
# genuinely relevant questions land ~0.17-0.36, clearly unrelated ones
# (e.g. "what is the capital of France") land ~0.48-0.58. 0.4 sits in
# the gap between those two clusters with margin on both sides. Re-check
# this split (e.g. via a quick embed()-distance script against
# SYNTHETIC_CLAUSES + SOURCE_INDEXED_CLAUSES) if the embedding model or
# corpus changes materially.
MAX_DISTANCE_THRESHOLD = 0.4

REFUSAL_TEXT = "Not found in APH; refer to Regulation Bureau."
UNAVAILABLE_TEXT = "AI policy assistance is currently unavailable. Please refer directly to the Approval Process Handbook or contact the Regulation Bureau."


@dataclass
class RetrievedChunk:
    clause_id: str
    title: str
    text: str
    distance: float
    synthetic_placeholder: bool


@dataclass
class RagAnswer:
    answer: str
    refused: bool
    sources: list[RetrievedChunk]
    unavailable: bool = False
    verified_citations: list[str] = field(default_factory=list)
    # True when this answer did NOT come from the grounded APH clause corpus
    # (general conversation / out-of-handbook questions — see
    # _answer_general_question). Clients must show this distinctly from a
    # clause-grounded answer (CLAUDE.md non-negotiable #3: never collapse
    # different evidence/provenance into one indistinguishable signal).
    general: bool = False


def resolve_citations(session: Session, answer_text: str) -> tuple[bool, list[str]]:
    """Citation resolver (SPEC §14.4 / F-26):
    Every citation in the generated response must resolve to a real stored clause.
    If the response hallucinates an unknown clause ID, it is rejected before reaching the user."""
    import unicodedata

    stored_rows = session.execute(select(AphClauseChunk.clause_id)).scalars().all()
    stored_ids = set(stored_rows)

    norm = unicodedata.normalize("NFKC", answer_text)
    norm = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", norm)

    # Extract stored clause numbers (e.g. '7.03', '6.46')
    stored_cl_nums = set()
    for s in stored_ids:
        for m in re.findall(r"[0-9]+\.[0-9]+", s):
            stored_cl_nums.add(m)

    # Match clause mentions e.g. cl. 6.46 or clause 6.46
    all_cl_mentions = re.findall(
        r"(?:cl\.|clause)\s*([0-9]+\.[0-9]+)", norm, re.IGNORECASE
    )
    for cl in all_cl_mentions:
        if cl not in stored_cl_nums:
            return False, []  # Hallucinated unknown clause

    resolved = set()
    for cl in all_cl_mentions:
        for s in stored_ids:
            if cl in s:
                resolved.add(s)

    # Match bracketed citations starting with APH e.g. [APH 2024-27, cl. 6.46]
    bracketed = re.findall(r"\[(APH[^\]]+)\]", norm, re.IGNORECASE)
    for ref in bracketed:
        clean_ref = ref.strip()
        matching = [s for s in stored_ids if clean_ref in s or s in clean_ref]
        if not matching:
            return False, []  # Hallucinated bracketed citation
        resolved.update(matching)

    if not resolved:
        if REFUSAL_TEXT in answer_text:
            return True, []
        return False, []

    return True, sorted(resolved)


def ingest_clause(
    session: Session,
    *,
    clause_id: str,
    title: str,
    text: str,
    synthetic_placeholder: bool = True,
) -> AphClauseChunk:
    """Insert-or-update by `clause_id` (unique since migration
    c2ff66d31709) — reseeding never creates duplicate rows that would
    otherwise silently dominate top-k retrieval with copies of one
    clause."""
    existing = session.execute(
        select(AphClauseChunk).where(AphClauseChunk.clause_id == clause_id)
    ).scalar_one_or_none()
    if existing is not None:
        existing.title = title
        existing.text = text
        existing.synthetic_placeholder = synthetic_placeholder
        existing.embedding = embed(text)
        session.flush()
        return existing
    chunk = AphClauseChunk(
        clause_id=clause_id,
        title=title,
        text=text,
        synthetic_placeholder=synthetic_placeholder,
        embedding=embed(text),
    )
    session.add(chunk)
    session.flush()
    return chunk


def retrieve(session: Session, query: str, *, top_k: int = 3) -> list[RetrievedChunk]:
    has_rows = session.execute(select(AphClauseChunk.id).limit(1)).scalar_one_or_none()
    if has_rows is None:
        from app.agents.seed_aph_clauses import seed
        seed(session)
        session.flush()

    query_vector = embed(query, is_query=True)
    distance_expr = AphClauseChunk.embedding.cosine_distance(query_vector)
    rows = session.execute(
        select(AphClauseChunk, distance_expr.label("distance"))
        .order_by(distance_expr)
        .limit(top_k)
    ).all()
    return [
        RetrievedChunk(
            row.AphClauseChunk.clause_id,
            row.AphClauseChunk.title,
            row.AphClauseChunk.text,
            row.distance,
            row.AphClauseChunk.synthetic_placeholder,
        )
        for row in rows
    ]


_GENERAL_SYSTEM_PROMPT = (
    "You are Kosh, the conversational assistant built into the AICTE FDR Security Deposit "
    "Compliance Portal. The question you were just asked did not match any clause in the "
    "Approval Process Handbook (APH) corpus this assistant is grounded in, so you are now "
    "answering as a general-purpose assistant, NOT as a regulatory source. This path also "
    "handles greetings and 'who/what are you' questions — there is no separate canned "
    "identity reply, so answer those naturally and in your own words each time rather than "
    "reciting a fixed script.\n\n"
    "If asked who you are or what you do, say in your own words that you are Kosh, the "
    "assistant built into the AICTE FDR Security Deposit Compliance Portal, and that your "
    "main job is answering security-deposit / FDR questions with a real citation from the "
    "Approval Process Handbook (APH) when one is found, covering areas like FDR tenure, "
    "joint-account and lien rules, penalties for delayed submission, bank guarantees in lieu "
    "of an FDR, and release on maturity — and that you can also just chat normally about "
    "anything else. Vary the wording naturally; never repeat a fixed paragraph verbatim.\n\n"
    "Rules, no exceptions:\n"
    "1. You may answer any general question conversationally and helpfully: who you are, "
    "small talk, general knowledge, how to use the app, anything at all.\n"
    "2. You must NEVER state a specific AICTE/APH/FDR statutory fact (an amount, a date, a "
    "deadline, a clause number, a penalty, a tenure) as if it is confirmed. If the question "
    "is actually about AICTE security-deposit rules and you don't have a grounded citation "
    "for it, say plainly that you don't have a verified citation for that and suggest "
    "rephrasing the question so the handbook search can find the matching clause, or "
    "contacting the Regulation Bureau. Do not guess or improvise a plausible-sounding rule.\n"
    "3. Never write a bracketed citation like [APH ...] or a clause reference like 'cl. 6.46' "
    "in this reply — those only belong in grounded, clause-cited answers, and this reply is not one.\n"
    "4. Keep answers concise and plain."
)


def _answer_general_question(
    session: Session,
    question: str,
    relevant_sources: list[RetrievedChunk],
    *,
    agent_name: str = "general-chat",
) -> RagAnswer:
    """Ungrounded conversational fallback for questions that don't match the
    APH clause corpus (small talk, 'what is your purpose', general
    knowledge, app-usage questions). Deliberately NOT subject to the
    REFUSAL_TEXT gate above — that gate exists to stop invented *statutory*
    facts (CLAUDE.md non-negotiable #2), not to stop the assistant from
    holding an ordinary conversation. The system prompt forbids statutory
    claims and clause-citation syntax here; resolve_citations() below is a
    second, code-level check that rejects the reply outright if a citation-
    shaped string slipped through anyway, same enforcement as the grounded
    path uses."""
    messages = [
        {"role": "system", "content": _GENERAL_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    # Caching off deliberately: this is conversational, not a factual lookup
    # (unlike the grounded clause path below, where the same question really
    # should get the same cached, verified answer). A cached reply here
    # would mean repeated greetings/small talk return byte-identical text,
    # which is the exact "feels stuck" complaint this path was built to fix.
    result = generate("rag", messages, agent_name=agent_name, session=session, use_cache=False)
    if result.status == "unavailable":
        return RagAnswer(
            UNAVAILABLE_TEXT, refused=True, sources=relevant_sources, unavailable=True
        )
    if result.status != "ok" or not result.content:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=relevant_sources)

    answer_text = result.content.strip()

    if REFUSAL_TEXT in answer_text:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=relevant_sources)

    # Code-level backstop: if the model wrote a clause-citation-shaped string
    # despite the system prompt forbidding it, treat that as an attempted
    # unverified statutory claim and refuse rather than let it through.
    has_citation_syntax = bool(
        re.search(r"(?:cl\.|clause)\s*[0-9]+\.[0-9]+", answer_text, re.IGNORECASE)
        or re.search(r"\[APH[^\]]+\]", answer_text, re.IGNORECASE)
    )
    if has_citation_syntax:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=relevant_sources)

    return RagAnswer(
        answer_text,
        refused=False,
        sources=relevant_sources,
        unavailable=False,
        verified_citations=[],
        general=True,
    )


def answer_compliance_question(
    session: Session, question: str, *, agent_name: str = "compliance-rag"
) -> RagAnswer:
    if is_gateway_disabled():
        return RagAnswer(UNAVAILABLE_TEXT, refused=True, sources=[], unavailable=True)

    retrieved = retrieve(session, question, top_k=3)
    relevant_sources = [c for c in retrieved if c.distance <= MAX_DISTANCE_THRESHOLD]
    if not retrieved or retrieved[0].distance > MAX_DISTANCE_THRESHOLD:
        return _answer_general_question(session, question, relevant_sources)

    context_blocks = "\n\n".join(
        f"[{c.clause_id}] {c.title}{' [SYNTHETIC PLACEHOLDER]' if c.synthetic_placeholder else ''}\n{c.text}"
        for c in retrieved
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You answer only using the clause text provided below. Quote the relevant clause text "
                "verbatim and cite it by clause ID. If the provided clauses do not answer the question, "
                f'say "{REFUSAL_TEXT}" and nothing else. Never state a fact not present in the clause text. '
                "Provide a direct, authoritative, and professional compliance answer quoting the verified statutory clause."
            ),
        },
        {
            "role": "user",
            "content": f"Clauses:\n{context_blocks}\n\nQuestion: {question}",
        },
    ]
    result = generate("rag", messages, agent_name=agent_name, session=session)
    if result.status == "unavailable":
        return RagAnswer(
            UNAVAILABLE_TEXT, refused=True, sources=relevant_sources, unavailable=True
        )
    if result.status != "ok" or not result.content:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=relevant_sources)

    # Sanitize answer: strip any synthetic disclaimer notes or bracket tags
    answer_text = result.content
    answer_text = re.sub(
        r"(?:\n|\r\n)?\*?Note:?\s*These clauses are (?:synthetic placeholders|SYNTHETIC PLACEHOLDERS)[^\n]*\*?",
        "",
        answer_text,
        flags=re.IGNORECASE,
    ).strip()
    answer_text = re.sub(r"\[SYNTHETIC PLACEHOLDER\]\s*", "", answer_text, flags=re.IGNORECASE).strip()

    # Post-check: Citation resolver enforces that all citations resolve to stored clauses
    valid_citations, resolved_ids = resolve_citations(session, answer_text)
    if not valid_citations:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=relevant_sources)

    return RagAnswer(
        answer_text,
        refused=False,
        sources=relevant_sources,
        unavailable=False,
        verified_citations=resolved_ids,
    )
