"""Insight agent: natural-language question -> SQL -> result, per the
brief's exact spec: "sqlglot validation, SELECT-only, allow-listed views,
read-only role, 5s timeout, LIMIT". Every one of those five constraints
is enforced here, not just described:

- sqlglot validation: the generated SQL is parsed; anything that fails
  to parse as a single statement is rejected before touching the DB.
- SELECT-only: the parsed statement must be exactly one SELECT.
- allow-listed views: every table reference in the parsed statement must
  be in ALLOWED_VIEWS (migration a63a3efb737c's v_instrument_summary /
  v_reminder_summary) — not the underlying base tables.
- read-only role: executed as `fdr_readonly`, a DB role with SELECT-only
  grants on exactly those two views (no base-table access at all).
- 5s timeout: `SET LOCAL statement_timeout` on the readonly connection.
- LIMIT: injected if the generated query doesn't already have one.
"""

from dataclasses import dataclass
from functools import lru_cache

import sqlglot
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.llm_gateway.gateway import generate

ALLOWED_VIEWS = {"v_instrument_summary", "v_reminder_summary"}
DEFAULT_LIMIT = 200
STATEMENT_TIMEOUT_MS = 5000

TEXT2SQL_SYSTEM_PROMPT = (
    "You write a single read-only PostgreSQL SELECT query answering the user's question. "
    f"You may ONLY reference these views: {', '.join(sorted(ALLOWED_VIEWS))}. "
    "Never reference any other table or view. Never write INSERT/UPDATE/DELETE/DDL. "
    "Respond with ONLY the SQL query, no explanation, no markdown fences."
)


class SqlValidationError(Exception):
    pass


@dataclass
class InsightResult:
    sql: str
    rows: list[dict]
    row_count: int


@lru_cache
def _readonly_engine():
    return create_engine(settings.readonly_database_url, future=True)


def validate_sql(raw_sql: str) -> str:
    """Returns the validated (and LIMIT-ensured) SQL, or raises
    SqlValidationError. Pure function — no DB access — so it's cheap to
    unit test every rejection path without a live database."""
    raw_sql = raw_sql.strip().strip(";")
    try:
        statements = sqlglot.parse(raw_sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError(f"could not parse SQL: {exc}") from exc

    if len(statements) != 1:
        raise SqlValidationError(
            f"expected exactly one statement, got {len(statements)}"
        )
    stmt = statements[0]
    if stmt is None or stmt.key != "select":
        raise SqlValidationError("only a single SELECT statement is permitted")

    referenced = {table.name for table in stmt.find_all(sqlglot.exp.Table)}
    disallowed = referenced - ALLOWED_VIEWS
    if disallowed:
        raise SqlValidationError(
            f"query references non-allow-listed table(s): {sorted(disallowed)}"
        )

    if stmt.args.get("limit") is None:
        stmt = stmt.limit(DEFAULT_LIMIT)

    return stmt.sql(dialect="postgres")


def execute_validated_sql(sql: str) -> InsightResult:
    engine = _readonly_engine()
    with engine.connect() as conn:
        conn.execute(text(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}"))
        result = conn.execute(text(sql))
        rows = [dict(row._mapping) for row in result.fetchall()]
    return InsightResult(sql=sql, rows=rows, row_count=len(rows))


def ask(
    session: Session, question: str, *, agent_name: str = "insight"
) -> InsightResult:
    messages = [
        {"role": "system", "content": TEXT2SQL_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    gen_result = generate("text2sql", messages, agent_name=agent_name, session=session)
    if gen_result.status != "ok" or not gen_result.content:
        raise SqlValidationError(
            "the text2sql model call did not succeed — see agent_runs for detail"
        )

    validated_sql = validate_sql(gen_result.content)
    return execute_validated_sql(validated_sql)
