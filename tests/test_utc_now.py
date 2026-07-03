"""Ensure database timestamps avoid deprecated datetime.utcnow."""

from __future__ import annotations

from datetime import timezone

from actinoedit.db.timeutil import utc_now


def test_utc_now_is_timezone_aware() -> None:
    now = utc_now()
    assert now.tzinfo == timezone.utc
