"""Tests for organism / genome / project entity links."""

from __future__ import annotations

from pathlib import Path

import pytest

from actinoedit.db import (
    create_project,
    get_genome,
    get_project,
    import_genome,
    link_genome_to_organism,
    list_genomes_for_organism,
    list_projects,
    list_projects_for_organism,
    save_genome,
    save_organism,
    update_project,
)
from actinoedit.db.session import use_db_url

EXAMPLES = Path(__file__).parent.parent / "examples"


def test_create_project_with_links(db_url: str) -> None:
    with use_db_url(db_url):
        save_organism("S. demo", species="Streptomyces")
        save_genome("demo_g", contigs=1, organism_name="S. demo")
        pid = create_project(
            "linked_proj",
            description="test",
            profile="streptomyces",
            organism_name="S. demo",
            genome_name="demo_g",
        )
        assert pid > 0
        detail = get_project("linked_proj")
        assert detail is not None
        assert detail["organism_name"] == "S. demo"
        assert detail["genome_name"] == "demo_g"
        assert detail["guide_count"] == 0


def test_import_genome_links_organism(
    db_url: str,
    demo_paths: tuple[Path, Path],
) -> None:
    genome, gff = demo_paths
    with use_db_url(db_url):
        summary = import_genome(
            "strep_demo",
            str(genome),
            str(gff),
            organism_name="Streptomyces demo",
        )
        assert summary["genome_id"] > 0
        detail = get_genome("strep_demo")
        assert detail is not None
        assert detail["organism_name"] == "Streptomyces demo"
        genomes = list_genomes_for_organism("Streptomyces demo")
        assert len(genomes) == 1
        assert genomes[0]["name"] == "strep_demo"


def test_link_genome_and_project_update(db_url: str) -> None:
    with use_db_url(db_url):
        save_organism("org_a")
        save_organism("org_b")
        save_genome("genome_x", contigs=2)
        create_project("proj_link")

        assert link_genome_to_organism("genome_x", "org_a")
        assert get_genome("genome_x")["organism_name"] == "org_a"

        assert update_project("proj_link", organism_name="org_b", genome_name="genome_x")
        detail = get_project("proj_link")
        assert detail is not None
        assert detail["organism_name"] == "org_b"
        assert detail["genome_name"] == "genome_x"

        projects = list_projects_for_organism("org_b")
        assert any(p["name"] == "proj_link" for p in projects)


def test_list_projects_includes_link_fields(db_url: str) -> None:
    with use_db_url(db_url):
        save_organism("list_org")
        save_genome("list_genome", contigs=1, organism_name="list_org")
        create_project("list_proj", organism_name="list_org", genome_name="list_genome")
        rows = list_projects()
        match = [p for p in rows if p["name"] == "list_proj"]
        assert len(match) == 1
        assert match[0]["organism_name"] == "list_org"
        assert match[0]["genome_name"] == "list_genome"


def test_create_project_unknown_link_raises(db_url: str) -> None:
    with use_db_url(db_url), pytest.raises(ValueError, match="Organism not found"):
        create_project("bad_proj", organism_name="missing_org")


@pytest.fixture
def demo_paths() -> tuple[Path, Path]:
    genome = EXAMPLES / "demo_genome.fasta"
    gff = EXAMPLES / "demo_annotation.gff"
    assert genome.exists()
    assert gff.exists()
    return genome, gff
