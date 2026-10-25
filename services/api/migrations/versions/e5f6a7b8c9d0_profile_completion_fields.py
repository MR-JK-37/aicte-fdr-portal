"""profile-completion fields on app_users

Backs GET /v1/me/profile-completion (R2 continuation): designation and mobile
number/verification have no column to read today, so the endpoint cannot be
real without them. mobile_verified defaults false and stays false until a real
SMS/OTP provider exists (none is configured — docs/PREFLIGHT.md) — this field
is never set true by anything in this codebase, which is the honest state, not
a bug: the "verified mobile" checklist item can never show complete until a
real provider is wired, and should keep showing as a remaining item until then.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-24 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('app_users', sa.Column('designation', sa.String(length=128), nullable=True))
    op.add_column('app_users', sa.Column('mobile_number', sa.String(length=20), nullable=True))
    op.add_column('app_users', sa.Column('mobile_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('app_users', 'mobile_verified')
    op.drop_column('app_users', 'mobile_number')
    op.drop_column('app_users', 'designation')
