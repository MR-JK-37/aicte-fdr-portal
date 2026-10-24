"""institutions_onboarding_policy

Revision ID: 73b6fd5a0cc4
Revises: 3f6133e1cec6
Create Date: 2026-10-24 10:40:58.598430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73b6fd5a0cc4'
down_revision: Union[str, Sequence[str], None] = '3f6133e1cec6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON institutions;")
    op.execute("""
    CREATE POLICY tenant_isolation ON institutions
    FOR ALL USING (
        is_bureau_role() OR
        id = current_app_institution_id() OR
        current_app_user_id() IS NOT NULL
    );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON institutions;")
    op.execute("""
    CREATE POLICY tenant_isolation ON institutions
    FOR ALL USING (is_bureau_role() OR (id = current_app_institution_id()));
    """)
