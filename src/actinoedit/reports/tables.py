"""Table generation for ActinoEdit reports."""

from __future__ import annotations

import pandas as pd

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
    OffTargetHit,
)


def guides_to_dataframe(
    guides: list[GuideCandidate],
    scores: list[GuideScore] | None = None,
    off_target_hits: dict[str, list[OffTargetHit]] | None = None,
) -> pd.DataFrame:
    """Convert guide candidates to a pandas DataFrame.

    Args:
        guides: List of GuideCandidate objects.
        scores: Optional list of GuideScore objects.
        off_target_hits: Optional dictionary of off-target hits.

    Returns:
        pandas DataFrame with guide information.
    """
    rows = []

    # Create score lookup
    score_lookup = {}
    if scores:
        score_lookup = {s.guide_id: s for s in scores}

    for guide in guides:
        row = {
            "guide_id": guide.guide_id,
            "target_label": guide.target_label or "",
            "contig": guide.contig,
            "start": guide.start,
            "end": guide.end,
            "strand": guide.strand,
            "spacer": guide.spacer,
            "pam": guide.pam,
            "pam_start": guide.pam_start,
            "pam_end": guide.pam_end,
            "cut_site": guide.cut_site,
            "gc_content": guide.gc_content,
        }

        # Add score information
        score = score_lookup.get(guide.guide_id)
        if score:
            row["specificity_score"] = score.specificity_score
            row["gc_score"] = score.gc_score
            row["position_score"] = score.position_score
            row["homopolymer_penalty"] = score.homopolymer_penalty
            row["final_score"] = score.final_score
            row["recommendation"] = score.recommendation

        # Add off-target counts
        if off_target_hits:
            hits = off_target_hits.get(guide.guide_id, [])
            row["off_target_0mm"] = sum(1 for h in hits if h.mismatch_count == 0)
            row["off_target_1mm"] = sum(1 for h in hits if h.mismatch_count == 1)
            row["off_target_2mm"] = sum(1 for h in hits if h.mismatch_count == 2)
            row["off_target_3mm"] = sum(1 for h in hits if h.mismatch_count == 3)

        # BGC context (optional)
        row["bgc_id"] = guide.bgc_id or ""
        row["bgc_type"] = guide.bgc_type or ""
        row["bgc_context"] = guide.bgc_context or ""

        rows.append(row)

    return pd.DataFrame(rows)


def offtargets_to_dataframe(
    off_target_hits: dict[str, list[OffTargetHit]],
) -> pd.DataFrame:
    """Convert off-target hits to a pandas DataFrame.

    Args:
        off_target_hits: Dictionary mapping guide_id to off-target hits.

    Returns:
        pandas DataFrame with off-target information.
    """
    rows = []

    for guide_id, hits in off_target_hits.items():
        for hit in hits:
            rows.append({
                "guide_id": guide_id,
                "contig": hit.contig,
                "start": hit.start,
                "end": hit.end,
                "strand": hit.strand,
                "sequence": hit.sequence,
                "mismatch_count": hit.mismatch_count,
                "mismatch_positions": ",".join(map(str, hit.mismatch_positions)),
                "nearby_gene": hit.nearby_gene or "",
            })

    return pd.DataFrame(rows)


