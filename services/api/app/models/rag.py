import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# Matches app.agents.embeddings.EMBEDDING_DIM — see that module's docstring
# for why this is a local lexical hash embedding, not a real model's.
EMBEDDING_DIM = 256


class AphClauseChunk(Base):
    """A chunk of APH (Approval Process Handbook) text, for the Compliance
    RAG agent. Seeded with SYNTHETIC placeholder clauses in this build —
    the source blueprint does not include real APH text and flags
    obtaining it from AICTE as an open item (Blueprint.txt §17 item 2).
    Never cite `synthetic_placeholder=True` rows' content as real
    regulatory text; the agent must say so in every answer sourced from
    one."""

    __tablename__ = "aph_clause_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clause_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text)
    synthetic_placeholder: Mapped[bool] = mapped_column(default=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
