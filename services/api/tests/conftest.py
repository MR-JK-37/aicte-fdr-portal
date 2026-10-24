import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://fdr_app:fdr_app_dev_password@localhost:5434/fdr",
)
SUPERUSER_DATABASE_URL = os.environ.get(
    "SUPERUSER_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)
VALKEY_URL = os.environ.get("VALKEY_URL", "redis://localhost:6379/0")

# Tables these tests write to that must start each test session empty.
# Reference/structural tables (banks, branches) are intentionally excluded
# — they're not what any test's assertions depend on being absent.
_VOLATILE_TABLES = [
    "notification_log",
    "device_tokens",
    "consent_records",
    "escalations",
    "reminders",
    "release_requests",
    "penalties",
    "scrutiny_observations",
    "discrepancies",
    "verification_records",
    "documents",
    "audit_checkpoints",
    "audit_log",
    "instruments",
    "app_users",
    "trusts",
    "institutions",
    "aph_clause_chunks",
]


@pytest.fixture(scope="session", autouse=True)
def _reset_db_once_per_session():
    """Truncates all tables the test suite writes to, once at the start of
    the session. Without this, these tests (necessarily integration tests
    against the live Compose Postgres, not an in-memory DB — RLS and the
    audit-immutability trigger only mean anything against real Postgres)
    accumulate rows across every local `pytest` invocation during
    development, which silently corrupts assertions that count rows or
    compare hashes/perceptual-hashes against "nothing else in the table" —
    exactly what caused a real false failure here (a pHash duplicate flag
    tripped by a leftover document from an earlier manual test run, not a
    bug in the detector)."""
    engine = create_engine(SUPERUSER_DATABASE_URL, future=True)
    with engine.begin() as conn:
        conn.execute(
            text(f"TRUNCATE {', '.join(_VOLATILE_TABLES)} RESTART IDENTITY CASCADE")
        )
    engine.dispose()

    # Same problem, same fix, for the LLM gateway's Valkey-backed state
    # (circuit breakers, token buckets, response cache): without this, a
    # circuit tripped by one failing run stays "open" into the next
    # `pytest` invocation (60s TTL — long enough to span two closely
    # spaced local runs) and silently makes later tests skip the provider
    # they're meant to be exercising. Found exactly this way: a cache/
    # circuit test that passed in isolation failed when run as part of a
    # second consecutive suite run, with zero HTTP calls made at all.
    redis_client = redis.Redis.from_url(VALKEY_URL)
    for key in redis_client.scan_iter("llm_*"):
        redis_client.delete(key)
    redis_client.close()


@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL, future=True)


@pytest.fixture
def db_session(engine):
    """A session whose role/institution GUCs default to the unrestricted
    'bureau_admin' role, for tests that set up fixture data before
    switching to a restricted role to test isolation."""
    Session_ = sessionmaker(bind=engine, future=True)
    session = Session_()
    session.execute(text("SELECT set_config('app.role', 'bureau_admin', false)"))
    session.execute(text("SELECT set_config('app.institution_id', '', false)"))
    session.execute(text("SELECT set_config('app.user_id', '', false)"))
    yield session
    session.rollback()
    session.close()


def session_as(
    engine, role: str, institution_id: str | None = None, user_id: str | None = None
) -> Session:
    Session_ = sessionmaker(bind=engine, future=True)
    session = Session_()
    session.execute(text("SELECT set_config('app.role', :v, false)"), {"v": role})
    session.execute(
        text("SELECT set_config('app.institution_id', :v, false)"),
        {"v": institution_id or ""},
    )
    session.execute(
        text("SELECT set_config('app.user_id', :v, false)"), {"v": user_id or ""}
    )
    return session


@dataclass
class FakeClock:
    """Test-only `Clock` (see app.clock.Clock) that can be advanced
    without waiting on wall-clock time. Lives strictly in this tests
    package — production code only ever gets `app.clock.RealClock`."""

    _offset: timedelta = field(default_factory=timedelta)

    def now(self) -> datetime:
        return datetime.now(UTC) + self._offset

    def advance(self, *, days: int = 0, seconds: int = 0) -> datetime:
        self._offset += timedelta(days=days, seconds=seconds)
        return self.now()

    def reset(self) -> datetime:
        self._offset = timedelta()
        return self.now()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()
