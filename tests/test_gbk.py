"""Tests for GenBank parser."""

from pathlib import Path

import pytest

# Skip GenBank tests if Biopython is not installed
pytest.importorskip("Bio")

from actinoedit.io.gbk import (
    find_by_gene_name,
    find_by_locus_tag,
    find_features_in_region,
    parse_gbk,
    parse_gbk_string,
)


@pytest.fixture
def sample_gbk_content() -> str:
    """Sample GenBank content for testing."""
    return """LOCUS       contig1                 620 bp    DNA     linear   BCT 01-JAN-2024
DEFINITION  Streptomyces coelicolor A3(2) chromosome, complete sequence.
ACCESSION   .
VERSION     .
KEYWORDS    .
SOURCE      Streptomyces coelicolor A3(2)
  ORGANISM  Streptomyces coelicolor A3(2)
            Bacteria; Actinobacteria; Streptomycetales; Streptomycetaceae;
            Streptomyces.
FEATURES             Location/Qualifiers
     source          1..620
                     /organism="Streptomyces coelicolor A3(2)"
                     /mol_type="genomic DNA"
     gene            1..300
                     /locus_tag="SCO0001"
                     /gene="geneA"
                     /product="Hypothetical protein"
     CDS             1..300
                     /locus_tag="SCO0001"
                     /gene="geneA"
                     /product="Hypothetical protein"
                     /transl_table=11
     gene            400..800
                     /locus_tag="SCO0002"
                     /gene="geneB"
                     /product="Transcriptional regulator"
     CDS             400..800
                     /locus_tag="SCO0002"
                     /gene="geneB"
                     /product="Transcriptional regulator"
                     /transl_table=11
ORIGIN
        1 ttgacgtcaa tcgatcgatc gatcgatcga tcgatcgatc gatcgatcga tcgatcgatc
       61 gatcgatcga tcgatcgatc gatcgatcga tcgatcgatc gatcgatcga tcgatcgatc
//
"""


@pytest.fixture
def tmp_gbk(tmp_path: Path, sample_gbk_content: str) -> Path:
    """Create a temporary GenBank file for testing."""
    gbk_file = tmp_path / "test.gbk"
    gbk_file.write_text(sample_gbk_content)
    return gbk_file


class TestParseGbk:
    """Tests for parse_gbk function."""

    def test_parse_gbk_file(self, tmp_gbk: Path) -> None:
        """Test parsing GenBank file."""
        features = parse_gbk(tmp_gbk)
        # Should have 2 genes and 2 CDS = 4 features
        assert len(features) == 4

    def test_parse_gbk_features(self, tmp_gbk: Path) -> None:
        """Test parsed features content."""
        features = parse_gbk(tmp_gbk)
        gene_a = find_by_locus_tag(features, "SCO0001")
        assert gene_a is not None
        assert gene_a.gene_name == "geneA"
        assert gene_a.product == "Hypothetical protein"
        assert gene_a.start == 1
        assert gene_a.end == 300
        assert gene_a.strand == "+"

    def test_parse_gbk_file_not_found(self) -> None:
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_gbk("nonexistent.gbk")


class TestParseGbkString:
    """Tests for parse_gbk_string function."""

    def test_parse_gbk_string(self, sample_gbk_content: str) -> None:
        """Test parsing GenBank string."""
        features = parse_gbk_string(sample_gbk_content)
        assert len(features) == 4


class TestFindByLocusTag:
    """Tests for find_by_locus_tag function."""

    def test_find_existing(self, tmp_gbk: Path) -> None:
        """Test finding existing locus tag."""
        features = parse_gbk(tmp_gbk)
        gene = find_by_locus_tag(features, "SCO0001")
        assert gene is not None
        assert gene.gene_name == "geneA"

    def test_find_nonexistent(self, tmp_gbk: Path) -> None:
        """Test finding nonexistent locus tag."""
        features = parse_gbk(tmp_gbk)
        gene = find_by_locus_tag(features, "NONEXISTENT")
        assert gene is None


class TestFindByGeneName:
    """Tests for find_by_gene_name function."""

    def test_find_existing(self, tmp_gbk: Path) -> None:
        """Test finding existing gene name."""
        features = parse_gbk(tmp_gbk)
        genes = find_by_gene_name(features, "geneA")
        assert len(genes) == 2  # gene and CDS

    def test_find_nonexistent(self, tmp_gbk: Path) -> None:
        """Test finding nonexistent gene name."""
        features = parse_gbk(tmp_gbk)
        genes = find_by_gene_name(features, "nonexistent")
        assert len(genes) == 0


class TestFindFeaturesInRegion:
    """Tests for find_features_in_region function."""

    def test_find_in_region(self, tmp_gbk: Path) -> None:
        """Test finding features in region."""
        features = parse_gbk(tmp_gbk)
        # Get the actual contig name from the first feature
        contig_name = features[0].contig
        genes = find_features_in_region(features, contig_name, 1, 500)
        assert len(genes) == 4  # geneA, cdsA, geneB, cdsB

    def test_find_in_region_no_overlap(self, tmp_gbk: Path) -> None:
        """Test finding features in region with no overlap."""
        features = parse_gbk(tmp_gbk)
        genes = find_features_in_region(features, "contig1", 900, 1000)
        assert len(genes) == 0
