"""phase3_evidence_and_verification

Revision ID: b5e2eef8a8d4
Revises: a0cac1745624
Create Date: 2026-10-24 11:08:23.528214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5e2eef8a8d4'
down_revision: Union[str, Sequence[str], None] = 'a0cac1745624'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. bank_confirmation_requests (F-06 / SPEC §2.4, §7 Machine 6)
    op.create_table(
        "bank_confirmation_requests",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("institution_id", sa.UUID(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("instrument_id", sa.UUID(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("bank_name", sa.String(128), nullable=False),
        sa.Column("branch_name", sa.String(128), nullable=True),
        sa.Column("ifsc", sa.String(16), nullable=True),
        sa.Column("account_number_ref", sa.String(64), nullable=True),
        sa.Column("tracking_number", sa.String(64), unique=True, nullable=False),
        sa.Column("status", sa.String(32), server_default="AWAITING_RESPONSE", nullable=False),
        sa.Column("requested_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("assigned_bank_verifier_id", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("response_document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("response_payload", sa.dialects.postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("decision", sa.String(32), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bcr_instrument", "bank_confirmation_requests", ["instrument_id"])
    op.create_index("ix_bcr_tracking", "bank_confirmation_requests", ["tracking_number"])

    # 2. statement_batches (F-07 / SPEC §8.3, §12.2)
    op.create_table(
        "statement_batches",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("source_filename", sa.String(256), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("account_number_masked", sa.String(64), nullable=False),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=True),
        sa.Column("closing_balance", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_lines", sa.Integer(), server_default="0", nullable=False),
        sa.Column("matched_lines", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unmatched_lines", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quarantined_lines", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quarantined_summary", sa.dialects.postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("imported_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_stmt_batches_checksum", "statement_batches", ["checksum"])

    # 3. statement_lines (F-07)
    op.create_table(
        "statement_lines",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("batch_id", sa.UUID(), sa.ForeignKey("statement_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("line_date", sa.Date(), nullable=True),
        sa.Column("utr", sa.String(64), nullable=True),
        sa.Column("narration", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(32), server_default="UNMATCHED", nullable=False),
        sa.Column("matched_instrument_id", sa.UUID(), sa.ForeignKey("instruments.id"), nullable=True),
        sa.Column("reconciliation_rule_version", sa.String(64), nullable=True),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_stmt_lines_batch", "statement_lines", ["batch_id"])
    op.create_index("ix_stmt_lines_utr", "statement_lines", ["utr"])

    # 4. reconciliation_exceptions (F-07 / SPEC §8.3)
    op.create_table(
        "reconciliation_exceptions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("statement_line_id", sa.UUID(), sa.ForeignKey("statement_lines.id"), nullable=True),
        sa.Column("instrument_id", sa.UUID(), sa.ForeignKey("instruments.id"), nullable=True),
        sa.Column("exception_type", sa.String(64), nullable=False),
        sa.Column("details", sa.dialects.postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(32), server_default="OPEN", nullable=False),
        sa.Column("resolved_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. document_extractions (F-05 / SPEC §14.1)
    op.create_table(
        "document_extractions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("instrument_id", sa.UUID(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("candidate_fields", sa.dialects.postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("reviewed_fields", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("engine", sa.String(64), server_default="tesseract-v5", nullable=False),
        sa.Column("status", sa.String(32), server_default="CANDIDATE", nullable=False),
        sa.Column("reviewed_by", sa.UUID(), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_doc_extractions_doc", "document_extractions", ["document_id"])
    op.create_index("ix_doc_extractions_inst", "document_extractions", ["instrument_id"])

    # 6. Grants & RLS
    op.execute("""
    GRANT SELECT, INSERT, UPDATE, DELETE ON bank_confirmation_requests TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON statement_batches TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON statement_lines TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON reconciliation_exceptions TO fdr_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON document_extractions TO fdr_app;

    ALTER TABLE bank_confirmation_requests ENABLE ROW LEVEL SECURITY;
    CREATE POLICY bank_confirmation_requests_policy ON bank_confirmation_requests
    FOR ALL USING (
        is_bureau_role() OR
        (current_app_role() = 'bank_verifier' AND (
            assigned_bank_verifier_id = current_app_user_id() OR
            (COALESCE(NULLIF(current_app_role_scope(), ''), '{}')::jsonb ->> 'bank_name' = bank_name)
        )) OR
        (institution_id = current_app_institution_id())
    );

    ALTER TABLE statement_batches ENABLE ROW LEVEL SECURITY;
    CREATE POLICY statement_batches_policy ON statement_batches
    FOR ALL USING (is_bureau_role());

    ALTER TABLE statement_lines ENABLE ROW LEVEL SECURITY;
    CREATE POLICY statement_lines_policy ON statement_lines
    FOR ALL USING (is_bureau_role());

    ALTER TABLE reconciliation_exceptions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY reconciliation_exceptions_policy ON reconciliation_exceptions
    FOR ALL USING (is_bureau_role());

    ALTER TABLE document_extractions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY document_extractions_policy ON document_extractions
    FOR ALL USING (
        is_bureau_role() OR EXISTS (
            SELECT 1 FROM instruments i
            WHERE i.id = document_extractions.instrument_id
            AND i.institution_id = current_app_institution_id()
        )
    );
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS document_extractions CASCADE;
    DROP TABLE IF EXISTS reconciliation_exceptions CASCADE;
    DROP TABLE IF EXISTS statement_lines CASCADE;
    DROP TABLE IF EXISTS statement_batches CASCADE;
    DROP TABLE IF EXISTS bank_confirmation_requests CASCADE;
    """)

