"""add_phase2_instrument_statuses

Revision ID: 3f6133e1cec6
Revises: f2b2c3d4e5f6
Create Date: 2026-10-24 10:26:24.949719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f6133e1cec6'
down_revision: Union[str, Sequence[str], None] = 'f2b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres enum values must be added with COMMIT outside a multi-statement transaction if not using raw connection,
    # or ALTER TYPE ... ADD VALUE IF NOT EXISTS
    new_statuses = [
        'DRAFT',
        'INTAKE_REVIEW',
        'SCRUTINY',
        'ACTIVE_TRACKING',
        'SUPERSEDED',
        'CANCELLED',
        'ARCHIVED',
        'RETURNED_FOR_CORRECTION',
    ]
    for status in new_statuses:
        op.execute(f"ALTER TYPE instrument_status ADD VALUE IF NOT EXISTS '{status}';")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type easily.
    pass
