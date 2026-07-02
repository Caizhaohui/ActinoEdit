"""Database configuration abstraction for ActinoEdit.

Supports:
- Local: SQLite (default, file based)
- Lab: PostgreSQL (via DATABASE_URL or config)

For full Postgres support, future migration to SQLAlchemy/SQLModel + Alembic is recommended.
Current prototype uses raw sqlite3 for local.

Config via:
- env: ACTINOEDIT_DB_URL (e.g. sqlite:////path/to/db or postgresql://user:pass@host/db)
- or yaml files (future)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import yaml

DEFAULT_DB_PATH = Path.home() / ".actinoedit" / "actinoedit.db"


def get_db_url(config_path: str | Path | None = None) -> str:
    """Get database URL from env or config.

    Priority:
    1. ACTINOEDIT_DB_URL env var
    2. config file (local.yaml or lab_server.yaml based on env)
    3. default sqlite
    """
    env_url = os.environ.get("ACTINOEDIT_DB_URL")
    if env_url:
        return env_url

    if config_path:
        cfg_path = Path(config_path)
        if cfg_path.exists():
            with open(cfg_path) as f:
                cfg = cast(dict[str, Any], yaml.safe_load(f) or {})
            db_cfg = cfg.get("database", {})
            url = db_cfg.get("url")
            if url:
                return str(url)

    # default local sqlite
    return f"sqlite:///{DEFAULT_DB_PATH}"


def is_postgres(url: str) -> bool:
    return url.startswith("postgresql") or url.startswith("postgres")


def get_sqlite_path(url: str) -> Path | None:
    if url.startswith("sqlite:///"):
        path_str = url.replace("sqlite:///", "", 1)
        if path_str.startswith("/"):
            return Path(path_str)
        return Path(path_str)
    return None


def load_config(mode: str = "local") -> dict[str, Any]:
    """Load yaml config. mode: 'local' or 'lab'."""
    cfg_name = "lab_server.yaml" if mode == "lab" else "local.yaml"
    # Look in current dir or ~/.actinoedit/
    candidates = [
        Path.cwd() / cfg_name,
        Path.home() / ".actinoedit" / cfg_name,
    ]
    for p in candidates:
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f) or {}
    return {}


def get_engine_options(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get SQLAlchemy engine options from config or defaults.
    Supports pool_size, echo, connect_args (for ssl etc).
    """
    if config is None:
        config = load_config()
    db_cfg = config.get("database", {}) if isinstance(config, dict) else {}
    opts: dict[str, Any] = {
        "echo": db_cfg.get("echo", False),
        "pool_size": db_cfg.get("pool_size", 5),
        "max_overflow": db_cfg.get("max_overflow", 10),
    }
    connect_args = db_cfg.get("connect_args", {})
    if connect_args:
        opts["connect_args"] = connect_args
    return opts
