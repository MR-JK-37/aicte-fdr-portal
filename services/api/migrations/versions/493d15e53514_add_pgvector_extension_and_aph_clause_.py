"""add pgvector extension and aph clause chunks

Revision ID: 493d15e53514
Revises: ef43e7d9fd11
Create Date: 2026-10-23 19:15:37.299925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '493d15e53514'
down_revision: Union[str, Sequence[str], None] = 'ef43e7d9fd11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('aph_clause_chunks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clause_id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=256), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('synthetic_placeholder', sa.Boolean(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.Vector(256), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # aph_clause_chunks has no institution_id — it's shared reference data
    # (like banks/branches), intentionally left without RLS. Still gets
    # the fdr_app grant via the default-privileges rule from migration
    # a821603301c6 automatically; explicit here for clarity/robustness.
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON aph_clause_chunks TO fdr_app")


def downgrade() -> None:
    op.drop_table('aph_clause_chunks')
    op.execute("DROP EXTENSION IF EXISTS vector")
