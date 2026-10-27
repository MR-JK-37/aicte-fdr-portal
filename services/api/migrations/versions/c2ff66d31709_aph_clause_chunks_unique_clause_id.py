"""aph_clause_chunks: unique clause_id, dedupe existing rows

The RAG seed (app.agents.seed_aph_clauses.seed) is invoked lazily from
app.agents.rag.retrieve() whenever the table is empty, with no guard
against two concurrent requests both observing "empty" and seeding
twice. In practice this produced duplicate rows per clause_id, so a
top-k=3 retrieval could return the same clause three times instead of
three distinct ones. A unique constraint makes a repeat seed fail loudly
instead of silently duplicating; combined with the idempotent seed()
(checks existing clause_ids before inserting) this closes the race.

Revision ID: c2ff66d31709
Revises: f6a7b8c9d0e1
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2ff66d31709'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the oldest row per clause_id, drop the rest, before the
    # constraint can be added.
    op.execute(
        """
        DELETE FROM aph_clause_chunks a
        USING aph_clause_chunks b
        WHERE a.clause_id = b.clause_id
          AND a.id > b.id
        """
    )
    op.create_unique_constraint(
        "uq_aph_clause_chunks_clause_id", "aph_clause_chunks", ["clause_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_aph_clause_chunks_clause_id", "aph_clause_chunks", type_="unique"
    )
