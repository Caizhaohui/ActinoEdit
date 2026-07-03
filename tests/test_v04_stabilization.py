"""v0.4 stabilization tests: host defaults, resolve, core modules."""

from __future__ import annotations

from pathlib import Path

import pytest

from actinoedit.core.crispri import annotate_crispri_guides
from actinoedit.core.design_types import DesignInput
from actinoedit.core.models import GuideCandidate, TargetRegion
from actinoedit.core.resolve import resolve_design_params
from actinoedit.web.app import DEFAULT_WEB_HOST


def test_default_web_host_is_localhost() -> None:
    assert DEFAULT_WEB_HOST == "127.0.0.1"


def test_resolve_design_params_is_immutable(demo_files: tuple[Path, Path]) -> None:
    fasta_file, gff_file = demo_files
    inp = DesignInput(
        genome_path=str(fasta_file),
        annotation_path=str(gff_file),
        target="SCO0001",
        organism_profile="streptomyces",
    )
    resolved = resolve_design_params(inp)
    assert resolved.profile_name == "streptomyces"
    assert inp.pam == "NGG"
    assert resolved.pam == "NGG"


def test_crispri_module_annotates_guides() -> None:
    target = TargetRegion(
        contig="c1",
        start=100,
        end=300,
        strand="+",
        label="geneA",
    )
    guide = GuideCandidate(
        guide_id="g1",
        contig="c1",
        spacer="A" * 20,
        pam="NGG",
        start=90,
        end=113,
        strand="+",
        pam_start=114,
        pam_end=116,
        cut_site=113,
        gc_content=0.0,
    )
    annotate_crispri_guides([guide], target)
    assert guide.crispri_region_type in {"promoter", "early_cds", "cds"}
    assert guide.distance_to_start_codon is not None


@pytest.fixture
def demo_files(tmp_path: Path) -> tuple[Path, Path]:
    fasta_file = tmp_path / "genome.fasta"
    fasta_file.write_text(
        ">contig1\n"
        + "ATCG" * 50
        + "\n"
    )
    gff_file = tmp_path / "annotation.gff"
    gff_file.write_text(
        "##gff-version 3\n"
        "contig1\tProdigal\tgene\t10\t200\t.\t+\t0\tID=geneA;locus_tag=SCO0001;gene=geneA\n"
    )
    return fasta_file, gff_file
