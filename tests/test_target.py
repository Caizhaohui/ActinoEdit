"""Tests for target region selection."""

import pytest

from actinoedit.core.models import GeneFeature
from actinoedit.core.target import (
    get_target_info,
    list_targets,
    resolve_target,
)


@pytest.fixture
def sample_features() -> list[GeneFeature]:
    """Sample features for testing."""
    return [
        GeneFeature(
            contig="contig1", start=100, end=500, strand="+",
            locus_tag="SCO0001", gene_name="dnaA", product="DNA replication"
        ),
        GeneFeature(
            contig="contig1", start=600, end=1000, strand="-",
            locus_tag="SCO0002", gene_name="dnaN", product="DNA polymerase"
        ),
        GeneFeature(
            contig="contig2", start=100, end=400, strand="+",
            locus_tag="SCO0003", gene_name="gyrA", product="DNA gyrase"
        ),
        GeneFeature(
            contig="contig2", start=500, end=800, strand="+",
            locus_tag="SCO0004", gene_name="gyrB", product="DNA gyrase subunit B"
        ),
    ]


class TestResolveTarget:
    """Tests for resolve_target function."""

    def test_by_locus_tag(self, sample_features: list[GeneFeature]) -> None:
        """Test resolving by locus tag."""
        target = resolve_target(sample_features, "SCO0001")
        assert target.contig == "contig1"
        assert target.start == 100
        assert target.end == 500
        assert target.strand == "+"

    def test_by_gene_name(self, sample_features: list[GeneFeature]) -> None:
        """Test resolving by gene name."""
        target = resolve_target(sample_features, "dnaA")
        assert target.contig == "contig1"
        assert target.start == 100
        assert target.end == 500

    def test_by_coordinate(self, sample_features: list[GeneFeature]) -> None:
        """Test resolving by coordinate string."""
        target = resolve_target(sample_features, "contig1:200-300")
        assert target.contig == "contig1"
        assert target.start == 200
        assert target.end == 300
        assert target.strand == "."

    def test_ambiguous_gene_name(self, sample_features: list[GeneFeature]) -> None:
        """Test ambiguous gene name raises error."""
        # Add another dnaA gene
        features = sample_features + [
            GeneFeature(
                contig="contig2", start=1000, end=1500, strand="+",
                locus_tag="SCO0005", gene_name="dnaA", product="DNA replication"
            ),
        ]
        with pytest.raises(ValueError, match="Ambiguous"):
            resolve_target(features, "dnaA")

    def test_not_found(self, sample_features: list[GeneFeature]) -> None:
        """Test target not found."""
        with pytest.raises(ValueError, match="not found"):
            resolve_target(sample_features, "nonexistent")

    def test_with_flank(self, sample_features: list[GeneFeature]) -> None:
        """Test resolving with flanks."""
        target = resolve_target(
            sample_features, "SCO0001",
            upstream_flank=50, downstream_flank=30
        )
        assert target.start == 50  # 100 - 50
        assert target.end == 530   # 500 + 30

    def test_flank_at_contig_start(self, sample_features: list[GeneFeature]) -> None:
        """Test flank at contig start."""
        target = resolve_target(
            sample_features, "SCO0001",
            upstream_flank=200
        )
        assert target.start == 1  # max(1, 100-200)


class TestGetTargetInfo:
    """Tests for get_target_info function."""

    def test_by_locus_tag(self, sample_features: list[GeneFeature]) -> None:
        """Test getting info by locus tag."""
        info = get_target_info(sample_features, "SCO0001")
        assert info["contig"] == "contig1"
        assert info["locus_tag"] == "SCO0001"
        assert info["gene_name"] == "dnaA"
        assert info["product"] == "DNA replication"

    def test_by_coordinate(self, sample_features: list[GeneFeature]) -> None:
        """Test getting info by coordinate."""
        info = get_target_info(sample_features, "contig1:200-300")
        assert info["contig"] == "contig1"
        assert info["start"] == 200
        assert info["end"] == 300
        assert "locus_tag" not in info


class TestListTargets:
    """Tests for list_targets function."""

    def test_list_all(self, sample_features: list[GeneFeature]) -> None:
        """Test listing all targets."""
        targets = list_targets(sample_features)
        assert len(targets) == 4

    def test_list_by_contig(self, sample_features: list[GeneFeature]) -> None:
        """Test listing targets by contig."""
        targets = list_targets(sample_features, contig="contig1")
        assert len(targets) == 2

    def test_list_properties(self, sample_features: list[GeneFeature]) -> None:
        """Test target properties."""
        targets = list_targets(sample_features)
        target = targets[0]
        assert target["locus_tag"] == "SCO0001"
        assert target["gene_name"] == "dnaA"
        assert target["contig"] == "contig1"
        assert target["start"] == 100
        assert target["end"] == 500
