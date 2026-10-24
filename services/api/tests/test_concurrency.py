from datetime import UTC, datetime

import pytest

from app.concurrency import check_if_match, etag_from_row_version, etag_from_updated_at
from app.problem_json import ConflictError


def test_etag_from_updated_at_is_deterministic_and_quoted():
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    etag = etag_from_updated_at(ts)
    assert etag == etag_from_updated_at(ts)
    assert etag.startswith('"') and etag.endswith('"')


def test_etag_changes_when_timestamp_changes():
    a = etag_from_updated_at(datetime(2026, 1, 1, tzinfo=UTC))
    b = etag_from_updated_at(datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC))
    assert a != b


def test_check_if_match_accepts_matching_etag():
    etag = etag_from_updated_at(datetime(2026, 1, 1, tzinfo=UTC))
    check_if_match(etag, etag)  # must not raise


def test_check_if_match_accepts_wildcard():
    etag = etag_from_updated_at(datetime(2026, 1, 1, tzinfo=UTC))
    check_if_match("*", etag)  # must not raise


def test_check_if_match_rejects_stale_etag():
    current = etag_from_updated_at(datetime(2026, 1, 1, tzinfo=UTC))
    stale = etag_from_updated_at(datetime(2025, 1, 1, tzinfo=UTC))
    with pytest.raises(ConflictError):
        check_if_match(stale, current)


def test_check_if_match_requires_header():
    current = etag_from_updated_at(datetime(2026, 1, 1, tzinfo=UTC))
    with pytest.raises(ConflictError):
        check_if_match(None, current)


def test_etag_from_row_version_is_quoted_integer():
    assert etag_from_row_version(3) == '"3"'
