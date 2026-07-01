"""Tests for GFF3 parser."""

from pathlib import Path

import pytest

from actinoedit.io.gff import (
    filter_by_feature_type,
    find_by_gene_name,
    find_by_locus_tag,
    find_features_in_region,
    find_genes_by_contig,
    get_cds_features,
    get_gene_features,
    get_unique_contigs,
    parse_gff,
    parse_gff_string,
)


@pytest.fixture
def sample_gff_content() -> str:
    """Sample GFF3 content for testing."""
    return """##gff-version 3
##species Streptomyces coelicolor
contig1\tProdigal:2.60\tgene\t1\t300\t.\t+\t0\tID=geneA;locus_tag=SCO0001;gene=geneA;product=Hypothetical protein
contig1\tProdigal:2.60\tCDS\t1\t300\t.\t+\t0\tID=cdsA;Parent=geneA;locus_tag=SCO0001;gene=geneA;product=Hypothetical protein
contig1\tProdigal:2.60\tgene\t400\t800\t.\t+\t0\tID=geneB;locus_tag=SCO0002;gene=geneB;product=Transcriptional regulator
contig1\tProdigal:2.60\tCDS\t400\t800\t.\t+\t0\tID=cdsB;Parent=geneB;locus_tag=SCO0002;gene=geneB;product=Transcriptional regulator
contig1\tProdigal:2.60\tgene\t900\t1200\t.\t-\t0\tID=geneC;locus_tag=SCO0003;gene=geneC;product=ABC transporter
contig1\tProdigal:2.60\tCDS\t900\t1200\t.\t-\t0\tID=cdsC;Parent=geneC;locus_tag=SCO0003;gene=geneC;product=ABC transporter
contig2\tProdigal:2.60\tgene\t100\t500\t.\t+\t0\tID=geneD;locus_tag=SCO0004;gene=geneD;product=Replication protein
contig2\tProdigal:2.60\tCDS\t100\t500\t.\t+\t0\tID=cdsD;Parent=geneD;locus_tag=SCO0004;gene=geneD;product=Replication protein
"""


@pytest.fixture
def tmp_gff(tmp_path: Path, sample_gff_content: str) -> Path:
    """Create a temporary GFF3 file for testing."""
    gff_file = tmp_path / "test.gff"
    gff_file.write_text(sample_gff_content)
    return gff_file


@pytest.fixture
def sample_features() -> list:
    """Sample features for testing."""
    from actinoedit.core.models import GeneFeature

    return [
        GeneFeature(
            contig="contig1", start=1, end=300, strand="+",
            locus_tag="SCO0001", gene_name="geneA", product="Hypothetical protein"
        ),
        GeneFeature(
            contig="contig1", start=400, end=800, strand="+",
            locus_tag="SCO0002", gene_name="geneB", product="Transcriptional regulator"
        ),
        GeneFeature(
            contig="contig1", start=900, end=1200, strand="-",
            locus_tag="SCO0003", gene_name="geneC", product="ABC transporter"
        ),
        GeneFeature(
            contig="contig2", start=100, end=500, strand="+",
            locus_tag="SCO0004", gene_name="geneD", product="Replication protein"
        ),
    ]


class TestParseGff:
    """Tests for parse_gff function."""

    def test_parse_gff_file(self, tmp_gff: Path) -> None:
        """Test parsing GFF3 file."""
        features = parse_gff(tmp_gff)
        # Should extract both genes and CDS features
        assert len(features) == 8

    def test_parse_gff_features(self, tmp_gff: Path) -> None:
        """Test parsed features content."""
        features = parse_gff(tmp_gff)
        gene_a = find_by_locus_tag(features, "SCO0001")
        assert gene_a is not None
        assert gene_a.gene_name == "geneA"
        assert gene_a.product == "Hypothetical protein"
        assert gene_a.start == 1
        assert gene_a.end == 300
        assert gene_a.strand == "+"

    def test_parse_gff_multi_contig(self, tmp_gff: Path) -> None:
        """Test parsing multi-contig GFF3."""
        features = parse_gff(tmp_gff)
        contigs = get_unique_contigs(features)
        assert len(contigs) == 2
        assert "contig1" in contigs
        assert "contig2" in contigs

    def test_parse_gff_file_not_found(self) -> None:
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_gff("nonexistent.gff")


class TestParseGffString:
    """Tests for parse_gff_string function."""

    def test_parse_gff_string(self, sample_gff_content: str) -> None:
        """Test parsing GFF3 string."""
        features = parse_gff_string(sample_gff_content)
        # Should extract both genes and CDS features
        assert len(features) == 8

    def test_parse_gff_string_with_fasta(self) -> None:
        """Test parsing GFF3 string with FASTA section."""
        gff_content = """##gff-version 3
contig1\tProdigal\tgene\t1\t300\t.\t+\t0\tID=geneA;locus_tag=SCO0001
##FASTA
>contig1
ATCGATCGATCG
"""
        features = parse_gff_string(gff_content)
        assert len(features) == 1


class TestFindByLocusTag:
    """Tests for find_by_locus_tag function."""

    def test_find_existing(self, sample_features: list) -> None:
        """Test finding existing locus tag."""
        gene = find_by_locus_tag(sample_features, "SCO0001")
        assert gene is not None
        assert gene.gene_name == "geneA"

    def test_find_nonexistent(self, sample_features: list) -> None:
        """Test finding nonexistent locus tag."""
        gene = find_by_locus_tag(sample_features, "NONEXISTENT")
        assert gene is None


class TestFindByGeneName:
    """Tests for find_by_gene_name function."""

    def test_find_existing(self, sample_features: list) -> None:
        """Test finding existing gene name."""
        genes = find_by_gene_name(sample_features, "geneA")
        assert len(genes) == 1
        assert genes[0].locus_tag == "SCO0001"

    def test_find_nonexistent(self, sample_features: list) -> None:
        """Test finding nonexistent gene name."""
        genes = find_by_gene_name(sample_features, "nonexistent")
        assert len(genes) == 0


class TestFindFeaturesInRegion:
    """Tests for find_features_in_region function."""

    def test_find_in_region(self, sample_features: list) -> None:
        """Test finding features in region."""
        genes = find_features_in_region(sample_features, "contig1", 1, 500)
        assert len(genes) == 2  # SCO0001 and SCO0002

    def test_find_in_region_no_overlap(self, sample_features: list) -> None:
        """Test finding features in region with no overlap."""
        genes = find_features_in_region(sample_features, "contig1", 2000, 3000)
        assert len(genes) == 0

    def test_find_in_region_wrong_contig(self, sample_features: list) -> None:
        """Test finding features in region on wrong contig."""
        genes = find_features_in_region(sample_features, "contig3", 1, 1000)
        assert len(genes) == 0


class TestFindGenesByContig:
    """Tests for find_genes_by_contig function."""

    def test_find_by_contig(self, sample_features: list) -> None:
        """Test finding genes by contig."""
        genes = find_genes_by_contig(sample_features, "contig1")
        assert len(genes) == 3

    def test_find_by_contig_empty(self, sample_features: list) -> None:
        """Test finding genes by nonexistent contig."""
        genes = find_genes_by_contig(sample_features, "contig3")
        assert len(genes) == 0


class TestGetUniqueContigs:
    """Tests for get_unique_contigs function."""

    def test_get_contigs(self, sample_features: list) -> None:
        """Test getting unique contigs."""
        contigs = get_unique_contigs(sample_features)
        assert len(contigs) == 2
        assert contigs == ["contig1", "contig2"]


class TestFilterByFeatureType:
    """Tests for filter_by_feature_type function."""

    def test_filter_genes(self, sample_features: list) -> None:
        """Test filtering by gene type."""
        genes = filter_by_feature_type(sample_features, "gene")
        assert len(genes) == 4

    def test_filter_cds(self, sample_features: list) -> None:
        """Test filtering by CDS type."""
        cds = filter_by_feature_type(sample_features, "CDS")
        assert len(cds) == 0  # sample_features are all gene type


class TestGetCdsFeatures:
    """Tests for get_cds_features function."""

    def test_get_cds(self, sample_features: list) -> None:
        """Test getting CDS features."""
        cds = get_cds_features(sample_features)
        assert len(cds) == 0  # sample_features are all gene type


class TestGetGeneFeatures:
    """Tests for get_gene_features function."""

    def test_get_genes(self, sample_features: list) -> None:
        """Test getting gene features."""
        genes = get_gene_features(sample_features)
        assert len(genes) == 4
