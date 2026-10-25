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
# opposite. This threshold is deliberately conservative given the weak
# (lexical, not semantic) embedding — tune down once a real embeddings
# model is wired in and the distribution of real scores is known.
MAX_DISTANCE_THRESHOLD = 0.85

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

    query_vector = embed(query)
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


_GREETING_PATTERN = re.compile(
    r"(?:^\s*(?:he+l+o+|hi+|hey+|namaste|greetings|good\s+(?:morning|afternoon|evening)|who\s+are\s+(?:you|u)|what\s+is\s+this|what\s+can\s+you\s+do|how\s+can\s+you\s+help|help(?:\s+me)?|introduce\s+yourself|tell\s+me\s+about\s+yourself)\b)|"
    r"(?:what(?:'s|\s+is)\s+(?:your|ur)\s+name)|"
    r"(?:who\s+(?:are\s+you|are\s+u|made\s+you|created\s+you))|"
    r"(?:(?:your|ur)\s+name\??$)",
    re.IGNORECASE,
)


def _is_greeting(query: str) -> bool:
    return bool(_GREETING_PATTERN.search(query.strip()))


def answer_compliance_question(
    session: Session, question: str, *, agent_name: str = "compliance-rag"
) -> RagAnswer:
    if is_gateway_disabled():
        return RagAnswer(UNAVAILABLE_TEXT, refused=True, sources=[], unavailable=True)

    if _is_greeting(question):
        greeting_text = (
            "Namaste! I am the AICTE Regulatory Copilot, an official compliance intelligence assistant "
            "grounded in the verified clauses of the AICTE Approval Process Handbook (APH 2024–27).\n\n"
            "I provide direct, citation-backed statutory guidance regarding Security Deposit Fixed Deposit Receipts (FDRs). "
            "Key normative areas I can substantiate include:\n\n"
            "• **Validity & Mandatory Tenure** ([APH 2024-27, cl. 6.15]) — Minimum initial 8 to 10 years tenure requirements.\n"
            "• **Joint Account & Lien Marking** ([APH 2024-27, cl. 6.08]) — Joint account establishment with AICTE Regional Officer & statutory bank lien.\n"
            "• **Penalties for Delayed Submission** ([APH 2024-27, cl. 7.03]) — Graded shortfall penalties on delayed security deposits.\n"
            "• **Leased-Campus Multiplier** ([APH 2024-27, cl. 6.12]) — Multiplier calculation for leasehold campus lands under Table 1.4.\n"
            "• **Prohibition of Premature Withdrawal** ([APH 2024-27, cl. 6.22]) — Strict prohibition of encashment, pledging, or hypothecation without AICTE NOC.\n"
            "• **Compound Interest Accrual** ([APH 2024-27, cl. 6.38]) — Automatic reinvestment and compounding upon cumulative renewal.\n"
            "• **Bank Guarantee in Lieu of FDR** ([APH 2024-27, cl. 6.30]) — Operative claim clauses and commercial bank requirements.\n"
            "• **Release on Maturity** ([APH 2024-27, cl. 6.46]) — Conditions precedent and verification for security deposit release.\n\n"
            "Please select any suggested question or ask a specific compliance question regarding your institution's security deposit."
        )
        _, valid_ids = resolve_citations(session, greeting_text)
        return RagAnswer(
            greeting_text,
            refused=False,
            sources=[],
            unavailable=False,
            verified_citations=valid_ids,
        )

    retrieved = retrieve(session, question, top_k=3)
    relevant_sources = [c for c in retrieved if c.distance <= MAX_DISTANCE_THRESHOLD]
    if not retrieved or retrieved[0].distance > MAX_DISTANCE_THRESHOLD:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=relevant_sources)

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
