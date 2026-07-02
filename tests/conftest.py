"""Shared pytest fixtures for ActinoEdit."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from actinoedit.db.database import get_engine, init_database
from actinoedit.db.session import use_db_url

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove Rich/ANSI color codes from CLI output."""
    return _ANSI_ESCAPE.sub("", text)


@pytest.fixture
def isolated_db_url(tmp_path: Path) -> str:
    """Create an isolated SQLite database URL for tests."""
    db_file = tmp_path / "actinoedit_test.db"
    url = f"sqlite:///{db_file}"
    init_database(get_engine(url))
    return url


@pytest.fixture
def db_url(isolated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> str:
    """Route all DB operations to a temporary SQLite file via env + context."""
    monkeypatch.setenv("ACTINOEDIT_DB_URL", isolated_db_url)
    return isolated_db_url


@pytest.fixture
def db_context(db_url: str):
    """Context manager fixture wrapping use_db_url."""
    with use_db_url(db_url):
        yield db_url
