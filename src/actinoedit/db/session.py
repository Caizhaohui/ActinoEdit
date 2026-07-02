"""Database session scoping for ActinoEdit.

Supports explicit db_url injection via context manager or environment variable.
Used by CRUD layer and tests for isolated SQLite databases.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_db_url_override: ContextVar[str | None] = ContextVar("actinoedit_db_url", default=None)


def get_db_url_override() -> str | None:
    """Return the active db_url override, if any."""
    return _db_url_override.get()


@contextmanager
def use_db_url(db_url: str) -> Iterator[None]:
    """Temporarily route all DB operations to the given URL."""
    token = _db_url_override.set(db_url)
    try:
        yield
    finally:
        _db_url_override.reset(token)


def resolve_db_url(db_url: str | None = None) -> str:
    """Resolve db_url from explicit arg, context override, or config."""
    if db_url is not None:
        return db_url
    override = get_db_url_override()
    if override is not None:
        return override
    from actinoedit.db.config import get_db_url

    return get_db_url()


def open_session(db_url: str | None = None, session: Any | None = None) -> tuple[Any, bool]:
    """Return (session, should_close).

    If session is provided, returns it unchanged with should_close=False.
    Otherwise creates a new session bound to the resolved db_url.
    """
    if session is not None:
        return session, False

    from sqlalchemy.orm import sessionmaker

    from actinoedit.db.database import get_engine

    resolved = resolve_db_url(db_url)
    engine = get_engine(resolved)
    session_local = sessionmaker(bind=engine)
    return session_local(), True
