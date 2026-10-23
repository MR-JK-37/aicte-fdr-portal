from datetime import UTC, datetime

from app import sim_clock


def test_now_defaults_close_to_real_time(db_session):
    before = datetime.now(UTC)
    sim_now = sim_clock.now(db_session)
    after = datetime.now(UTC)
    assert before <= sim_now <= after


def test_advance_shifts_now_forward(db_session):
    base = sim_clock.now(db_session)
    advanced = sim_clock.advance(db_session, days=300)
    assert (advanced - base).days >= 299  # allow for sub-second test execution drift


def test_advance_is_cumulative(db_session):
    sim_clock.advance(db_session, days=10)
    second = sim_clock.advance(db_session, days=5)
    base = datetime.now(UTC)
    assert (second - base).days >= 14


def test_reset_returns_to_real_time(db_session):
    sim_clock.advance(db_session, days=300)
    reset_now = sim_clock.reset(db_session)
    real_now = datetime.now(UTC)
    assert abs((reset_now - real_now).total_seconds()) < 5
