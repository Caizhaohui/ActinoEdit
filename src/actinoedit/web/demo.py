"""Demo mode helpers for one-click Web acceptance (v0.4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from actinoedit.resources import get_demo_annotation_path, get_demo_genome_path
from actinoedit.web.runner import run_design
from actinoedit.web.state import WebState


def load_demo_state(state: WebState) -> None:
    """Populate web state with bundled Streptomyces demo inputs."""
    genome = get_demo_genome_path()
    annotation = get_demo_annotation_path("gff")
    if not genome.is_file():
        raise FileNotFoundError(f"Demo genome missing: {genome}")
    if not annotation.is_file():
        raise FileNotFoundError(f"Demo annotation missing: {annotation}")

    state.genome_path = str(genome)
    state.annotation_path = str(annotation)
    state.annotation_format = "gff"
    state.profile_name = "streptomyces"
    state.pam = "NGG"
    state.spacer_length = 20
    state.max_mismatches = 3
    state.target = "geneA"
    state.design_mode = "knockout"


def run_demo_acceptance(
    output_dir: str | Path | None = None,
    db_url: str | None = None,
) -> dict[str, Any]:
    """Headless v0.4 acceptance: demo load -> design -> reports -> DB -> export.

    Raises on failure. Returns a summary dict for logging/CI.
    """
    from actinoedit.db import (
        export_project_guides,
        get_project_guides,
        save_guides_from_result,
    )
    from actinoedit.db.database import get_engine, init_database
    from actinoedit.db.session import use_db_url
    from actinoedit.reports import write_design_reports

    out = Path(output_dir or Path.cwd() / "results" / "demo_acceptance")
    out.mkdir(parents=True, exist_ok=True)

    state = WebState()
    load_demo_state(state)
    result = run_design(state)
    if not result.guide_candidates:
        raise RuntimeError("Demo design produced no guides")

    prefix = out / "demo_design"
    report_paths = write_design_reports(
        result.guide_candidates,
        result.guide_scores,
        result.off_target_hits,
        result.target_region,
        result.warnings,
        str(prefix),
        {"source": "demo-acceptance"},
    )
    for path in report_paths:
        if not Path(path).is_file():
            raise RuntimeError(f"Expected report missing: {path}")

    if db_url is None:
        db_url = f"sqlite:///{out / 'acceptance.db'}"

    init_database(get_engine(db_url))
    project_name = "demo_acceptance"
    export_path = out / "demo_guides_export.csv"

    with use_db_url(db_url):
        n_saved = save_guides_from_result(
            result,
            project_name,
            design_run_meta={
                "genome_path": state.genome_path,
                "annotation_path": state.annotation_path,
                "target": state.target,
                "organism_profile": state.profile_name,
                "pam": state.pam,
                "design_mode": state.design_mode,
                "spacer_length": state.spacer_length,
                "max_mismatches": state.max_mismatches,
                "parameters": {"source": "demo-acceptance"},
            },
        )
        guides = get_project_guides(project_name)
        export_project_guides(project_name, export_path)

    if n_saved != len(result.guide_candidates):
        raise RuntimeError(f"Saved {n_saved} guides, expected {len(result.guide_candidates)}")
    if len(guides) != n_saved:
        raise RuntimeError("Guide count mismatch after DB save")
    if not export_path.is_file():
        raise RuntimeError(f"Export missing: {export_path}")

    return {
        "guides": len(result.guide_candidates),
        "reports": report_paths,
        "db_project": project_name,
        "export": str(export_path),
    }
