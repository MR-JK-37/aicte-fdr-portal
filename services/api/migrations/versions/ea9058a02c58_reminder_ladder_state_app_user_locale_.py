"""reminder ladder state, app_user locale/quiet-hours

Revision ID: ea9058a02c58
Revises: a63a3efb737c
Create Date: 2026-10-23 20:29:35.159417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea9058a02c58'
down_revision: Union[str, Sequence[str], None] = 'a63a3efb737c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'app_users',
        sa.Column('preferred_language', sa.String(length=8), nullable=False, server_default='en'),
    )
    op.add_column(
        'app_users',
        sa.Column('quiet_hours_start', sa.Integer(), nullable=False, server_default='21'),
    )
    op.add_column(
        'app_users',
        sa.Column('quiet_hours_end', sa.Integer(), nullable=False, server_default='8'),
    )
    op.add_column(
        'reminders',
        sa.Column('ladder_step', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('reminders', sa.Column('last_step_at', sa.DateTime(), nullable=True))
    op.add_column('reminders', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
    op.create_unique_constraint('uq_reminder_instrument_window', 'reminders', ['instrument_id', 'window'])


def downgrade() -> None:
    op.drop_constraint('uq_reminder_instrument_window', 'reminders', type_='unique')
    op.drop_column('reminders', 'acknowledged_at')
    op.drop_column('reminders', 'last_step_at')
    op.drop_column('reminders', 'ladder_step')
    op.drop_column('app_users', 'quiet_hours_end')
    op.drop_column('app_users', 'quiet_hours_start')
    op.drop_column('app_users', 'preferred_language')
    # ### end Alembic commands ###
