import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://fdr:fdr@localhost:5434/fdr"
)


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


def session_as(engine, role: str, institution_id: str | None = None, user_id: str | None = None) -> Session:
    Session_ = sessionmaker(bind=engine, future=True)
    session = Session_()
    session.execute(text("SELECT set_config('app.role', :v, false)"), {"v": role})
    session.execute(text("SELECT set_config('app.institution_id', :v, false)"), {"v": institution_id or ""})
    session.execute(text("SELECT set_config('app.user_id', :v, false)"), {"v": user_id or ""})
    return session
