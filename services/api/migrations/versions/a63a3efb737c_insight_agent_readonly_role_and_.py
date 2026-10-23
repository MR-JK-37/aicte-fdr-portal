"""insight agent readonly role and reporting view

Revision ID: a63a3efb737c
Revises: 493d15e53514
Create Date: 2026-10-23 19:17:33.881368

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a63a3efb737c'
down_revision: Union[str, Sequence[str], None] = '493d15e53514'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The Insight (text2sql) agent's entire allow-list, per the brief:
# "SELECT-only, allow-listed views, read-only role". Only these view
# names are ever permitted in a generated query (app/agents/insight.py).
VIEW_SQL = """
CREATE OR REPLACE VIEW v_instrument_summary AS
SELECT
    i.id AS instrument_id,
    i.institution_id,
    inst.name AS institution_name,
    inst.aicte_code,
    i.type,
    i.status,
    i.evidence_level,
    i.amount,
    i.issue_date,
    i.maturity_date,
    i.tenor_months,
    i.created_at
FROM instruments i
JOIN institutions inst ON inst.id = i.institution_id;

CREATE OR REPLACE VIEW v_reminder_summary AS
SELECT
    r.id AS reminder_id,
    r.instrument_id,
    r.institution_id,
    r.window,
    r.channel,
    r.status,
    r.scheduled_for,
    r.sent_at
FROM reminders r;
"""

ROLE_SQL = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fdr_readonly') THEN
    CREATE ROLE fdr_readonly LOGIN PASSWORD 'fdr_readonly_dev_password' NOSUPERUSER NOBYPASSRLS;
  END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO fdr_readonly;
GRANT SELECT ON v_instrument_summary, v_reminder_summary TO fdr_readonly;
"""


def upgrade() -> None:
    op.execute(VIEW_SQL)
    op.execute(ROLE_SQL)


def downgrade() -> None:
    op.execute("REVOKE ALL ON v_instrument_summary, v_reminder_summary FROM fdr_readonly")
    op.execute("DROP ROLE IF EXISTS fdr_readonly")
    op.execute("DROP VIEW IF EXISTS v_reminder_summary")
    op.execute("DROP VIEW IF EXISTS v_instrument_summary")
