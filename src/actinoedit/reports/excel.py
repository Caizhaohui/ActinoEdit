"""Excel report generation for ActinoEdit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
    OffTargetHit,
)
from actinoedit.reports.tables import (
    guides_to_dataframe,
    offtargets_to_dataframe,
)


def write_excel_report(
    guides: list[GuideCandidate],
    output_path: str | Path,
    scores: list[GuideScore] | None = None,
    off_target_hits: dict[str, list[OffTargetHit]] | None = None,
    parameters: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> None:
    """Write an Excel report with multiple sheets.

    Args:
        guides: List of GuideCandidate objects.
        output_path: Path to output Excel file.
        scores: Optional list of GuideScore objects.
        off_target_hits: Optional dictionary of off-target hits.
        parameters: Optional dictionary of design parameters.
        warnings: Optional list of warning messages.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
        # Sheet 1: Guide candidates
        guides_df = guides_to_dataframe(guides, scores, off_target_hits)
        guides_df.to_excel(writer, sheet_name="guide_candidates", index=False)

        # Sheet 2: Off-targets
        if off_target_hits:
            offtargets_df = offtargets_to_dataframe(off_target_hits)
            offtargets_df.to_excel(writer, sheet_name="off_targets", index=False)

        # Sheet 3: Parameters
        if parameters:
            params_df = pd.DataFrame(
                list(parameters.items()),
                columns=["Parameter", "Value"],
            )
            params_df.to_excel(writer, sheet_name="parameters", index=False)

        # Sheet 4: Warnings
        if warnings:
            warnings_df = pd.DataFrame(warnings, columns=["Warning"])
            warnings_df.to_excel(writer, sheet_name="warnings", index=False)

        # Sheet 5: CRISPRi details (if applicable)
        crispri_guides = [g for g in guides if g.crispri_region_type]
        if crispri_guides:
            crispri_data = []
            for g in crispri_guides:
                crispri_data.append({
                    "guide_id": g.guide_id,
                    "crispri_region_type": g.crispri_region_type,
                    "distance_to_start_codon": g.distance_to_start_codon,
                    "target_strand_relation": g.target_strand_relation,
                })
            crispri_df = pd.DataFrame(crispri_data)
            crispri_df.to_excel(writer, sheet_name="crispri_details", index=False)
