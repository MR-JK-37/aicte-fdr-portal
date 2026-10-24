"""phase5_notifications_and_realtime

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-10-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'c6d7e8f9a0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_notifications (Inbox-first persistence / SPEC §11.2, §11.3, §11.6, MASTER_PROMPT §10)
    op.create_table(
        "user_notifications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("recipient_user_id", sa.UUID(), sa.ForeignKey("app_users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("institution_id", sa.UUID(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, default="critical_workflow"),
        sa.Column("channel", sa.String(32), nullable=False, default="in_app"),
        sa.Column("template_key", sa.String(128), nullable=False),
        sa.Column("template_version", sa.String(32), nullable=False, default="v1.0"),
        sa.Column("locale", sa.String(16), nullable=False, default="en"),
        sa.Column("status", sa.String(32), nullable=False, default="CREATED"),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("deep_link", sa.String(512), nullable=True),
        sa.Column("lock_screen_title", sa.String(256), nullable=True),
        sa.Column("lock_screen_body", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_notifications_recipient", "user_notifications", ["recipient_user_id"])
    op.create_index("ix_user_notifications_status", "user_notifications", ["status"])
    op.create_index("ix_user_notifications_category", "user_notifications", ["category"])
    op.create_index("ix_user_notifications_created_at", "user_notifications", ["created_at"])

    # 2. notification_attempts (Provider delivery attempts / SPEC §11.2, §11.3)
    op.create_table(
        "notification_attempts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_notification_id", sa.UUID(), sa.ForeignKey("user_notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_message_id", sa.String(256), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, default=1),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("result_code", sa.String(64), nullable=False),
        sa.Column("error_category", sa.String(64), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_attempts_user_notif", "notification_attempts", ["user_notification_id"])

    # 3. device_installations (Device lifecycle & token registration / SPEC §11.6, MASTER_PROMPT §10.5, §10.6)
    op.create_table(
        "device_installations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("push_token", sa.String(512), nullable=True),
        sa.Column("endpoint", sa.String(512), nullable=True),
        sa.Column("auth_key", sa.String(256), nullable=True),
        sa.Column("p256dh_key", sa.String(256), nullable=True),
        sa.Column("app_version", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_device_installations_user_id", "device_installations", ["user_id"])
    op.create_index("ix_device_installations_token", "device_installations", ["push_token"])
    op.create_index("ix_device_installations_active", "device_installations", ["is_active"])

    # 4. notification_preferences (Per-user category/channel preferences / SPEC §11.5)
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("locale", sa.String(16), nullable=False, default="en"),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("quiet_hours_start", sa.String(8), nullable=True),
        sa.Column("quiet_hours_end", sa.String(8), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "category", "channel", name="uq_user_notif_pref"),
    )
    op.create_index("ix_notification_preferences_user", "notification_preferences", ["user_id"])

    # 5. sse_events (Replay buffer for SSE Last-Event-ID / MASTER_PROMPT §10.8)
    op.create_table(
        "sse_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("sequence_id", sa.BigInteger(), sa.Identity(start=1, cycle=False), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("recipient_user_id", sa.UUID(), nullable=True),
        sa.Column("institution_id", sa.UUID(), nullable=True),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sse_events_sequence_id", "sse_events", ["sequence_id"])
    op.create_index("ix_sse_events_recipient", "sse_events", ["recipient_user_id"])
    op.create_index("ix_sse_events_created_at", "sse_events", ["created_at"])

    # 6. notification_dlq (Dead-letter queue / SPEC §11.2, §11.3, MASTER_PROMPT §10.2 step 6)
    op.create_table(
        "notification_dlq",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("outbox_id", sa.UUID(), nullable=True),
        sa.Column("user_notification_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("error_reason", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(32), nullable=False, default="DEAD_LETTER"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_dlq_status", "notification_dlq", ["status"])

    # 7. Permissions & Grants
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fdr_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fdr_app")

    # 8. RLS Policies
    for tbl in ("user_notifications", "device_installations", "notification_preferences", "notification_attempts", "sse_events", "notification_dlq"):
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")

    # user_notifications RLS
    op.execute("""
        CREATE POLICY user_notifications_access_policy ON user_notifications
        USING (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR recipient_user_id::text = current_setting('app.user_id', true)
            OR (
                current_setting('app.institution_id', true) IS NOT NULL
                AND institution_id::text = current_setting('app.institution_id', true)
            )
        )
        WITH CHECK (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR recipient_user_id::text = current_setting('app.user_id', true)
        )
    """)

    # device_installations RLS
    op.execute("""
        CREATE POLICY device_installations_access_policy ON device_installations
        USING (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR user_id::text = current_setting('app.user_id', true)
        )
        WITH CHECK (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR user_id::text = current_setting('app.user_id', true)
        )
    """)

    # notification_preferences RLS
    op.execute("""
        CREATE POLICY notification_preferences_access_policy ON notification_preferences
        USING (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR user_id::text = current_setting('app.user_id', true)
        )
        WITH CHECK (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR user_id::text = current_setting('app.user_id', true)
        )
    """)

    # Admin/system bypass for notification_attempts, sse_events, notification_dlq
    op.execute("""
        CREATE POLICY notification_attempts_policy ON notification_attempts
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY sse_events_policy ON sse_events
        USING (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
            OR recipient_user_id IS NULL
            OR recipient_user_id::text = current_setting('app.user_id', true)
            OR (
                current_setting('app.institution_id', true) IS NOT NULL
                AND institution_id::text = current_setting('app.institution_id', true)
            )
        )
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY notification_dlq_policy ON notification_dlq
        USING (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
        )
        WITH CHECK (
            current_setting('app.role', true) IN ('platform_operator', 'bureau_admin', 'system')
        )
    """)


def downgrade() -> None:
    op.drop_table("notification_dlq")
    op.drop_table("sse_events")
    op.drop_table("notification_preferences")
    op.drop_table("device_installations")
    op.drop_table("notification_attempts")
    op.drop_table("user_notifications")
