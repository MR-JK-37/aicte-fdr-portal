"""Tests for the DB-leased scheduler lock primitive
(app.outbox.scheduler). Pure Postgres advisory-lock behaviour — no
dependency on the outbox table or any migration, so nothing here is
blocked on the parallel workstream's migration landing.
"""

from app.outbox.scheduler import (
    SCHEDULER_ADVISORY_LOCK_KEY,
    release_scheduler_lease,
    try_acquire_scheduler_lease,
)

# Use a distinct key in tests so running worker containers on the dev database
# do not cause spurious lock contention failures.
TEST_LOCK_KEY = 0x46445259


def test_second_session_cannot_acquire_while_first_holds_lease(engine):
    from sqlalchemy.orm import sessionmaker

    Session_ = sessionmaker(bind=engine, future=True)
    holder = Session_()
    contender = Session_()
    try:
        assert try_acquire_scheduler_lease(holder, key=TEST_LOCK_KEY) is True
        assert try_acquire_scheduler_lease(contender, key=TEST_LOCK_KEY) is False
    finally:
        release_scheduler_lease(holder, key=TEST_LOCK_KEY)
        holder.close()
        contender.close()


def test_lease_becomes_available_again_after_release(engine):
    from sqlalchemy.orm import sessionmaker

    Session_ = sessionmaker(bind=engine, future=True)
    first = Session_()
    second = Session_()
    try:
        assert try_acquire_scheduler_lease(first, key=TEST_LOCK_KEY) is True
        release_scheduler_lease(first, key=TEST_LOCK_KEY)
        assert try_acquire_scheduler_lease(second, key=TEST_LOCK_KEY) is True
    finally:
        release_scheduler_lease(second, key=TEST_LOCK_KEY)
        first.close()
        second.close()


def test_lease_releases_automatically_when_connection_closes():
    """A pooled engine's `session.close()` returns the connection to the
    pool without actually closing the underlying TCP connection — so a
    later `Session()` from the same pooled `engine` fixture can get
    back that exact same (still-locked) physical connection, which
    would make this test pass for the wrong reason. A dedicated
    `NullPool` engine (no reuse) is what actually exercises "the
    physical connection really went away" — the real production case
    (app.outbox.scheduler.run_forever) this test models: a crashed
    scheduler process, not a session returned to a pool.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import NullPool

    from tests.conftest import TEST_DATABASE_URL

    nullpool_engine = create_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)
    Session_ = sessionmaker(bind=nullpool_engine, future=True)

    crashed = Session_()
    assert try_acquire_scheduler_lease(crashed, key=TEST_LOCK_KEY) is True
    crashed.close()  # NullPool: this really closes the physical connection

    survivor = Session_()
    try:
        assert try_acquire_scheduler_lease(survivor, key=TEST_LOCK_KEY) is True
    finally:
        release_scheduler_lease(survivor, key=TEST_LOCK_KEY)
        survivor.close()
        nullpool_engine.dispose()


def test_lock_key_is_a_fixed_constant():
    assert isinstance(SCHEDULER_ADVISORY_LOCK_KEY, int)
