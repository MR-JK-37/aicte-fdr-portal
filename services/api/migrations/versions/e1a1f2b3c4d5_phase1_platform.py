"""Phase 1 platform foundations: 13-role permission matrix, RLS update, outbox, idempotency, feature registry, audit checkpoints

Revision ID: e1a1f2b3c4d5
Revises: dcb3d9923d88
Create Date: 2026-10-24 09:40:00.000000
"""

from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e1a1f2b3c4d5'
down_revision: Union[str, Sequence[str], None] = 'dcb3d9923d88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Add 13-role values to app_role enum in Postgres
    with op.get_context().autocommit_block():
        for val in [
            'ORG_ADMIN', 'INSTITUTION_SUBMITTER', 'INSTITUTION_VIEWER',
            'INTAKE_OFFICER', 'FINANCE_VERIFIER', 'REGIONAL_SUPERVISOR',
            'AUDIT_REVIEWER', 'IDENTITY_ADMIN', 'PLATFORM_OPERATOR',
            'INTEGRATION_SERVICE', 'BANK_VERIFIER'
        ]:
            op.execute(f"ALTER TYPE app_role ADD VALUE IF NOT EXISTS '{val}'")

    # 1. idempotency_keys
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(length=256), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(length=8), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_idempotency_keys_expires_at', 'idempotency_keys', ['expires_at'])
    op.create_index('ix_idempotency_keys_user_key', 'idempotency_keys', ['user_id', 'key'])

    # 2. outbox
    op.create_table(
        'outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('aggregate_type', sa.String(length=64), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=128), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('dedupe_key', sa.String(length=256), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('claimed_by', sa.String(length=128), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
    )
    op.create_index('ix_outbox_unprocessed', 'outbox', ['claimed_at', 'processed_at'])

    # 3. feature_registry & connector_health_checks
    op.create_table(
        'feature_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key', sa.String(length=128), nullable=False, unique=True),
        sa.Column('state', sa.String(length=32), nullable=False, server_default='disabled'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('acceptance_evidence_ref', sa.String(length=512), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'connector_health_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('feature_key', sa.String(length=128), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('detail', postgresql.JSONB(), nullable=True),
    )

    # 4. role_permissions
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('role', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('scope', sa.String(length=64), nullable=False),
        sa.UniqueConstraint('role', 'action', 'scope', name='uq_role_permission_action_scope'),
    )

    # 5. audit_checkpoints
    op.create_table(
        'audit_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('checkpoint_index', sa.Integer(), nullable=False, unique=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('first_event_id', sa.BigInteger(), nullable=True),
        sa.Column('last_event_id', sa.BigInteger(), nullable=True),
        sa.Column('event_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chain_root_hash', sa.String(length=64), nullable=False),
        sa.Column('signature', sa.Text(), nullable=False),
        sa.Column('signer_key_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 6. app_users columns
    op.add_column('app_users', sa.Column('region_id', sa.String(length=64), nullable=True))
    op.add_column('app_users', sa.Column('delegation_limit', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('app_users', sa.Column('mfa_enrolled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('app_users', sa.Column('status', sa.String(length=32), nullable=False, server_default='active'))
    op.add_column('app_users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('app_users', sa.Column('step_up_valid_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('app_users', sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'))

    # 7. Update RLS functions and policies in Postgres
    op.execute("""
    CREATE OR REPLACE FUNCTION is_bureau_role() RETURNS boolean AS $$
      SELECT current_app_role() IN (
        'intake_officer', 'scrutiny_officer', 'finance_verifier',
        'regional_supervisor', 'competent_authority', 'audit_reviewer',
        'identity_admin', 'platform_operator', 'integration_service',
        'bureau_admin'
      );
    $$ LANGUAGE sql STABLE;

    CREATE OR REPLACE FUNCTION current_app_role_scope() RETURNS text AS $$
      SELECT current_setting('app.role_scope', true);
    $$ LANGUAGE sql STABLE;

    CREATE OR REPLACE FUNCTION current_app_assurance() RETURNS text AS $$
      SELECT current_setting('app.assurance', true);
    $$ LANGUAGE sql STABLE;
    """)

    # Grant table permissions to fdr_app role
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fdr_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON idempotency_keys TO fdr_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON outbox TO fdr_app;
        GRANT SELECT, INSERT, UPDATE ON feature_registry TO fdr_app;
        GRANT SELECT, INSERT ON connector_health_checks TO fdr_app;
        GRANT SELECT, INSERT, UPDATE ON role_permissions TO fdr_app;
        GRANT SELECT, INSERT ON audit_checkpoints TO fdr_app;
      END IF;
    END $$;
    """)

    # Enable RLS on outbox & idempotency_keys
    op.execute("""
    ALTER TABLE idempotency_keys ENABLE ROW LEVEL SECURITY;
    CREATE POLICY idempotency_keys_isolation ON idempotency_keys
      USING (is_bureau_role() OR user_id = current_app_user_id() OR current_app_role() = 'bureau_admin')
      WITH CHECK (is_bureau_role() OR user_id = current_app_user_id() OR current_app_role() = 'bureau_admin');

    ALTER TABLE outbox ENABLE ROW LEVEL SECURITY;
    CREATE POLICY outbox_insert ON outbox FOR INSERT
      WITH CHECK (true);
    CREATE POLICY outbox_select ON outbox FOR SELECT
      USING (is_bureau_role());
    CREATE POLICY outbox_update ON outbox FOR UPDATE
      USING (is_bureau_role())
      WITH CHECK (is_bureau_role());
    CREATE POLICY outbox_delete ON outbox FOR DELETE
      USING (is_bureau_role());

    ALTER TABLE feature_registry ENABLE ROW LEVEL SECURITY;
    CREATE POLICY feature_registry_read ON feature_registry
      USING (true);
    CREATE POLICY feature_registry_write ON feature_registry
      USING (current_app_role() IN ('platform_operator', 'bureau_admin'))
      WITH CHECK (current_app_role() IN ('platform_operator', 'bureau_admin'));

    ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY role_permissions_read ON role_permissions
      USING (true);
    CREATE POLICY role_permissions_write ON role_permissions
      USING (current_app_role() IN ('identity_admin', 'platform_operator', 'bureau_admin'))
      WITH CHECK (current_app_role() IN ('identity_admin', 'platform_operator', 'bureau_admin'));

    ALTER TABLE audit_checkpoints ENABLE ROW LEVEL SECURITY;
    CREATE POLICY audit_checkpoints_read ON audit_checkpoints
      USING (true);
    CREATE POLICY audit_checkpoints_write ON audit_checkpoints
      USING (current_app_role() IN ('platform_operator', 'audit_reviewer', 'bureau_admin'))
      WITH CHECK (current_app_role() IN ('platform_operator', 'audit_reviewer', 'bureau_admin'));
    """)

    # 8. Seed default Feature Registry entries per MASTER_PROMPT §3
    op.execute("""
    INSERT INTO feature_registry (id, key, state, description, updated_at) VALUES
      (gen_random_uuid(), 'in_app_inbox', 'production-enabled', 'DB-backed in-app inbox and Server-Sent Events', NOW()),
      (gen_random_uuid(), 'android_push', 'disabled', 'Android FCM HTTP v1 push notifications', NOW()),
      (gen_random_uuid(), 'ios_push', 'disabled', 'Apple Push Notification service token authentication', NOW()),
      (gen_random_uuid(), 'web_push', 'disabled', 'VAPID Web Push notifications', NOW()),
      (gen_random_uuid(), 'email', 'disabled', 'SMTP/API e-mail notifications', NOW()),
      (gen_random_uuid(), 'sms_whatsapp', 'disabled', 'SMS/WhatsApp messaging adapters', NOW()),
      (gen_random_uuid(), 'statement_import', 'production-enabled', 'MT940/CAMT.053/CSV/XLSX statement import & reconciliation', NOW()),
      (gen_random_uuid(), 'bank_verifier_portal', 'disabled', 'Participating bank verifier portal role & workflow', NOW()),
      (gen_random_uuid(), 'aicte_institution_registry', 'disabled', 'AICTE central institution registry sync API', NOW()),
      (gen_random_uuid(), 'financial_execution_system', 'disabled', 'Bank/treasury financial execution interface', NOW()),
      (gen_random_uuid(), 'ocr_local_engine', 'production-enabled', 'Local OCR extraction assist pipeline', NOW()),
      (gen_random_uuid(), 'llm_tier_p', 'sandbox-only', 'Public policy Q&A LLM gateway', NOW()),
      (gen_random_uuid(), 'llm_tier_s', 'disabled', 'Sensitive case data LLM processing', NOW()),
      (gen_random_uuid(), 'bg_sfms_nesl', 'disabled', 'Bank Guarantee / SFMS / NeSL integration', NOW()),
      (gen_random_uuid(), 'digilocker_esign', 'disabled', 'DigiLocker, eSign, API Setu, Parichay integration', NOW())
    ON CONFLICT (key) DO NOTHING;
    """)

    # 9. Seed role_permissions table from SPEC §5 / MASTER_PROMPT §8.2
    permissions = [
        # org_admin
        ('org_admin', 'view', 'own_institution'),
        ('org_admin', 'manage_institution_users', 'own_institution'),
        ('org_admin', 'download_evidence', 'own_institution'),

        # institution_submitter
        ('institution_submitter', 'view', 'own_institution'),
        ('institution_submitter', 'create_draft', 'own_institution'),
        ('institution_submitter', 'edit_draft', 'own_institution'),
        ('institution_submitter', 'submit', 'own_institution'),
        ('institution_submitter', 'upload_evidence', 'own_institution'),
        ('institution_submitter', 'download_evidence', 'own_institution'),
        ('institution_submitter', 'respond_observation', 'own_institution'),
        ('institution_submitter', 'request_release', 'own_institution'),
        ('institution_submitter', 'export_report', 'own_institution'),

        # institution_viewer
        ('institution_viewer', 'view', 'own_institution'),
        ('institution_viewer', 'download_evidence', 'own_institution'),

        # intake_officer
        ('intake_officer', 'view', 'assigned'),
        ('intake_officer', 'upload_evidence', 'assigned'),
        ('intake_officer', 'download_evidence', 'assigned'),
        ('intake_officer', 'raise_observation', 'assigned'),
        ('intake_officer', 'assign_case', 'assigned'),
        ('intake_officer', 'export_report', 'assigned'),

        # scrutiny_officer
        ('scrutiny_officer', 'view', 'assigned'),
        ('scrutiny_officer', 'upload_evidence', 'assigned'),
        ('scrutiny_officer', 'download_evidence', 'assigned'),
        ('scrutiny_officer', 'raise_observation', 'assigned'),
        ('scrutiny_officer', 'recommend', 'assigned'),
        ('scrutiny_officer', 'assign_case', 'assigned'),
        ('scrutiny_officer', 'export_report', 'assigned'),

        # finance_verifier
        ('finance_verifier', 'view', 'assigned'),
        ('finance_verifier', 'upload_evidence', 'assigned'),
        ('finance_verifier', 'download_evidence', 'assigned'),
        ('finance_verifier', 'verify_bank_evidence', 'assigned'),
        ('finance_verifier', 'reconcile_statement', 'assigned'),
        ('finance_verifier', 'resolve_exception', 'assigned'),
        ('finance_verifier', 'export_report', 'assigned'),

        # regional_supervisor
        ('regional_supervisor', 'view', 'region'),
        ('regional_supervisor', 'assign_case', 'region'),
        ('regional_supervisor', 'raise_observation', 'region'),
        ('regional_supervisor', 'recommend', 'region'),
        ('regional_supervisor', 'export_report', 'region'),

        # competent_authority
        ('competent_authority', 'view', 'delegation'),
        ('competent_authority', 'download_evidence', 'delegation'),
        ('competent_authority', 'approve_release', 'delegation'),
        ('competent_authority', 'export_report', 'delegation'),

        # audit_reviewer
        ('audit_reviewer', 'view', 'all'),
        ('audit_reviewer', 'download_evidence', 'all'),
        ('audit_reviewer', 'view_audit', 'all'),
        ('audit_reviewer', 'export_report', 'all'),

        # identity_admin
        ('identity_admin', 'manage_roles', 'all'),
        ('identity_admin', 'administer_platform', 'identity'),

        # platform_operator
        ('platform_operator', 'configure_integrations', 'all'),
        ('platform_operator', 'administer_platform', 'all'),
        ('platform_operator', 'manage_templates', 'all'),

        # integration_service
        ('integration_service', 'reconcile_statement', 'connector'),
        ('integration_service', 'verify_bank_evidence', 'connector'),

        # bank_verifier (conditional)
        ('bank_verifier', 'verify_bank_evidence', 'assigned_bank'),
    ]

    for role, action, scope in permissions:
        op.execute(f"""
        INSERT INTO role_permissions (id, role, action, scope)
        VALUES (gen_random_uuid(), '{role}', '{action}', '{scope}')
        ON CONFLICT (role, action, scope) DO NOTHING;
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_checkpoints CASCADE;")
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE;")
    op.execute("DROP TABLE IF EXISTS connector_health_checks CASCADE;")
    op.execute("DROP TABLE IF EXISTS feature_registry CASCADE;")
    op.execute("DROP TABLE IF EXISTS outbox CASCADE;")
    op.execute("DROP TABLE IF EXISTS idempotency_keys CASCADE;")
    op.drop_column('app_users', 'row_version')
    op.drop_column('app_users', 'step_up_valid_until')
    op.drop_column('app_users', 'is_active')
    op.drop_column('app_users', 'status')
    op.drop_column('app_users', 'mfa_enrolled')
    op.drop_column('app_users', 'delegation_limit')
    op.drop_column('app_users', 'region_id')
