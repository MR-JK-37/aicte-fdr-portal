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

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.embeddings import embed
from app.llm_gateway.gateway import generate
from app.models.rag import AphClauseChunk

# Cosine distance from pgvector's <=> operator: 0 = identical, 2 =
# opposite. This threshold is deliberately conservative given the weak
# (lexical, not semantic) embedding — tune down once a real embeddings
# model is wired in and the distribution of real scores is known.
MAX_DISTANCE_THRESHOLD = 0.6

REFUSAL_TEXT = "Not found in APH; refer to Regulation Bureau."


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


def answer_compliance_question(
    session: Session, question: str, *, agent_name: str = "compliance-rag"
) -> RagAnswer:
    retrieved = retrieve(session, question, top_k=3)
    if not retrieved or retrieved[0].distance > MAX_DISTANCE_THRESHOLD:
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=retrieved)

    context_blocks = "\n\n".join(
        f"[{c.clause_id}] {c.title}\n{c.text}" for c in retrieved
    )
    placeholder_notice = (
        " NOTE: these clauses are SYNTHETIC PLACEHOLDERS for development, not real APH text — say so explicitly."
        if any(c.synthetic_placeholder for c in retrieved)
        else ""
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You answer only using the clause text provided below. Quote the relevant clause text "
                "verbatim and cite it by clause ID. If the provided clauses do not answer the question, "
                f'say "{REFUSAL_TEXT}" and nothing else. Never state a fact not present in the clause text.'
                + placeholder_notice
            ),
        },
        {
            "role": "user",
            "content": f"Clauses:\n{context_blocks}\n\nQuestion: {question}",
        },
    ]
    result = generate("rag", messages, agent_name=agent_name, session=session)
    if result.status != "ok":
        return RagAnswer(REFUSAL_TEXT, refused=True, sources=retrieved)
    return RagAnswer(result.content, refused=False, sources=retrieved)
