"""Tests for Alembic-backed database initialization and design_runs."""

from __future__ import annotations

from pathlib import Path

import pytest

from actinoedit.core.pipeline import DesignInput, run_design_pipeline
from actinoedit.db import (
    get_database_status,
    list_design_runs,
    save_guides_from_result,
    save_organism,
)
from actinoedit.db.crud import save_genome
from actinoedit.db.session import use_db_url


def test_init_database_uses_alembic(isolated_db_url: str) -> None:
    status = get_database_status(isolated_db_url)
    assert status["head_revision"] == "003"
    assert status["current_revision"] == "003"
    assert status["up_to_date"] is True


def test_organism_and_genome_unique_names(isolated_db_url: str) -> None:
    with use_db_url(isolated_db_url):
        save_organism("unique_org")
        save_organism("unique_org")
        save_genome("unique_genome", contigs=1)
        save_genome("unique_genome", contigs=2)


def test_design_run_recorded_on_save(
    demo_paths: tuple[Path, Path],
    isolated_db_url: str,
) -> None:
    genome, gff = demo_paths
    inp = DesignInput(
        genome_path=str(genome),
        annotation_path=str(gff),
        target="geneA",
        organism_profile="streptomyces",
    )
    result = run_design_pipeline(inp)
    assert result.guide_candidates

    with use_db_url(isolated_db_url):
        n = save_guides_from_result(
            result,
            "run_proj",
            design_run_meta={
                "genome_path": str(genome),
                "annotation_path": str(gff),
                "target": "geneA",
                "organism_profile": "streptomyces",
                "pam": "NGG",
                "design_mode": "knockout",
                "spacer_length": 20,
                "max_mismatches": 3,
            },
        )
        assert n == len(result.guide_candidates)
        runs = list_design_runs("run_proj")
        assert len(runs) == 1
        assert runs[0]["target"] == "geneA"
        assert runs[0]["guide_count"] == n


@pytest.fixture
def demo_paths() -> tuple[Path, Path]:
    examples = Path(__file__).parent.parent / "examples"
    return examples / "demo_genome.fasta", examples / "demo_annotation.gff"
