"""Web application state management for ActinoEdit."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
)
from actinoedit.core.pipeline import DesignResult

TaskStatus = Literal[
    "idle",
    "running",
    "cancelling",
    "completed",
    "failed",
    "cancelled",
    "timeout",
]


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

    # Design mode
    design_mode: str = "knockout"  # knockout or crispri

    # Optional BGC for actinomycete context
    bgc_path: str = ""

    # Export / output preferences
    export_output_dir: str = "results/db_exports"
    report_output_dir: str = "results/web_autosave"

    # Temp uploads tracked for cleanup
    temp_upload_paths: list[str] = field(default_factory=list)

    # Design results
    result: DesignResult | None = None
    is_running: bool = False
    task_status: TaskStatus = "idle"
    cancel_requested: bool = False
    error_message: str = ""
    status_message: str = ""
    progress_messages: list[str] = field(default_factory=list)

    # Upload feedback
    genome_upload_status: str = ""
    annotation_upload_status: str = ""

    # Table filtering
    filter_recommendation: str = "all"
    filter_max_offtargets: int = -1  # -1 means no filter

    def reset(self) -> None:
        """Reset state for a new design run."""
        self.result = None
        self.is_running = False
        self.task_status = "idle"
        self.cancel_requested = False
        self.error_message = ""
        self.status_message = ""
        self.progress_messages = []

    def register_temp_upload(self, path: str) -> None:
        """Track an uploaded temp file and remove any previously tracked uploads."""
        self.cleanup_temp_uploads()
        self.temp_upload_paths = [path]

    def cleanup_temp_uploads(self) -> None:
        """Remove tracked temporary upload files."""
        for path in self.temp_upload_paths:
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
            except OSError:
                continue
        self.temp_upload_paths = []

    def request_cancel(self) -> None:
        """Request cancellation of the active background design task."""
        self.cancel_requested = True
        if self.is_running:
            self.task_status = "cancelling"
            self.status_message = "Cancellation requested; waiting for pipeline to stop..."

    def add_progress(self, message: str) -> None:
        """Add a progress message."""
        self.progress_messages.append(message)

    @property
    def has_result(self) -> bool:
        """Check if a design result is available."""
        return self.result is not None

    @property
    def has_guides(self) -> bool:
        """Check if the current result contains guide candidates."""
        return self.result is not None and bool(self.result.guide_candidates)

    @property
    def show_task_status(self) -> bool:
        """Whether the task status panel should be visible."""
        return self.task_status != "idle"

    @property
    def show_progress(self) -> bool:
        """Whether the progress panel should be visible."""
        return self.is_running or self.task_status == "cancelling"

    @property
    def show_no_guides_message(self) -> bool:
        """Whether to show the empty-result guidance panel."""
        return self.task_status == "completed" and not self.has_guides

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
