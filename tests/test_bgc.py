"""Tests for BGC annotation module."""

from pathlib import Path

import pytest

from actinoedit.annotation.bgc import (
    annotate_guides_with_bgc,
    find_bgc_for_position,
    find_nearest_bgc,
    load_bgc_regions,
)
from actinoedit.core.models import BGCRegion, GuideCandidate


@pytest.fixture
def demo_bgc_regions() -> list[BGCRegion]:
    return [
        BGCRegion(contig="contig1", start=50, end=280, bgc_id="bgc1", bgc_type="PKS", product="demo"),
        BGCRegion(contig="contig1", start=500, end=900, bgc_id="bgc2", bgc_type="NRPS"),
    ]


@pytest.fixture
def demo_guides() -> list[GuideCandidate]:
    return [
        GuideCandidate(
            guide_id="g1",
            contig="contig1",
            spacer="ATCGATCGATCGATCGATCG",
            pam="NGG",
            start=100,
            end=119,
            strand="+",
            pam_start=120,
            pam_end=122,
            cut_site=117,
            gc_content=0.5,
        ),
        GuideCandidate(
            guide_id="g2",
            contig="contig1",
            spacer="GCGCGCGCGCGCGCGCGCGC",
            pam="NGG",
            start=350,
            end=369,
            strand="+",
            pam_start=370,
            pam_end=372,
            cut_site=367,
            gc_content=1.0,
        ),
        GuideCandidate(
            guide_id="g3",
            contig="contig1",
            spacer="TTTTTTTTTTTTTTTTTTTT",
            pam="NGG",
            start=520,
            end=539,
            strand="-",
            pam_start=540,
            pam_end=542,
            cut_site=537,
            gc_content=0.0,
        ),
    ]


def test_load_bgc_regions(tmp_path: Path) -> None:
    bgc_file = tmp_path / "test.bgc"
    bgc_file.write_text(
        "# comment\ncontig1\t100\t300\tBGC001\tPKS\tproduct1\ncontig2 400 600 BGC002\n"
    )
    regs = load_bgc_regions(bgc_file)
    assert len(regs) == 2
    assert regs[0].bgc_id == "BGC001"
    assert regs[1].bgc_id == "BGC002"


def test_find_bgc_inside(demo_bgc_regions: list[BGCRegion]) -> None:
    r = find_bgc_for_position("contig1", 150, demo_bgc_regions)
    assert r is not None
    assert r.bgc_id == "bgc1"


def test_find_bgc_outside(demo_bgc_regions: list[BGCRegion]) -> None:
    r = find_bgc_for_position("contig1", 400, demo_bgc_regions)
    assert r is None


def test_nearest_bgc(demo_bgc_regions: list[BGCRegion]) -> None:
    reg, dist = find_nearest_bgc("contig1", 400, demo_bgc_regions, max_distance=200)
    assert reg is not None
    assert reg.bgc_id == "bgc2"
    assert dist > 0


def test_annotate_guides(demo_guides: list[GuideCandidate], demo_bgc_regions: list[BGCRegion]) -> None:
    annotated = annotate_guides_with_bgc(demo_guides, demo_bgc_regions, near_threshold=100)
    # g1 inside bgc1 (100-119 overlaps 50-280)
    assert annotated[0].bgc_id == "bgc1"
    assert "inside" in (annotated[0].bgc_context or "")
    # g2 at ~350 , distance to bgc1(~70bp) so it is "near" under 100bp threshold
    assert annotated[1].bgc_id == "bgc1"
    assert "near" in (annotated[1].bgc_context or "")
    # g3 inside bgc2
    assert annotated[2].bgc_id == "bgc2"


def test_bgc_model_validation() -> None:
    with pytest.raises(ValueError):
        BGCRegion(contig="c1", start=100, end=50, bgc_id="x")
