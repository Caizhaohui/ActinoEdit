"""Database connection and schema initialization using SQLAlchemy.

Full support for SQLite and PostgreSQL (via DATABASE_URL).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from actinoedit.db.config import is_postgres
from actinoedit.db.session import resolve_db_url

DEFAULT_DB_PATH = Path.home() / ".actinoedit" / "actinoedit.db"


def get_engine(db_url: str | None = None, extra_options: dict[str, Any] | None = None) -> Any:
    """Create SQLAlchemy engine based on URL.

    Supports sqlite and postgresql with production options (pooling, ssl etc).
    For postgres, requires psycopg2-binary installed.
    """
    db_url = resolve_db_url(db_url)

    from actinoedit.db.config import get_engine_options
    opts = get_engine_options()
    if extra_options:
        opts.update(extra_options)

    if is_postgres(db_url):
        try:
            import psycopg2  # type: ignore[import-untyped]  # noqa: F401
        except ImportError:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL support. "
                "Install with: pip install psycopg2-binary"
            ) from None
        # Ensure proper dialect
        if not db_url.startswith("postgresql+"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        connect_args = opts.get("connect_args", {})
    else:
        connect_args = {"check_same_thread": False}
        if "connect_args" in opts:
            connect_args.update(opts["connect_args"])

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=opts.get("echo", False),
        pool_size=opts.get("pool_size", 5),
        max_overflow=opts.get("max_overflow", 10),
    )
    return engine


def get_session(db_url: str | None = None, extra_options: dict[str, Any] | None = None) -> Any:
    """Get a sessionmaker bound to engine. Supports production options."""
    engine = get_engine(db_url, extra_options)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_local()


def init_database(engine: Any | None = None, db_url: str | None = None) -> Any:
    """Initialize schema via Alembic migrations (versioned, idempotent).

    Applies all pending migrations up to head. Safe to call multiple times.
    """
    if engine is not None and db_url is None:
        db_url = str(engine.url)

    from actinoedit.db.migrations import upgrade_database

    upgrade_database(db_url)
    return engine if engine is not None else get_engine(db_url)


def test_connection(db_url: str | None = None) -> bool:
    """Test if we can connect to the DB. For Postgres, requires driver and server."""
    engine = get_engine(resolve_db_url(db_url))
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


# For backward compatibility with existing raw sqlite code in some places
# (e.g. older tests), but new code should use SQLAlchemy.
def get_connection(db_path: str | Path | None = None) -> Any:
    """Legacy sqlite3 connection for transitional code. Prefer get_engine/get_session."""

    if db_path is None:
        db_path = DEFAULT_DB_PATH
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
