"""remove voice calling and simulated clock tables

Phase 0 cleanup: the AI voice-calling module and the simulated clock are
both banned (CLAUDE.md non-negotiable #1/#10). This drops the
call_sessions table (and the app_users.call_pin_* columns that only
existed to authenticate a caller on that banned channel), and the
sim_clock table (replaced by the injectable app.clock.Clock, with
RealClock as the only clock allowed outside tests).

Revision ID: dcb3d9923d88
Revises: a8347cd6b959
Create Date: 2026-10-24 01:18:22.180662

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'dcb3d9923d88'
down_revision: Union[str, Sequence[str], None] = 'a8347cd6b959'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # DROP TABLE implicitly drops the table's own RLS policy
    # (a821603301c6 created `tenant_isolation ON call_sessions`) — nothing
    # further to clean up there.
    op.drop_table('call_sessions')
    op.drop_table('sim_clock')
    op.drop_column('app_users', 'call_pin_locked_until')
    op.drop_column('app_users', 'call_pin_hash')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('app_users', sa.Column('call_pin_hash', sa.String(length=256), nullable=True))
    op.add_column('app_users', sa.Column('call_pin_locked_until', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'sim_clock',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('offset_seconds', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'call_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('institution_id', sa.UUID(), nullable=True),
        sa.Column('app_user_id', sa.UUID(), nullable=True),
        sa.Column('reminder_id', sa.UUID(), nullable=True),
        sa.Column('language', sa.String(length=8), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('pin_attempts', sa.Integer(), nullable=False),
        sa.Column('transcript', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['app_user_id'], ['app_users.id']),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.ForeignKeyConstraint(['reminder_id'], ['reminders.id'], name='fk_call_sessions_reminder_id_reminders'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Restore the RLS policy a821603301c6 put on call_sessions (part of
    # INSTITUTION_ID_TABLES there), since re-creating the table doesn't
    # bring it back on its own.
    op.execute("ALTER TABLE call_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE call_sessions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON call_sessions "
        "USING (is_bureau_role() OR institution_id = current_app_institution_id())"
    )
