import pytest
from sqlalchemy import create_engine, text

from app.agents.insight import (
    DEFAULT_LIMIT,
    SqlValidationError,
    execute_validated_sql,
    validate_sql,
)
from app.config import settings


def test_valid_select_on_allowed_view_passes():
    sql = validate_sql(
        "SELECT instrument_id, status FROM v_instrument_summary WHERE status = 'ACTIVE'"
    )
    assert "v_instrument_summary" in sql
    assert "LIMIT" in sql.upper()


def test_limit_is_not_duplicated_when_already_present():
    sql = validate_sql("SELECT instrument_id FROM v_instrument_summary LIMIT 10")
    assert sql.upper().count("LIMIT") == 1


def test_default_limit_is_injected_when_missing():
    sql = validate_sql("SELECT instrument_id FROM v_instrument_summary")
    assert str(DEFAULT_LIMIT) in sql


def test_non_allowlisted_table_rejected():
    with pytest.raises(SqlValidationError, match="non-allow-listed"):
        validate_sql("SELECT * FROM instruments")  # the base table, not the view


def test_insert_statement_rejected():
    with pytest.raises(SqlValidationError, match="only a single SELECT"):
        validate_sql("INSERT INTO v_instrument_summary (instrument_id) VALUES ('x')")


def test_delete_statement_rejected():
    with pytest.raises(SqlValidationError, match="only a single SELECT"):
        validate_sql("DELETE FROM v_instrument_summary")


def test_multiple_statements_rejected():
    with pytest.raises(SqlValidationError, match="exactly one statement"):
        validate_sql("SELECT 1 FROM v_instrument_summary; DROP TABLE instruments;")


def test_unparseable_sql_rejected():
    with pytest.raises(SqlValidationError, match="could not parse"):
        validate_sql("THIS IS NOT SQL AT ALL ;;; (((")


def test_execute_validated_sql_runs_against_the_real_readonly_role():
    sql = validate_sql("SELECT count(*) AS n FROM v_instrument_summary")
    result = execute_validated_sql(sql)
    assert result.row_count == 1
    assert "n" in result.rows[0]


def test_readonly_role_cannot_write_even_if_validation_were_bypassed():
    """Defence in depth: validate_sql() already blocks DML, but this
    proves the DB role itself is the real enforcement boundary, not just
    the Python-side check — fdr_readonly has no INSERT/UPDATE/DELETE
    grant on the underlying base table, so even a validation bypass
    couldn't write. (The views aren't independently useful as a write
    target either — Postgres refuses DELETE on a multi-table join view
    outright, "not automatically updatable" — but the real boundary this
    test is for is the role's table-level grants, hence testing against
    the base table directly.)"""
    engine = create_engine(settings.readonly_database_url, future=True)
    with engine.connect() as conn, pytest.raises(Exception, match="permission denied"):
        conn.execute(text("DELETE FROM instruments"))
    engine.dispose()
