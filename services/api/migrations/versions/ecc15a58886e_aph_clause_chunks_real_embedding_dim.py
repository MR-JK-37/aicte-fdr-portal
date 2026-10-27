"""aph_clause_chunks: embedding column 256 -> 384 dims (real model swap)

app.agents.embeddings now uses a real local sentence-embedding model
(BAAI/bge-small-en-v1.5, 384 dims) instead of a 256-dim lexical hash.
pgvector's `vector(N)` type has a fixed dimension baked into the column,
so existing 256-dim rows can't be reinterpreted as 384-dim — they must
be re-embedded, not migrated in place. aph_clause_chunks is reference
data reseeded by app.agents.seed_aph_clauses.seed() (called automatically
by app.agents.rag.retrieve() whenever the table is empty, and run
explicitly after this migration in dev/staging), so clearing it here is
safe and expected, not a data-loss risk for anything a user created.

Revision ID: ecc15a58886e
Revises: c2ff66d31709
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


revision: str = 'ecc15a58886e'
down_revision: Union[str, Sequence[str], None] = 'c2ff66d31709'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("TRUNCATE aph_clause_chunks")
    op.drop_column('aph_clause_chunks', 'embedding')
    op.add_column(
        'aph_clause_chunks',
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=False),
    )


def downgrade() -> None:
    op.execute("TRUNCATE aph_clause_chunks")
    op.drop_column('aph_clause_chunks', 'embedding')
    op.add_column(
        'aph_clause_chunks',
        sa.Column('embedding', pgvector.sqlalchemy.Vector(256), nullable=False),
    )
