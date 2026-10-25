from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


import json


def set_app_context(
    session: Session,
    role: str = "",
    institution_id: str | None = None,
    user_id: str | None = None,
    role_scope: dict | list | str | None = None,
    assurance: dict | str | None = None,
    is_local: bool = True,
) -> None:
    """Sets the Postgres session GUCs that RLS policies key on.

    Uses set_config(..., true) by default (SET LOCAL semantics, scoped to
    the current transaction). When is_local=False, sets session-level GUCs.
    """
    session.execute(
        text("SELECT set_config('app.role', :role, :local)"),
        {"role": str(role), "local": is_local},
    )
    session.execute(
        text("SELECT set_config('app.institution_id', :iid, :local)"),
        {"iid": str(institution_id) if institution_id else "", "local": is_local},
    )
    session.execute(
        text("SELECT set_config('app.user_id', :uid, :local)"),
        {"uid": str(user_id) if user_id else "", "local": is_local},
    )
    scope_val = (
        json.dumps(role_scope)
        if isinstance(role_scope, (dict, list))
        else (str(role_scope) if role_scope else "")
    )
    session.execute(
        text("SELECT set_config('app.role_scope', :scope, :local)"),
        {"scope": scope_val, "local": is_local},
    )
    assurance_val = (
        json.dumps(assurance)
        if isinstance(assurance, dict)
        else (str(assurance) if assurance else "")
    )
    session.execute(
        text("SELECT set_config('app.assurance', :assurance, :local)"),
        {"assurance": assurance_val, "local": is_local},
    )


def get_db():
    """FastAPI dependency yielding a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


get_session = get_db
