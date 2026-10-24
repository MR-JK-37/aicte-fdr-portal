"""update_state_transitions_and_case_comments_rls

Revision ID: a0cac1745624
Revises: 73b6fd5a0cc4
Create Date: 2026-10-24 10:47:47.735915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0cac1745624'
down_revision: Union[str, Sequence[str], None] = '73b6fd5a0cc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update state_transitions policy to cover observations and documents as well as instruments
    op.execute("DROP POLICY IF EXISTS state_transitions_policy ON state_transitions;")
    op.execute("""
    CREATE POLICY state_transitions_policy ON state_transitions
    FOR ALL USING (
        is_bureau_role() OR
        (entity_type = 'instrument' AND EXISTS (
            SELECT 1 FROM instruments i WHERE i.id = state_transitions.entity_id AND i.institution_id = current_app_institution_id()
        )) OR
        (entity_type = 'observation' AND EXISTS (
            SELECT 1 FROM scrutiny_observations o WHERE o.id = state_transitions.entity_id AND o.institution_id = current_app_institution_id()
        )) OR
        (entity_type = 'document' AND EXISTS (
            SELECT 1 FROM documents d WHERE d.id = state_transitions.entity_id AND d.institution_id = current_app_institution_id()
        ))
    );
    """)

    # 2. Update case_comments policy so public comments linked to instrument are visible to the institution
    op.execute("DROP POLICY IF EXISTS case_comments_policy ON case_comments;")
    op.execute("""
    CREATE POLICY case_comments_policy ON case_comments
    FOR ALL USING (
        is_bureau_role() OR (
            is_internal = false AND (
                institution_id = current_app_institution_id() OR
                EXISTS (
                    SELECT 1 FROM instruments i
                    WHERE i.id = case_comments.case_id
                    AND i.institution_id = current_app_institution_id()
                )
            )
        )
    );
    """)

    # 3. Update outbox_select policy so INSERT ... ON CONFLICT DO NOTHING succeeds for all actors
    op.execute("DROP POLICY IF EXISTS outbox_select ON outbox;")
    op.execute("""
    CREATE POLICY outbox_select ON outbox FOR SELECT
      USING (true);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS outbox_select ON outbox;")
    op.execute("""
    CREATE POLICY outbox_select ON outbox FOR SELECT
      USING (is_bureau_role());
    """)

    op.execute("DROP POLICY IF EXISTS state_transitions_policy ON state_transitions;")
    op.execute("""
    CREATE POLICY state_transitions_policy ON state_transitions
    FOR ALL USING (
        is_bureau_role() OR
        EXISTS (
            SELECT 1 FROM instruments i
            WHERE i.id = state_transitions.entity_id
            AND i.institution_id = current_app_institution_id()
        )
    );
    """)

    op.execute("DROP POLICY IF EXISTS case_comments_policy ON case_comments;")
    op.execute("""
    CREATE POLICY case_comments_policy ON case_comments
    FOR ALL USING (
        is_bureau_role() OR (
            is_internal = false AND institution_id = current_app_institution_id()
        )
    );
    """)

