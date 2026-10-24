"""phase4_lifecycle_and_release

Revision ID: c6d7e8f9a0b1
Revises: b5e2eef8a8d4
Create Date: 2026-10-24 12:26:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c6d7e8f9a0b1'
down_revision: Union[str, Sequence[str], None] = 'b5e2eef8a8d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. policy_versions (F-13 / SPEC §2.1-2.3, §21)
    op.create_table(
        "policy_versions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("document", sa.String(256), nullable=False),
        sa.Column("clause", sa.String(128), nullable=True),
        sa.Column("source_url", sa.String(512), nullable=True),
        sa.Column("document_hash", sa.String(64), nullable=True),
        sa.Column("scope", sa.String(64), nullable=True),
        sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_payload", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("blocked_reason", sa.String(256), nullable=True),
        sa.Column("author_id", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("approver_id", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("step_up_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_policy_versions_policy_id", "policy_versions", ["policy_id"])
    op.create_index("ix_policy_versions_status", "policy_versions", ["status"])

    # 2. scheduler_runs (F-10 / SPEC §9)
    op.create_table(
        "scheduler_runs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("scheduler_id", sa.String(64), nullable=False),
        sa.Column("leased_by", sa.String(128), nullable=True),
        sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), server_default="IDLE", nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scheduler_runs_scheduler_id", "scheduler_runs", ["scheduler_id"])

    # 3. instrument_lineage (F-11 / SPEC §6.1, §7)
    op.create_table(
        "instrument_lineage",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("predecessor_id", sa.UUID(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("successor_id", sa.UUID(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("relationship_type", sa.String(32), server_default="RENEWAL", nullable=False),
        sa.Column("gap_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("overlap_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("policy_allowed_gap_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_gap_discrepancy", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("predecessor_id", "successor_id", name="uq_lineage_pred_succ"),
    )
    op.create_index("ix_instrument_lineage_pred", "instrument_lineage", ["predecessor_id"])
    op.create_index("ix_instrument_lineage_succ", "instrument_lineage", ["successor_id"])

    # 4. clearances (F-12 / SPEC §2.3, §6.1 Clause 6.46)
    op.create_table(
        "clearances",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("release_request_id", sa.UUID(), sa.ForeignKey("release_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", sa.UUID(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("cell", sa.String(64), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING_SOURCE", nullable=False),
        sa.Column("received_date", sa.Date(), nullable=True),
        sa.Column("outcome", sa.String(64), nullable=True),
        sa.Column("evidence_document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("verified_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_clearances_release_req", "clearances", ["release_request_id"])
    op.create_index("ix_clearances_inst", "clearances", ["institution_id"])

    # 5. release_checklist_items (F-12)
    op.create_table(
        "release_checklist_items",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("release_request_id", sa.UUID(), sa.ForeignKey("release_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", sa.String(32), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING_SOURCE", nullable=False),
        sa.Column("deciding_user_id", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("evidence_ref", sa.String(256), nullable=True),
        sa.Column("evidence_document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("policy_version_id", sa.UUID(), sa.ForeignKey("policy_versions.id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("release_request_id", "rule_id", name="uq_release_checklist_rule"),
    )
    op.create_index("ix_release_checklist_req", "release_checklist_items", ["release_request_id"])

    # 6. Add workflow / SoD / execution columns to release_requests
    op.add_column("release_requests", sa.Column("recommender_id", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True))
    op.add_column("release_requests", sa.Column("recommendation", sa.String(32), nullable=True))
    op.add_column("release_requests", sa.Column("recommendation_reason", sa.Text(), nullable=True))
    op.add_column("release_requests", sa.Column("recommended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("release_requests", sa.Column("approver_id", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True))
    op.add_column("release_requests", sa.Column("decision", sa.String(32), nullable=True))
    op.add_column("release_requests", sa.Column("decision_reason", sa.Text(), nullable=True))
    op.add_column("release_requests", sa.Column("step_up_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("release_requests", sa.Column("execution_evidence_ref", sa.String(128), nullable=True))
    op.add_column("release_requests", sa.Column("execution_document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=True))
    op.add_column("release_requests", sa.Column("execution_recorded_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True))
    op.add_column("release_requests", sa.Column("execution_recorded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("release_requests", sa.Column("execution_verified_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True))
    op.add_column("release_requests", sa.Column("execution_verified_at", sa.DateTime(timezone=True), nullable=True))

    # 7. Grants & RLS
    op.execute("""
    GRANT SELECT, INSERT, UPDATE, DELETE ON policy_versions TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON scheduler_runs TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON instrument_lineage TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON clearances TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON release_checklist_items TO fdr_app;

    ALTER TABLE policy_versions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY policy_versions_read_policy ON policy_versions
    FOR SELECT USING (true);
    CREATE POLICY policy_versions_write_policy ON policy_versions
    FOR ALL USING (is_bureau_role());

    ALTER TABLE scheduler_runs ENABLE ROW LEVEL SECURITY;
    CREATE POLICY scheduler_runs_policy ON scheduler_runs
    FOR ALL USING (is_bureau_role());

    ALTER TABLE instrument_lineage ENABLE ROW LEVEL SECURITY;
    CREATE POLICY instrument_lineage_policy ON instrument_lineage
    FOR ALL USING (
        is_bureau_role() OR EXISTS (
            SELECT 1 FROM instruments i
            WHERE i.id = instrument_lineage.predecessor_id
            AND i.institution_id = current_app_institution_id()
        )
    );

    ALTER TABLE clearances ENABLE ROW LEVEL SECURITY;
    CREATE POLICY clearances_policy ON clearances
    FOR ALL USING (
        is_bureau_role() OR institution_id = current_app_institution_id()
    );

    ALTER TABLE release_checklist_items ENABLE ROW LEVEL SECURITY;
    CREATE POLICY release_checklist_items_policy ON release_checklist_items
    FOR ALL USING (
        is_bureau_role() OR EXISTS (
            SELECT 1 FROM release_requests r
            WHERE r.id = release_checklist_items.release_request_id
            AND r.institution_id = current_app_institution_id()
        )
    );
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS release_checklist_items CASCADE;
    DROP TABLE IF EXISTS clearances CASCADE;
    DROP TABLE IF EXISTS instrument_lineage CASCADE;
    DROP TABLE IF EXISTS scheduler_runs CASCADE;
    DROP TABLE IF EXISTS policy_versions CASCADE;
    """)
    op.drop_column("release_requests", "execution_verified_at")
    op.drop_column("release_requests", "execution_verified_by")
    op.drop_column("release_requests", "execution_recorded_at")
    op.drop_column("release_requests", "execution_recorded_by")
    op.drop_column("release_requests", "execution_document_id")
    op.drop_column("release_requests", "execution_evidence_ref")
    op.drop_column("release_requests", "step_up_verified")
    op.drop_column("release_requests", "decision_reason")
    op.drop_column("release_requests", "decision")
    op.drop_column("release_requests", "approver_id")
    op.drop_column("release_requests", "recommended_at")
    op.drop_column("release_requests", "recommendation_reason")
    op.drop_column("release_requests", "recommendation")
    op.drop_column("release_requests", "recommender_id")
