"""Alembic migration helpers for ActinoEdit database versioning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from actinoedit.db.session import resolve_db_url

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALEMBIC_INI = _REPO_ROOT / "alembic.ini"


def _alembic_config(db_url: str | None = None) -> Config:
    """Build Alembic config bound to the resolved database URL."""
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", resolve_db_url(db_url))
    return cfg


def upgrade_database(db_url: str | None = None, revision: str = "head") -> str:
    """Apply Alembic migrations up to ``revision`` (default: head).

    Returns the revision id after upgrade.
    """
    resolved = resolve_db_url(db_url)
    cfg = _alembic_config(resolved)
    status_before = get_database_status(resolved)
    if status_before["current_revision"] is None:
        engine = create_engine(resolved, connect_args={"check_same_thread": False})
        try:
            with engine.connect() as connection:
                inspector = __import__("sqlalchemy").inspect(connection)
                if inspector.has_table("projects") and not inspector.has_table("alembic_version"):
                    command.stamp(cfg, "002")
        finally:
            engine.dispose()

    command.upgrade(cfg, revision)
    status = get_database_status(resolved)
    return status["current_revision"] or revision


def get_database_status(db_url: str | None = None) -> dict[str, Any]:
    """Return migration status for the configured database."""
    resolved = resolve_db_url(db_url)
    cfg = _alembic_config(resolved)
    script = ScriptDirectory.from_config(cfg)
    head_revision = script.get_current_head()

    engine = create_engine(resolved, connect_args={"check_same_thread": False})
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current = context.get_current_revision()
    finally:
        engine.dispose()

    pending = current != head_revision
    return {
        "db_url": resolved,
        "current_revision": current,
        "head_revision": head_revision,
        "pending_migrations": pending,
        "up_to_date": not pending and current is not None,
    }
