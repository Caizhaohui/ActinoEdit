"""Shared design input/output types for the ActinoEdit pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from actinoedit.core.models import (
    BGCRegion,
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    TargetRegion,
)


@dataclass
class DesignInput:
    """Input parameters for guide RNA design."""

    genome_path: str
    annotation_path: str
    target: str
    pam: str = "NGG"
    spacer_length: int = 20
    max_mismatches: int = 3
    organism_profile: str | None = None
    output_prefix: str = "results/guides"
    bgc_path: str | None = None
    design_mode: str = "knockout"


@dataclass
class DesignResult:
    """Result of guide RNA design."""

    target_region: TargetRegion | None = None
    guide_candidates: list[GuideCandidate] = field(default_factory=list)
    off_target_hits: dict[str, list[OffTargetHit]] = field(default_factory=dict)
    guide_scores: list[GuideScore] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    bgc_regions: list[BGCRegion] = field(default_factory=list)
    resolved_params: dict[str, Any] = field(default_factory=dict)
    profile_name: str | None = None
    input_file_summary: dict[str, Any] = field(default_factory=dict)
    version: str | None = None
    report_paths: dict[str, str] = field(default_factory=dict)
    cancelled: bool = False

    def set_report_paths_from_files(self, paths: list[str]) -> None:
        """Populate report_paths from generated report file paths."""
        for path in paths:
            lower = path.lower()
            if lower.endswith(".csv"):
                self.report_paths["csv"] = path
            elif lower.endswith(".xlsx"):
                self.report_paths["xlsx"] = path
            elif lower.endswith(".html"):
                self.report_paths["html"] = path
        self.output_files = list(paths)
