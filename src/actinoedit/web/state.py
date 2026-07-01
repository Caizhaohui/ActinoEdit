"""Web application state management for ActinoEdit."""

from __future__ import annotations

from dataclasses import dataclass, field

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
)
from actinoedit.core.pipeline import DesignResult


@dataclass
class WebState:
    """Mutable application state for the web UI.

    Stores input parameters, design results, and UI state.
    """

    # Input files
    genome_path: str = ""
    annotation_path: str = ""
    annotation_format: str = "gff"  # "gff" or "gbk"

    # Organism profile
    profile_name: str = "streptomyces"

    # CRISPR parameters
    pam: str = "NGG"
    spacer_length: int = 20
    max_mismatches: int = 3

    # Target
    target: str = ""

    # Optional BGC for actinomycete context
    bgc_path: str = ""

    # Design results
    result: DesignResult | None = None
    is_running: bool = False
    error_message: str = ""
    progress_messages: list[str] = field(default_factory=list)

    # Table filtering
    filter_recommendation: str = "all"
    filter_max_offtargets: int = -1  # -1 means no filter

    def reset(self) -> None:
        """Reset state for a new design run."""
        self.result = None
        self.is_running = False
        self.error_message = ""
        self.progress_messages = []

    def add_progress(self, message: str) -> None:
        """Add a progress message."""
        self.progress_messages.append(message)

    @property
    def has_result(self) -> bool:
        """Check if a design result is available."""
        return self.result is not None

    @property
    def guide_count(self) -> int:
        """Get number of guide candidates."""
        if self.result is None:
            return 0
        return len(self.result.guide_candidates)

    @property
    def filtered_guides(self) -> list[tuple[GuideCandidate, GuideScore | None, int]]:
        """Get filtered guide candidates with scores and off-target counts.

        Returns:
            List of (guide, score, off_target_count) tuples.
        """
        if self.result is None:
            return []

        items: list[tuple[GuideCandidate, GuideScore | None, int]] = []
        score_map = {s.guide_id: s for s in self.result.guide_scores}

        for guide in self.result.guide_candidates:
            score = score_map.get(guide.guide_id)
            hits = self.result.off_target_hits.get(guide.guide_id, [])
            ot_count = len(hits)

            # Apply filters
            if (
                self.filter_recommendation != "all"
                and score is not None
                and score.recommendation != self.filter_recommendation
            ):
                continue
            if self.filter_max_offtargets >= 0 and ot_count > self.filter_max_offtargets:
                continue

            items.append((guide, score, ot_count))

        return items
