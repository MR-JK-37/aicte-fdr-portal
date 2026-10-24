"""Phase 2 core workflow: state_transitions, instrument_versions, institution_onboarding, case_comments, case_assignments

Revision ID: f2b2c3d4e5f6
Revises: e1a1f2b3c4d5
Create Date: 2026-10-24 10:25:00.000000
"""

from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f2b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e1a1f2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. state_transitions (append-only)
    op.create_table(
        'state_transitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_state', sa.String(length=64), nullable=False),
        sa.Column('to_state', sa.String(length=64), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=True),
        sa.Column('reason_code', sa.String(length=64), nullable=False),
        sa.Column('reason_text', sa.Text(), nullable=False),
        sa.Column('policy_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evidence_ref', sa.String(length=256), nullable=True),
        sa.Column('correlation_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_state_transitions_entity', 'state_transitions', ['entity_type', 'entity_id', 'created_at'])

    # Append-only trigger for state_transitions
    op.execute("""
    CREATE OR REPLACE FUNCTION state_transitions_no_update_or_delete()
    RETURNS TRIGGER AS $$
    BEGIN
      RAISE EXCEPTION 'state_transitions is an append-only audit record: UPDATE and DELETE are prohibited';
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_state_transitions_no_update ON state_transitions;
    CREATE TRIGGER trg_state_transitions_no_update
    BEFORE UPDATE OR DELETE ON state_transitions
    FOR EACH ROW EXECUTE FUNCTION state_transitions_no_update_or_delete();
    """)

    # 2. instrument_versions (immutable version snapshot)
    op.create_table(
        'instrument_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('instrument_id', 'version_number', name='uq_instrument_version_number'),
    )
    op.create_index('ix_instrument_versions_inst_ver', 'instrument_versions', ['instrument_id', 'version_number'])

    # 3. institution_onboarding_requests
    op.create_table(
        'institution_onboarding_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('institutions.id'), nullable=False),
        sa.Column('applicant_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=False),
        sa.Column('authority_letter_doc_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('official_id_ref', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_onboarding_status', 'institution_onboarding_requests', ['status', 'created_at'])

    # 4. case_comments (internal vs institution-visible)
    op.create_table(
        'case_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=False),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('institutions.id'), nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_case_comments_case', 'case_comments', ['case_id', 'created_at'])

    # 5. case_assignments (workload queues)
    op.create_table(
        'case_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('queue_name', sa.String(length=64), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_case_assignments_queue', 'case_assignments', ['queue_name', 'status'])
    op.create_index('ix_case_assignments_user', 'case_assignments', ['assigned_to', 'status'])

    # 6. instruments: add blind index column for FDR number exact lookup
    op.add_column('instruments', sa.Column('blind_index', sa.String(length=64), nullable=True))
    op.create_index('ix_instruments_blind_index', 'instruments', ['blind_index'])

    # 7. Enable RLS and setup policies
    for tbl in ['state_transitions', 'instrument_versions', 'institution_onboarding_requests', 'case_comments', 'case_assignments']:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY;")

    # state_transitions RLS: bureau roles see all, institutions see transitions for their own cases
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

    # instrument_versions RLS: bureau roles see all, institutions see own
    op.execute("""
    CREATE POLICY instrument_versions_policy ON instrument_versions
    FOR ALL USING (
        is_bureau_role() OR
        EXISTS (
            SELECT 1 FROM instruments i
            WHERE i.id = instrument_versions.instrument_id
            AND i.institution_id = current_app_institution_id()
        )
    );
    """)

    # institution_onboarding_requests RLS
    op.execute("""
    CREATE POLICY onboarding_requests_policy ON institution_onboarding_requests
    FOR ALL USING (
        is_bureau_role() OR
        institution_id = current_app_institution_id() OR
        applicant_user_id = current_app_user_id()
    );
    """)

    # case_comments RLS: bureau roles see all (including internal notes).
    # institution users see ONLY non-internal comments (is_internal = false) for their own institution!
    op.execute("""
    CREATE POLICY case_comments_policy ON case_comments
    FOR ALL USING (
        is_bureau_role() OR (
            institution_id = current_app_institution_id() AND
            is_internal = false
        )
    );
    """)

    # case_assignments RLS: bureau roles see all
    op.execute("""
    CREATE POLICY case_assignments_policy ON case_assignments
    FOR ALL USING (is_bureau_role());
    """)

    # 8. Grant table permissions to fdr_app
    op.execute("""
    GRANT SELECT, INSERT ON state_transitions TO fdr_app;
    GRANT SELECT, INSERT ON instrument_versions TO fdr_app;
    GRANT SELECT, INSERT, UPDATE ON institution_onboarding_requests TO fdr_app;
    GRANT SELECT, INSERT ON case_comments TO fdr_app;
    GRANT SELECT, INSERT, UPDATE ON case_assignments TO fdr_app;
    """)


def downgrade() -> None:
    op.drop_index('ix_instruments_blind_index', table_name='instruments')
    op.drop_column('instruments', 'blind_index')
    op.execute("DROP TABLE IF EXISTS case_assignments CASCADE;")
    op.execute("DROP TABLE IF EXISTS case_comments CASCADE;")
    op.execute("DROP TABLE IF EXISTS institution_onboarding_requests CASCADE;")
    op.execute("DROP TABLE IF EXISTS instrument_versions CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS trg_state_transitions_no_update ON state_transitions;")
    op.execute("DROP FUNCTION IF EXISTS state_transitions_no_update_or_delete();")
    op.execute("DROP TABLE IF EXISTS state_transitions CASCADE;")
