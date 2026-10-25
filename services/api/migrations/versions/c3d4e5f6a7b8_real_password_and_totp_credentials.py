"""real password and TOTP credentials on app_users

R2 (docs/MASTER_PROMPT_V2.md): closes the authentication bypass found in R0/R1 inspection —
`/auth/login` previously accepted any password for any registered email, and `/auth/step-up`
accepted any syntactically-valid 6-digit code. This migration adds real credential storage so
those checks can be real. `password_hash` is nullable because existing rows (created directly in
tests via `AppUser(...)`, never through a real signup) have no password yet — `app/auth/router.py`
treats a null `password_hash` as "this account cannot log in with a password" rather than as an
open door.

Revision ID: c3d4e5f6a7b8
Revises: d7e8f9a0b1c2
Create Date: 2026-10-24 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('app_users', sa.Column('password_hash', sa.String(length=256), nullable=True))
    op.add_column('app_users', sa.Column('totp_secret_encrypted', sa.String(length=256), nullable=True))
    op.add_column('app_users', sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('app_users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('app_users', sa.Column('recovery_codes_hashed', sa.ARRAY(sa.String(length=128)), nullable=True))


def downgrade() -> None:
    op.drop_column('app_users', 'recovery_codes_hashed')
    op.drop_column('app_users', 'locked_until')
    op.drop_column('app_users', 'failed_login_count')
    op.drop_column('app_users', 'totp_secret_encrypted')
    op.drop_column('app_users', 'password_hash')
