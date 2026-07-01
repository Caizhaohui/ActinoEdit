"""Report generation modules."""

from pathlib import Path

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    TargetRegion,
)
from actinoedit.reports.excel import write_excel_report
from actinoedit.reports.html import write_html_report
from actinoedit.reports.tables import guides_to_dataframe, offtargets_to_dataframe

__all__ = [
    "guides_to_dataframe",
    "offtargets_to_dataframe",
    "write_csv_report",
    "write_excel_report",
    "write_html_report",
    "write_design_reports",
]


def write_csv_report(
    guides: list[GuideCandidate],
    output_path: str | Path,
    scores: list[GuideScore] | None = None,
    off_target_hits: dict[str, list[OffTargetHit]] | None = None,
) -> None:
    """Write guides to a CSV file with scores and off-target info.

    Args:
        guides: List of GuideCandidate.
        output_path: Path for CSV.
        scores: Optional scores list.
        off_target_hits: Optional offtarget dict.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = guides_to_dataframe(guides, scores, off_target_hits)
    df.to_csv(output_path, index=False)


def write_design_reports(
    guides: list[GuideCandidate],
    scores: list[GuideScore] | None,
    off_target_hits: dict[str, list[OffTargetHit]] | None,
    target_region: TargetRegion | None,
    warnings: list[str] | None,
    output_prefix: str,
    parameters: dict[str, str] | None = None,
) -> list[str]:
    """Generate the three standard reports (CSV, Excel, HTML) for a design.

    This is the shared report writer used by CLI and (future) other callers.

    Naming convention:
      output_prefix="results/geneA" produces:
        results/geneA_guides.csv
        results/geneA_report.xlsx
        results/geneA_report.html

    Args:
        guides: guide candidates
        scores: scores list
        off_target_hits: map guide_id -> hits
        target_region: the resolved target (for HTML)
        warnings: list of warnings
        output_prefix: base name/path without extension
        parameters: dict of run parameters for metadata sheets

    Returns:
        List of absolute paths to the generated files.
    """
    prefix_path = Path(output_prefix)
    out_dir = prefix_path.parent
    base = prefix_path.name or "guides"
    # Strip common extensions if user passed a full filename as prefix
    for ext in (".csv", ".xlsx", ".html", ".txt"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
            break
    if not base:
        base = "guides"
    out_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []

    # CSV: <base>_guides.csv
    csv_path = out_dir / f"{base}_guides.csv"
    write_csv_report(guides, csv_path, scores, off_target_hits)
    created.append(str(csv_path))

    # Excel: <base>_report.xlsx
    xlsx_path = out_dir / f"{base}_report.xlsx"
    write_excel_report(
        guides,
        xlsx_path,
        scores,
        off_target_hits,
        parameters or {},
        warnings or [],
    )
    created.append(str(xlsx_path))

    # HTML: <base>_report.html
    html_path = out_dir / f"{base}_report.html"
    write_html_report(
        guides,
        html_path,
        target_region,
        scores,
        off_target_hits,
        parameters or {},
        warnings or [],
    )
    created.append(str(html_path))

    return created
