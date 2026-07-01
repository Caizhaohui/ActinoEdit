"""Tests for off-target search module."""

import pytest

from actinoedit.core.models import Contig, GuideCandidate, OffTargetHit
from actinoedit.core.offtarget import (
    count_offtargets_by_mismatch,
    filter_offtargets,
    get_offtarget_summary,
    search_offtargets,
)


@pytest.fixture
def sample_guide() -> GuideCandidate:
    """Sample guide for testing."""
    return GuideCandidate(
        guide_id="guide_001",
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
    )


@pytest.fixture
def sample_contigs() -> dict[str, Contig]:
    """Sample contigs for testing."""
    # Create a genome with some off-target sites
    seq1 = "N" * 99 + "ATCGATCGATCGATCGATCG" + "N" * 100  # On-target
    seq1 += "ATCGATCGATCGATCGATCN" + "N" * 50  # 1 mismatch (last base different)
    seq1 += "NNNNATCGATCGATCGATCG" + "N" * 50  # Exact match at different position

    return {
        "contig1": Contig(name="contig1", sequence=seq1),
        "contig2": Contig(name="contig2", sequence="N" * 500),
    }


class TestSearchOfftargets:
    """Tests for search_offtargets function."""

    def test_basic_search(self, sample_guide: GuideCandidate, sample_contigs: dict) -> None:
        """Test basic off-target search."""
        hits = search_offtargets(sample_guide, sample_contigs, max_mismatches=3)
        assert isinstance(hits, list)

    def test_ignore_on_target(self, sample_guide: GuideCandidate, sample_contigs: dict) -> None:
        """Test ignoring on-target site."""
        hits = search_offtargets(
            sample_guide, sample_contigs,
            max_mismatches=3, ignore_on_target=True
        )
        # Should not include the on-target position
        on_target_hits = [
            h for h in hits
            if h.contig == "contig1" and h.start == 100 and h.mismatch_count == 0
        ]
        assert len(on_target_hits) == 0

    def test_include_on_target(self, sample_guide: GuideCandidate, sample_contigs: dict) -> None:
        """Test including on-target site."""
        hits = search_offtargets(
            sample_guide, sample_contigs,
            max_mismatches=3, ignore_on_target=False
        )
        # Should include the on-target position
        on_target_hits = [
            h for h in hits
            if h.contig == "contig1" and h.start == 100 and h.mismatch_count == 0
        ]
        assert len(on_target_hits) == 1

    def test_max_mismatches(self, sample_guide: GuideCandidate, sample_contigs: dict) -> None:
        """Test max mismatches filter."""
        hits_0 = search_offtargets(sample_guide, sample_contigs, max_mismatches=0)
        hits_3 = search_offtargets(sample_guide, sample_contigs, max_mismatches=3)
        assert len(hits_0) <= len(hits_3)

    def test_hit_properties(self, sample_guide: GuideCandidate, sample_contigs: dict) -> None:
        """Test hit properties."""
        hits = search_offtargets(sample_guide, sample_contigs, max_mismatches=3)
        if hits:
            hit = hits[0]
            assert hit.guide_id == "guide_001"
            assert hit.mismatch_count >= 0
            assert hit.mismatch_count <= 3
            assert len(hit.mismatch_positions) == hit.mismatch_count


class TestCountOfftargetsByMismatch:
    """Tests for count_offtargets_by_mismatch function."""

    def test_count(self) -> None:
        """Test counting by mismatch."""
        hits = [
            OffTargetHit(
                guide_id="g1", contig="c1", start=1, end=20,
                strand="+", sequence="A" * 20, mismatch_count=0
            ),
            OffTargetHit(
                guide_id="g1", contig="c1", start=50, end=69,
                strand="+", sequence="A" * 20, mismatch_count=1
            ),
            OffTargetHit(
                guide_id="g1", contig="c1", start=100, end=119,
                strand="+", sequence="A" * 20, mismatch_count=1
            ),
        ]
        counts = count_offtargets_by_mismatch(hits, max_mismatches=3)
        assert counts[0] == 1
        assert counts[1] == 2
        assert counts[2] == 0
        assert counts[3] == 0


class TestFilterOfftargets:
    """Tests for filter_offtargets function."""

    def test_filter_by_mismatch(self) -> None:
        """Test filtering by mismatch count."""
        hits = [
            OffTargetHit(
                guide_id="g1", contig="c1", start=1, end=20,
                strand="+", sequence="A" * 20, mismatch_count=0
            ),
            OffTargetHit(
                guide_id="g1", contig="c1", start=50, end=69,
                strand="+", sequence="A" * 20, mismatch_count=2
            ),
            OffTargetHit(
                guide_id="g1", contig="c1", start=100, end=119,
                strand="+", sequence="A" * 20, mismatch_count=5
            ),
        ]
        filtered = filter_offtargets(hits, max_mismatches=2)
        assert len(filtered) == 2

    def test_filter_by_contig(self) -> None:
        """Test filtering by contig."""
        hits = [
            OffTargetHit(
                guide_id="g1", contig="c1", start=1, end=20,
                strand="+", sequence="A" * 20, mismatch_count=0
            ),
            OffTargetHit(
                guide_id="g1", contig="c2", start=50, end=69,
                strand="+", sequence="A" * 20, mismatch_count=1
            ),
        ]
        filtered = filter_offtargets(hits, exclude_contigs=["c2"])
        assert len(filtered) == 1
        assert filtered[0].contig == "c1"


class TestGetOfftargetSummary:
    """Tests for get_offtarget_summary function."""

    def test_summary(self, sample_guide: GuideCandidate) -> None:
        """Test summary generation."""
        hits = [
            OffTargetHit(
                guide_id="guide_001", contig="c1", start=1, end=20,
                strand="+", sequence="A" * 20, mismatch_count=0
            ),
            OffTargetHit(
                guide_id="guide_001", contig="c1", start=50, end=69,
                strand="+", sequence="A" * 20, mismatch_count=1
            ),
        ]
        summary = get_offtarget_summary(sample_guide, hits)
        assert summary["guide_id"] == "guide_001"
        assert summary["total_hits"] == 2
        assert summary["0_mismatch"] == 1
        assert summary["1_mismatch"] == 1
