"""rls policies and audit immutability

Revision ID: a821603301c6
Revises: b35cb080c98c
Create Date: 2026-10-23 15:12:22.956999

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a821603301c6'
down_revision: Union[str, Sequence[str], None] = 'b35cb080c98c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables scoped by institution_id, visible cross-institution only to
# bureau-side roles (scrutiny_officer/verifier/regional_officer/
# competent_authority/bureau_admin/auditor).
INSTITUTION_ID_TABLES = [
    "trusts",
    "instruments",
    "documents",
    "verification_records",
    "discrepancies",
    "scrutiny_observations",
    "reminders",
    "escalations",
    "release_requests",
    "penalties",
    "notification_log",
    "call_sessions",
    "audit_log",
]

# Tables scoped by their own app_user_id, not institution_id.
APP_USER_ID_TABLES = ["device_tokens", "consent_records"]

FUNCTIONS_SQL = """
CREATE OR REPLACE FUNCTION current_app_role() RETURNS text AS $$
  SELECT current_setting('app.role', true);
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_app_institution_id() RETURNS uuid AS $$
  SELECT CASE WHEN coalesce(current_setting('app.institution_id', true), '') = ''
              THEN NULL
              ELSE current_setting('app.institution_id', true)::uuid
         END;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_app_user_id() RETURNS uuid AS $$
  SELECT CASE WHEN coalesce(current_setting('app.user_id', true), '') = ''
              THEN NULL
              ELSE current_setting('app.user_id', true)::uuid
         END;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION is_bureau_role() RETURNS boolean AS $$
  SELECT current_app_role() IN (
    'scrutiny_officer', 'verifier', 'regional_officer',
    'competent_authority', 'bureau_admin', 'auditor'
  );
$$ LANGUAGE sql STABLE;
"""

DROP_FUNCTIONS_SQL = """
DROP FUNCTION IF EXISTS is_bureau_role();
DROP FUNCTION IF EXISTS current_app_user_id();
DROP FUNCTION IF EXISTS current_app_institution_id();
DROP FUNCTION IF EXISTS current_app_role();
"""

AUDIT_IMMUTABILITY_SQL = """
CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_log rows are append-only and cannot be updated or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_no_update
  BEFORE UPDATE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();

CREATE TRIGGER audit_log_no_delete
  BEFORE DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
"""

DROP_AUDIT_IMMUTABILITY_SQL = """
DROP TRIGGER IF EXISTS audit_log_no_delete ON audit_log;
DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;
DROP FUNCTION IF EXISTS audit_log_immutable();
"""


RUNTIME_ROLE_SQL = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fdr_app') THEN
    CREATE ROLE fdr_app LOGIN PASSWORD 'fdr_app_dev_password' NOSUPERUSER NOBYPASSRLS;
  END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO fdr_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fdr_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fdr_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fdr_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO fdr_app;
"""

DROP_RUNTIME_ROLE_SQL = """
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM fdr_app;
REVOKE ALL ON SCHEMA public FROM fdr_app;
DROP ROLE IF EXISTS fdr_app;
"""


def upgrade() -> None:
    # `fdr` (the migration-running role) is a Postgres superuser by virtue of
    # being POSTGRES_USER on the official postgres image, and superusers
    # always bypass RLS regardless of FORCE ROW LEVEL SECURITY. The API and
    # worker processes must connect as this unprivileged role instead, or
    # RLS is a no-op for them.
    op.execute(RUNTIME_ROLE_SQL)

    op.execute(FUNCTIONS_SQL)
    op.execute(AUDIT_IMMUTABILITY_SQL)

    # institutions: tenant key is its own id, not an institution_id column.
    op.execute("ALTER TABLE institutions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE institutions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON institutions "
        "USING (is_bureau_role() OR id = current_app_institution_id())"
    )

    # app_users: visible to bureau roles, to institution-mates, or to self.
    op.execute("ALTER TABLE app_users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app_users FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON app_users "
        "USING (is_bureau_role() "
        "OR institution_id = current_app_institution_id() "
        "OR id = current_app_user_id())"
    )

    for table in INSTITUTION_ID_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (is_bureau_role() OR institution_id = current_app_institution_id())"
        )

    for table in APP_USER_ID_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (is_bureau_role() OR app_user_id = current_app_user_id())"
        )

    # banks/branches are shared reference data (no tenant key) — intentionally
    # left without RLS. agent_runs/sim_clock are internal system tables the
    # API layer, not RLS, gates (no institution_id to scope by).


def downgrade() -> None:
    for table in APP_USER_ID_TABLES + INSTITUTION_ID_TABLES + ["app_users", "institutions"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute(DROP_AUDIT_IMMUTABILITY_SQL)
    op.execute(DROP_FUNCTIONS_SQL)
    op.execute(DROP_RUNTIME_ROLE_SQL)
