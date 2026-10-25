"""app_sessions table for real session management (R2 continuation)

Adds real session rows backing refresh-token rotation + reuse detection, and
GET/DELETE /v1/auth/sessions. RLS follows the same app_user_id-scoped pattern
as device_tokens/consent_records (a821603301c6): bureau-side roles can see/
revoke any user's sessions (IAM admin duties — AUTH_ROLES_MATRIX.md §2.2(8)
"IAM Admin can unlock"), self can always see/revoke their own. The API layer
(app/auth/router.py) narrows "bureau-side" further to identity_admin only for
cross-user session management; RLS here is defence in depth, not the only gate.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-24 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('app_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_token_hash', sa.String(length=64), nullable=True),
        sa.Column('device_label', sa.String(length=128), nullable=True),
        sa.Column('ip_area', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_app_sessions_app_user_id', 'app_sessions', ['app_user_id'])
    op.create_index('ix_app_sessions_refresh_token_hash', 'app_sessions', ['refresh_token_hash'])

    op.execute("ALTER TABLE app_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app_sessions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON app_sessions "
        "USING (is_bureau_role() OR app_user_id = current_app_user_id())"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON app_sessions")
    op.execute("ALTER TABLE app_sessions NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app_sessions DISABLE ROW LEVEL SECURITY")
    op.drop_index('ix_app_sessions_refresh_token_hash', table_name='app_sessions')
    op.drop_index('ix_app_sessions_app_user_id', table_name='app_sessions')
    op.drop_table('app_sessions')
