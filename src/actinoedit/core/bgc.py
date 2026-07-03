"""BGC (Biosynthetic Gene Cluster) annotation for ActinoEdit.

Supports actinomycete secondary metabolite cluster context for guide design.
Parses simple BED/TSV region files or basic antiSMASH outputs.

This module is optional and activated via organism profile
(enable_bgc_annotation) or explicit --bgc input.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from actinoedit.core.models import BGCRegion, GuideCandidate


def load_bgc_regions(path: str | Path) -> list[BGCRegion]:
    """Load BGC regions from a file.

    Supported formats (auto-detected):
    - Simple TSV/BED (tab or whitespace separated):
        contig<TAB>start<TAB>end<TAB>bgc_id[<TAB>bgc_type[<TAB>product]]
      Comments start with #. 1-based inclusive coordinates.

    Args:
        path: Path to BGC regions file.

    Returns:
        List of BGCRegion objects (sorted by contig then start).

    Raises:
        FileNotFoundError, ValueError on bad data.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"BGC file not found: {path}")

    regions: list[BGCRegion] = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t") if "\t" in line else line.split()
            if len(parts) < 4:
                continue
            try:
                contig = parts[0]
                start = int(parts[1])
                end = int(parts[2])
                bgc_id = parts[3]
                bgc_type = parts[4] if len(parts) > 4 else None
                product = parts[5] if len(parts) > 5 else None
                regions.append(
                    BGCRegion(
                        contig=contig,
                        start=start,
                        end=end,
                        bgc_id=bgc_id,
                        bgc_type=bgc_type,
                        product=product,
                    )
                )
            except (ValueError, IndexError):
                continue
    regions.sort(key=lambda r: (r.contig, r.start))
    return regions


def find_bgc_for_position(
    contig: str,
    position: int,
    regions: list[BGCRegion],
) -> BGCRegion | None:
    """Return the BGC that contains the given 1-based position, if any."""
    for r in regions:
        if r.contig == contig and r.contains(position):
            return r
    return None


def find_nearest_bgc(
    contig: str,
    position: int,
    regions: list[BGCRegion],
    max_distance: int = 10000,
) -> tuple[BGCRegion | None, int]:
    """Find nearest BGC within max_distance bp."""
    best: BGCRegion | None = None
    best_dist = max_distance + 1

    for r in regions:
        if r.contig != contig:
            continue
        dist = r.distance_to(position)
        if dist <= max_distance and dist < best_dist:
            best = r
            best_dist = dist

    if best is None:
        return None, -1
    return best, best_dist


def annotate_guides_with_bgc(
    guides: list[GuideCandidate],
    bgc_regions: list[BGCRegion],
    near_threshold: int = 10000,
) -> list[GuideCandidate]:
    """Return guides annotated with BGC context (does not mutate inputs)."""
    annotated: list[GuideCandidate] = []

    for guide in guides:
        pos = guide.cut_site or ((guide.start + guide.end) // 2)

        inside = find_bgc_for_position(guide.contig, pos, bgc_regions)
        if inside:
            context = f"inside:{inside.bgc_type or 'BGC'}"
            annotated.append(
                replace(
                    guide,
                    bgc_id=inside.bgc_id,
                    bgc_type=inside.bgc_type,
                    bgc_context=context,
                )
            )
            continue

        nearest, dist = find_nearest_bgc(
            guide.contig, pos, bgc_regions, max_distance=near_threshold
        )
        if nearest:
            direction = "upstream" if pos < nearest.start else "downstream"
            dist_kb = dist / 1000.0
            context = (
                f"near:{nearest.bgc_type or 'BGC'} "
                f"({direction} {dist_kb:.1f}kb)"
            )
            annotated.append(
                replace(
                    guide,
                    bgc_id=nearest.bgc_id,
                    bgc_type=nearest.bgc_type,
                    bgc_context=context,
                )
            )
        else:
            annotated.append(guide)

    return annotated


def annotate_bgc_context(
    guides: list[GuideCandidate],
    bgc_path: str | None,
    *,
    profile_enable_bgc: bool = False,
) -> tuple[list[GuideCandidate], list[BGCRegion], list[str]]:
    """Load BGC regions (if configured) and annotate guides.

    Returns:
        (annotated_guides, bgc_regions, warnings)
    """
    warnings: list[str] = []
    if not bgc_path and not profile_enable_bgc:
        return guides, [], warnings

    if not bgc_path:
        warnings.append("BGC annotation requested but no regions file provided")
        return guides, [], warnings

    try:
        bgc_regions = load_bgc_regions(bgc_path)
    except Exception as exc:
        warnings.append(f"BGC annotation skipped: {exc}")
        return guides, [], warnings

    if not bgc_regions:
        warnings.append("BGC annotation requested but no regions loaded")
        return guides, [], warnings

    annotated = annotate_guides_with_bgc(guides, bgc_regions)
    return annotated, bgc_regions, warnings


def get_bgc_summary(guides: list[GuideCandidate]) -> dict[str, int]:
    """Return quick stats: number of guides per BGC (or 'none')."""
    counts: dict[str, int] = {}
    for g in guides:
        key = g.bgc_id or "none"
        counts[key] = counts.get(key, 0) + 1
    return counts
