import logging
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app import main


class _FakeQuery:
    def __init__(self, count: int):
        self._count = count

    def count(self) -> int:
        return self._count


class _FakeSession:
    def __init__(self, *, count: int, commit_error: Exception | None = None):
        self._count = count
        self._commit_error = commit_error
        self.rollback_called = False
        self.commit_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, _model):
        return _FakeQuery(self._count)

    def commit(self) -> None:
        self.commit_called = True
        if self._commit_error is not None:
            raise self._commit_error

    def rollback(self) -> None:
        self.rollback_called = True


def _integrity_error(*, constraint_name: str) -> IntegrityError:
    message = (
        "duplicate key value violates unique constraint "
        f'"{constraint_name}"'
    )
    orig = Exception(message)
    orig.diag = SimpleNamespace(constraint_name=constraint_name)  # type: ignore[attr-defined]
    return IntegrityError("INSERT INTO aph_clause_chunks ...", {}, orig)


def test_startup_seed_duplicate_constraint_rolls_back_and_logs_info(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake_session = _FakeSession(
        count=0,
        commit_error=_integrity_error(
            constraint_name="uq_aph_clause_chunks_clause_id"
        ),
    )
    monkeypatch.setattr(main, "SessionLocal", lambda: fake_session)
    seeded = {"called": False}

    def fake_seed(_session) -> None:
        seeded["called"] = True

    monkeypatch.setattr("app.agents.seed_aph_clauses.seed", fake_seed)
    caplog.set_level(logging.INFO, logger="app.main")

    main.ensure_aph_clauses_seeded()

    assert seeded["called"] is True
    assert fake_session.commit_called is True
    assert fake_session.rollback_called is True
    assert "startup seed skipped after duplicate insert race" in caplog.text


def test_startup_seed_unexpected_integrity_error_rolls_back_and_logs_exception(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake_session = _FakeSession(
        count=0,
        commit_error=_integrity_error(constraint_name="other_constraint"),
    )
    monkeypatch.setattr(main, "SessionLocal", lambda: fake_session)
    monkeypatch.setattr("app.agents.seed_aph_clauses.seed", lambda _session: None)
    caplog.set_level(logging.ERROR, logger="app.main")

    main.ensure_aph_clauses_seeded()

    assert fake_session.commit_called is True
    assert fake_session.rollback_called is True
    assert "Unexpected integrity error while seeding APH clauses at startup." in caplog.text


def test_startup_seed_is_skipped_when_rows_already_exist(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_session = _FakeSession(count=3)
    monkeypatch.setattr(main, "SessionLocal", lambda: fake_session)
    seeded = {"calls": 0}

    def fake_seed(_session) -> None:
        seeded["calls"] += 1

    monkeypatch.setattr("app.agents.seed_aph_clauses.seed", fake_seed)

    main.ensure_aph_clauses_seeded()

    assert seeded["calls"] == 0
    assert fake_session.commit_called is False
    assert fake_session.rollback_called is False
