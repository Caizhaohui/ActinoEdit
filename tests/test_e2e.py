"""End-to-end tests: demo genome -> design -> reports -> DB -> export."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from actinoedit.cli import app
from actinoedit.core.pipeline import DesignInput, run_design_pipeline
from actinoedit.db import (
    export_project_guides,
    get_project_guides,
    import_genome,
    save_guides_from_result,
)
from actinoedit.db.session import use_db_url
from actinoedit.reports import write_design_reports

runner = CliRunner()
EXAMPLES = Path(__file__).parent.parent / "examples"


@pytest.fixture
def demo_paths() -> tuple[Path, Path]:
    """Return paths to bundled demo genome and annotation."""
    genome = EXAMPLES / "demo_genome.fasta"
    gff = EXAMPLES / "demo_annotation.gff"
    assert genome.exists(), "examples/demo_genome.fasta missing"
    assert gff.exists(), "examples/demo_annotation.gff missing"
    return genome, gff


def test_e2e_pipeline_reports_db_export(
    demo_paths: tuple[Path, Path],
    tmp_path: Path,
    db_url: str,
) -> None:
    """Full local workflow without polluting the user database."""
    genome, gff = demo_paths
    out_prefix = tmp_path / "e2e_design"

    with use_db_url(db_url):
        inp = DesignInput(
            genome_path=str(genome),
            annotation_path=str(gff),
            target="geneA",
            organism_profile="streptomyces",
        )
        result = run_design_pipeline(inp)
        assert result.guide_candidates, "expected guides from demo genome"

        report_paths = write_design_reports(
            result.guide_candidates,
            result.guide_scores,
            result.off_target_hits,
            result.target_region,
            result.warnings,
            str(out_prefix),
            {"source": "e2e-test"},
        )
        assert any(p.endswith("_guides.csv") for p in report_paths)
        assert any(p.endswith("_report.xlsx") for p in report_paths)
        assert any(p.endswith("_report.html") for p in report_paths)

        project_name = "e2e_demo_project"
        n_saved = save_guides_from_result(result, project_name)
        assert n_saved == len(result.guide_candidates)

        guides = get_project_guides(project_name)
        assert len(guides) == n_saved
        assert guides[0]["guide_id"]

        export_path = tmp_path / "exported_guides.csv"
        written = export_project_guides(project_name, export_path)
        assert Path(written).exists()
        assert Path(written).read_text().count("\n") >= 2


def test_e2e_cli_design_and_db_import(
    demo_paths: tuple[Path, Path],
    tmp_path: Path,
    db_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI design command and genome import against isolated DB."""
    genome, gff = demo_paths
    monkeypatch.setenv("ACTINOEDIT_DB_URL", db_url)
    out_prefix = tmp_path / "cli_design"

    result = runner.invoke(
        app,
        [
            "design",
            "--genome", str(genome),
            "--gff", str(gff),
            "--target", "geneA",
            "--profile", "streptomyces",
            "--output-prefix", str(out_prefix),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "cli_design_guides.csv").exists()

    with use_db_url(db_url):
        summary = import_genome("demo_strep", str(genome), str(gff), organism_name="Streptomyces demo")
        assert summary["genome_id"] > 0
        assert summary["features_imported"] > 0


def test_e2e_env_only_db_routing(db_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end DB save works with ACTINOEDIT_DB_URL only (no use_db_url)."""
    monkeypatch.setenv("ACTINOEDIT_DB_URL", db_url)
    genome, gff = (
        EXAMPLES / "demo_genome.fasta",
        EXAMPLES / "demo_annotation.gff",
    )
    inp = DesignInput(
        genome_path=str(genome),
        annotation_path=str(gff),
        target="geneA",
        organism_profile="streptomyces",
    )
    result = run_design_pipeline(inp)
    assert result.guide_candidates

    project_name = "env_only_e2e"
    n_saved = save_guides_from_result(result, project_name)
    assert n_saved == len(result.guide_candidates)
    assert len(get_project_guides(project_name)) == n_saved


def test_e2e_web_runner_design(demo_paths: tuple[Path, Path]) -> None:
    """Web runner uses the same pipeline as CLI."""
    from actinoedit.web.runner import run_design
    from actinoedit.web.state import WebState

    genome, gff = demo_paths
    state = WebState()
    state.genome_path = str(genome)
    state.annotation_path = str(gff)
    state.annotation_format = "gff"
    state.profile_name = "streptomyces"
    state.target = "geneA"

    result = run_design(state)
    assert result.guide_candidates


def test_e2e_db_service_acceptance(tmp_path: Path) -> None:
    """db_service wraps the headless demo acceptance workflow."""
    from actinoedit.web import db_service

    summary = db_service.run_demo_acceptance(output_dir=tmp_path / "svc_acceptance")
    assert summary["guides"] > 0
    assert Path(summary["export"]).is_file()
