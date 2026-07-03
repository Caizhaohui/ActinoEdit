"""Backward-compatible re-exports; BGC logic lives in actinoedit.core.bgc."""

from actinoedit.core.bgc import (
    annotate_guides_with_bgc,
    find_bgc_for_position,
    find_nearest_bgc,
    get_bgc_summary,
    load_bgc_regions,
)

__all__ = [
    "annotate_guides_with_bgc",
    "find_bgc_for_position",
    "find_nearest_bgc",
    "get_bgc_summary",
    "load_bgc_regions",
]
