"""Verify DB tests do not leak into the default user database."""

from __future__ import annotations

from pathlib import Path

import pytest

from actinoedit.db import list_organisms, save_organism
from actinoedit.db.database import get_engine, init_database
from actinoedit.db.session import use_db_url


def test_db_isolation_from_default(db_url: str) -> None:
    """Writes in isolated DB must not appear in another isolated DB."""
    other_url = db_url.replace("actinoedit_test.db", "actinoedit_other.db")
    init_database(get_engine(other_url))

    with use_db_url(db_url):
        save_organism("isolation_marker_org")

    with use_db_url(other_url):
        orgs = list_organisms()
        assert not any(o["name"] == "isolation_marker_org" for o in orgs)


def test_db_routing_via_env_only(db_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """CRUD respects ACTINOEDIT_DB_URL without an explicit use_db_url context."""
    monkeypatch.setenv("ACTINOEDIT_DB_URL", db_url)
    marker = "env_only_marker_org"
    save_organism(marker)
    orgs = list_organisms()
    assert any(o["name"] == marker for o in orgs)


def test_db_explicit_db_url_param(isolated_db_url: str) -> None:
    """CRUD db_url parameter routes to the requested database."""
    marker = "explicit_url_marker_org"
    save_organism(marker, db_url=isolated_db_url)
    orgs = list_organisms(db_url=isolated_db_url)
    assert any(o["name"] == marker for o in orgs)


def test_db_does_not_touch_default_path(
    isolated_db_url: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Isolated writes must not create rows in a separate default-path database."""
    default_db = tmp_path / "user_default.db"
    default_url = f"sqlite:///{default_db}"
    init_database(get_engine(default_url))

    monkeypatch.delenv("ACTINOEDIT_DB_URL", raising=False)
    marker = "must_not_leak_to_default"

    with use_db_url(isolated_db_url):
        save_organism(marker)

    default_orgs = list_organisms(db_url=default_url)
    assert not any(o["name"] == marker for o in default_orgs)
