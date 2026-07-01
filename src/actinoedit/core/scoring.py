"""Guide RNA scoring module for ActinoEdit.

This module provides functions for scoring guide RNA candidates based on
specificity, GC content, position, and homopolymer runs.
"""

from __future__ import annotations

from dataclasses import dataclass

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    OrganismProfile,
)
from actinoedit.core.sequence import count_homopolymer_runs


@dataclass
class ScoringWeights:
    """Weights for scoring components.

    Attributes:
        specificity: Weight for specificity score.
        gc: Weight for GC content score.
        position: Weight for position score.
        homopolymer: Weight for homopolymer penalty.
    """

    specificity: float = 0.4
    gc: float = 0.2
    position: float = 0.2
    homopolymer: float = 0.2

    def normalize(self) -> None:
        """Normalize weights to sum to 1."""
        total = self.specificity + self.gc + self.position + self.homopolymer
        if total > 0:
            self.specificity /= total
            self.gc /= total
            self.position /= total
            self.homopolymer /= total


def score_guide(
    guide: GuideCandidate,
    off_target_hits: list[OffTargetHit] | None = None,
    profile: OrganismProfile | None = None,
    weights: ScoringWeights | None = None,
    target_cds_length: int | None = None,
    design_mode: str = "knockout",
) -> GuideScore:
    """Score a guide RNA candidate.

    Args:
        guide: GuideCandidate object.
        off_target_hits: List of off-target hits for this guide.
        profile: Organism profile for GC preferences.
        weights: Scoring weights.
        target_cds_length: Length of target CDS for position scoring.
        design_mode: "knockout" (prefer early CDS) or "crispri" (prefer near TSS/ATG for repression).

    Returns:
        GuideScore object.
    """
    if weights is None:
        weights = ScoringWeights()
        weights.normalize()

    # Calculate individual scores
    specificity = _calculate_specificity_score(guide, off_target_hits)
    gc_score = _calculate_gc_score(guide, profile)
    position_score = _calculate_position_score(guide, target_cds_length, design_mode=design_mode)
    homopolymer_penalty = _calculate_homopolymer_penalty(guide)

    # Calculate final score
    final_score = (
        weights.specificity * specificity
        + weights.gc * gc_score
        + weights.position * position_score
        - weights.homopolymer * homopolymer_penalty
    )

    # Ensure final score is between 0 and 1
    final_score = max(0.0, min(1.0, final_score))

    # Determine recommendation
    recommendation = _get_recommendation(final_score)

    return GuideScore(
        guide_id=guide.guide_id,
        specificity_score=specificity,
        gc_score=gc_score,
        position_score=position_score,
        homopolymer_penalty=homopolymer_penalty,
        final_score=final_score,
        recommendation=recommendation,
    )


def _calculate_specificity_score(
    guide: GuideCandidate,
    off_target_hits: list[OffTargetHit] | None = None,
) -> float:
    """Calculate specificity score based on off-target hits.

    Args:
        guide: GuideCandidate object.
        off_target_hits: List of off-target hits.

    Returns:
        Specificity score (0-1, higher is better).
    """
    if off_target_hits is None or len(off_target_hits) == 0:
        return 1.0

    # Count hits by mismatch
    hit_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for hit in off_target_hits:
        if hit.mismatch_count <= 3:
            hit_counts[hit.mismatch_count] += 1

    # Penalize based on hit counts
    # More hits = lower score
    penalty = 0.0
    penalty += hit_counts[0] * 0.5  # Exact matches are very bad
    penalty += hit_counts[1] * 0.2  # 1 mismatch is bad
    penalty += hit_counts[2] * 0.05  # 2 mismatches are okay
    penalty += hit_counts[3] * 0.01  # 3 mismatches are fine

    # Convert to score (0-1)
    specificity = max(0.0, 1.0 - penalty)
    return specificity


def _calculate_gc_score(
    guide: GuideCandidate,
    profile: OrganismProfile | None = None,
) -> float:
    """Calculate GC content score.

    Args:
        guide: GuideCandidate object.
        profile: Organism profile for GC preferences.

    Returns:
        GC score (0-1, higher is better).
    """
    gc = guide.gc_content

    if profile is not None:
        # Use profile-specific GC range
        gc_min = profile.recommended_gc_min / 100
        gc_max = profile.recommended_gc_max / 100
    else:
        # Default GC range
        gc_min = 0.4
        gc_max = 0.8

    # Calculate score based on distance from optimal range
    if gc_min <= gc <= gc_max:
        # Within range - score based on distance from center
        center = (gc_min + gc_max) / 2
        distance = abs(gc - center) / (gc_max - gc_min)
        return 1.0 - distance * 0.5
    else:
        # Outside range - penalize
        if gc < gc_min:
            distance = (gc_min - gc) / gc_min
        else:
            distance = (gc - gc_max) / (1.0 - gc_max)
        return max(0.0, 1.0 - distance)


def _calculate_position_score(
    guide: GuideCandidate,
    target_cds_length: int | None = None,
    design_mode: str = "knockout",
) -> float:
    """Calculate position score.

    Knockout: prefer early CDS (first third).
    CRISPRi: prefer near 5' end / promoter proximal region (early in target for repression).

    Args:
        guide: GuideCandidate object.
        target_cds_length: Length of target CDS.
        design_mode: "knockout" or "crispri"

    Returns:
        Position score (0-1, higher is better).
    """
    if target_cds_length is None or target_cds_length == 0:
        return 0.6 if design_mode == "crispri" else 0.5

    # Simplified relative position (0 at start of region, 1 at end)
    # In real usage the caller would pass better relative info via target_cds_length + guide position
    # Here we use a heuristic based on cut_site within the target region length
    rel_pos = 0.5
    try:
        if target_cds_length > 0:
            # Assume the "target" start maps to 0; use guide start as proxy
            rel_pos = min(1.0, max(0.0, (guide.start % (target_cds_length or 300)) / (target_cds_length or 300)))
    except Exception:
        rel_pos = 0.5

    if design_mode == "crispri":
        # For CRISPRi, higher score closer to 5' end (small rel_pos)
        return max(0.1, 1.0 - rel_pos * 0.7)
    else:
        # Knockout: prefer first third
        if rel_pos < 0.33:
            return 0.95
        elif rel_pos < 0.66:
            return 0.6
        return 0.3


def _calculate_homopolymer_penalty(guide: GuideCandidate) -> float:
    """Calculate homopolymer penalty.

    Args:
        guide: GuideCandidate object.

    Returns:
        Homopolymer penalty (0-1, lower is better).
    """
    runs = count_homopolymer_runs(guide.spacer, min_length=4)

    if not runs:
        return 0.0

    # Calculate penalty based on number and length of runs
    penalty = 0.0
    for _, _, length in runs:
        # Longer runs = higher penalty
        penalty += (length - 3) * 0.2

    return min(1.0, penalty)


def _get_recommendation(score: float) -> str:
    """Get recommendation based on score.

    Args:
        score: Final score (0-1).

    Returns:
        Recommendation string.
    """
    if score >= 0.8:
        return "excellent"
    elif score >= 0.6:
        return "good"
    elif score >= 0.4:
        return "caution"
    else:
        return "avoid"


def score_guides(
    guides: list[GuideCandidate],
    off_target_hits: dict[str, list[OffTargetHit]] | None = None,
    profile: OrganismProfile | None = None,
    weights: ScoringWeights | None = None,
) -> list[GuideScore]:
    """Score multiple guide RNA candidates.

    Args:
        guides: List of GuideCandidate objects.
        off_target_hits: Dictionary mapping guide_id to off-target hits.
        profile: Organism profile.
        weights: Scoring weights.

    Returns:
        List of GuideScore objects.
    """
    scores: list[GuideScore] = []

    for guide in guides:
        hits = None
        if off_target_hits is not None:
            hits = off_target_hits.get(guide.guide_id)

        score = score_guide(guide, hits, profile, weights)
        scores.append(score)

    return scores


def rank_guides(
    guides: list[GuideCandidate],
    scores: list[GuideScore],
) -> list[tuple[GuideCandidate, GuideScore]]:
    """Rank guides by score.

    Args:
        guides: List of GuideCandidate objects.
        scores: List of GuideScore objects.

    Returns:
        List of (GuideCandidate, GuideScore) tuples sorted by score.
    """
    # Create mapping
    score_map = {s.guide_id: s for s in scores}

    # Pair guides with scores
    paired = []
    for guide in guides:
        score = score_map.get(guide.guide_id)
        if score is not None:
            paired.append((guide, score))

    # Sort by final score (descending)
    paired.sort(key=lambda x: x[1].final_score, reverse=True)

    return paired
