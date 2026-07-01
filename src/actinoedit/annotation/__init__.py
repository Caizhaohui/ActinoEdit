"""Annotation modules for gene and BGC analysis."""

from actinoedit.annotation.bgc import (
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
