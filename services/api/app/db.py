from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def set_app_context(session: Session, role: str, institution_id: str | None, user_id: str | None = None) -> None:
    """Sets the Postgres session GUCs that RLS policies key on.

    Uses set_config(..., true) i.e. SET LOCAL semantics: scoped to the
    current transaction. Callers must set this inside the same transaction
    as the queries it is meant to protect.
    """
    session.execute(text("SELECT set_config('app.role', :role, true)"), {"role": role})
    session.execute(
        text("SELECT set_config('app.institution_id', :iid, true)"),
        {"iid": institution_id or ""},
    )
    session.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": user_id or ""})
