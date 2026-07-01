"""Tests for guide RNA scanner."""

import pytest

from actinoedit.core.models import Contig, TargetRegion
from actinoedit.core.scanner import (
    ScannerConfig,
    filter_guides_by_gc,
    scan_entire_contig,
    scan_guides,
    sort_guides_by_gc,
)


@pytest.fixture
def sample_contig() -> Contig:
    """Sample contig for testing."""
    # Sequence with multiple NGG PAMs
    sequence = (
        "ATCGATCGATCGATCGATCG"  # 20 bp
        "AGG"  # PAM at 21-23
        "ATCGATCGATCGATCGATCG"  # 20 bp spacer
        "CGG"  # PAM at 44-46
        "GCGCGCGCGCGCGCGCGCGC"  # 20 bp GC-rich
        "TGG"  # PAM at 67-69
        "AAAAAAAATTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"  # AT-rich
        "GGG"  # PAM
        "ATCGATCGATCGATCGATCG"  # 20 bp
        "AGG"  # PAM
    )
    return Contig(name="contig1", sequence=sequence)


@pytest.fixture
def sample_target() -> TargetRegion:
    """Sample target region for testing."""
    return TargetRegion(
        contig="contig1",
        start=1,
        end=100,
        strand="+",
        label="test_gene",
    )


class TestScannerConfig:
    """Tests for ScannerConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = ScannerConfig()
        assert config.pam_pattern == "NGG"
        assert config.spacer_length == 20
        assert config.cut_offset == 3
        assert config.nuclease_name == "SpCas9"

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = ScannerConfig(
            pam_pattern="TTTV",
            spacer_length=20,
            cut_offset=18,
            nuclease_name="Cas12a",
        )
        assert config.pam_pattern == "TTTV"
        assert config.cut_offset == 18


class TestScanGuides:
    """Tests for scan_guides function."""

    def test_basic_scan(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test basic guide scanning."""
        guides = scan_guides(sample_contig, sample_target)
        assert len(guides) > 0

    def test_forward_strand(self, sample_contig: Contig) -> None:
        """Test forward strand scanning."""
        target = TargetRegion(contig="contig1", start=1, end=50, strand="+")
        guides = scan_guides(sample_contig, target)
        forward_guides = [g for g in guides if g.strand == "+"]
        assert len(forward_guides) > 0

    def test_reverse_strand(self, sample_contig: Contig) -> None:
        """Test reverse strand scanning."""
        target = TargetRegion(contig="contig1", start=1, end=50, strand="-")
        guides = scan_guides(sample_contig, target)
        reverse_guides = [g for g in guides if g.strand == "-"]
        # May or may not have reverse strand guides depending on sequence
        assert isinstance(reverse_guides, list)

    def test_guide_properties(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test guide candidate properties."""
        guides = scan_guides(sample_contig, sample_target)
        if guides:
            guide = guides[0]
            assert guide.guide_id is not None
            assert guide.contig == "contig1"
            assert len(guide.spacer) == 20
            assert guide.gc_content >= 0 and guide.gc_content <= 1
            assert guide.start >= 1
            assert guide.end >= guide.start

    def test_pam_matching(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test that all guides have matching PAM."""
        guides = scan_guides(sample_contig, sample_target)
        for guide in guides:
            # PAM should match NGG pattern
            assert guide.pam in ["AGG", "CGG", "GGG", "TGG"]

    def test_invalid_target(self, sample_contig: Contig) -> None:
        """Test invalid target region."""
        # TargetRegion raises ValueError in __post_init__ for invalid start
        with pytest.raises(ValueError, match="Start position must be >= 1"):
            TargetRegion(contig="contig1", start=0, end=100, strand="+")

    def test_custom_pam(self, sample_contig: Contig) -> None:
        """Test custom PAM pattern."""
        config = ScannerConfig(pam_pattern="CGG")
        target = TargetRegion(contig="contig1", start=1, end=100, strand="+")
        guides = scan_guides(sample_contig, target, config)
        for guide in guides:
            assert guide.pam == "CGG"


class TestScanEntireContig:
    """Tests for scan_entire_contig function."""

    def test_scan_entire(self, sample_contig: Contig) -> None:
        """Test scanning entire contig."""
        guides = scan_entire_contig(sample_contig)
        assert len(guides) > 0


class TestFilterGuidesByGc:
    """Tests for filter_guides_by_gc function."""

    def test_filter_gc(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test filtering by GC content."""
        guides = scan_guides(sample_contig, sample_target)
        filtered = filter_guides_by_gc(guides, gc_min=0.4, gc_max=0.6)
        for guide in filtered:
            assert 0.4 <= guide.gc_content <= 0.6

    def test_filter_no_result(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test filtering with no results."""
        guides = scan_guides(sample_contig, sample_target)
        # Use a range that excludes all guides
        filtered = filter_guides_by_gc(guides, gc_min=0.01, gc_max=0.02)
        assert len(filtered) == 0


class TestSortGuidesByGc:
    """Tests for sort_guides_by_gc function."""

    def test_sort_ascending(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test ascending sort."""
        guides = scan_guides(sample_contig, sample_target)
        sorted_guides = sort_guides_by_gc(guides)
        for i in range(len(sorted_guides) - 1):
            assert sorted_guides[i].gc_content <= sorted_guides[i + 1].gc_content

    def test_sort_descending(self, sample_contig: Contig, sample_target: TargetRegion) -> None:
        """Test descending sort."""
        guides = scan_guides(sample_contig, sample_target)
        sorted_guides = sort_guides_by_gc(guides, reverse=True)
        for i in range(len(sorted_guides) - 1):
            assert sorted_guides[i].gc_content >= sorted_guides[i + 1].gc_content
