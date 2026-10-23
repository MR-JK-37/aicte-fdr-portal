"""release maker-checker and status fields

Revision ID: f7dc9ddd76e3
Revises: a821603301c6
Create Date: 2026-10-23 15:27:12.383455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7dc9ddd76e3'
down_revision: Union[str, Sequence[str], None] = 'a821603301c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'penalties',
        sa.Column('status', sa.String(length=32), nullable=False, server_default='unpaid'),
    )
    op.add_column('release_requests', sa.Column('scrutiny_officer_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_release_requests_scrutiny_officer_id',
        'release_requests', 'app_users', ['scrutiny_officer_id'], ['id'],
    )
    op.add_column(
        'scrutiny_observations',
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
    )


def downgrade() -> None:
    op.drop_column('scrutiny_observations', 'status')
    op.drop_constraint('fk_release_requests_scrutiny_officer_id', 'release_requests', type_='foreignkey')
    op.drop_column('release_requests', 'scrutiny_officer_id')
    op.drop_column('penalties', 'status')
