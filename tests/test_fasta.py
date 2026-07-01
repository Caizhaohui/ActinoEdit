"""Tests for FASTA parser."""

from pathlib import Path

import pytest

from actinoedit.core.models import Contig
from actinoedit.io.fasta import (
    count_contigs,
    extract_region,
    get_contig,
    get_contig_names,
    parse_fasta,
    parse_fasta_string,
    validate_fasta,
    write_fasta,
    write_fasta_string,
)


@pytest.fixture
def tmp_fasta(tmp_path: Path) -> Path:
    """Create a temporary FASTA file for testing."""
    fasta_content = """>contig1 Test sequence
ATCGATCGATCG
GCGCGCGCGC
>contig2 Another sequence
AAAATTTTCCCCGGGG
"""
    fasta_file = tmp_path / "test.fasta"
    fasta_file.write_text(fasta_content)
    return fasta_file


@pytest.fixture
def tmp_single_fasta(tmp_path: Path) -> Path:
    """Create a temporary single-contig FASTA file."""
    fasta_content = """>contig1 Test sequence
ATCGATCGATCG
GCGCGCGCGC
"""
    fasta_file = tmp_path / "single.fasta"
    fasta_file.write_text(fasta_content)
    return fasta_file


@pytest.fixture
def tmp_empty_fasta(tmp_path: Path) -> Path:
    """Create an empty temporary FASTA file."""
    fasta_file = tmp_path / "empty.fasta"
    fasta_file.write_text("")
    return fasta_file


class TestParseFasta:
    """Tests for parse_fasta function."""

    def test_parse_multi_contig(self, tmp_fasta: Path) -> None:
        """Test parsing multi-contig FASTA."""
        contigs = parse_fasta(tmp_fasta)
        assert len(contigs) == 2
        assert "contig1" in contigs
        assert "contig2" in contigs

    def test_parse_single_contig(self, tmp_single_fasta: Path) -> None:
        """Test parsing single-contig FASTA."""
        contigs = parse_fasta(tmp_single_fasta)
        assert len(contigs) == 1
        assert "contig1" in contigs

    def test_sequence_uppercase(self, tmp_fasta: Path) -> None:
        """Test that sequences are converted to uppercase."""
        contigs = parse_fasta(tmp_fasta)
        assert contigs["contig1"].sequence.isupper()
        assert contigs["contig2"].sequence.isupper()

    def test_sequence_length(self, tmp_fasta: Path) -> None:
        """Test sequence length calculation."""
        contigs = parse_fasta(tmp_fasta)
        # ATCGATCGATCG (12) + GCGCGCGCGC (10) = 22
        assert contigs["contig1"].length == 22

    def test_gc_content(self, tmp_fasta: Path) -> None:
        """Test GC content calculation."""
        contigs = parse_fasta(tmp_fasta)
        # contig1: ATCGATCGATCG (A=3,T=3,C=3,G=3) + GCGCGCGCGC (G=5,C=5)
        # total: 22 bases, G=8, C=8, GC = 16/22 ≈ 0.727
        assert abs(contigs["contig1"].gc_content - 16 / 22) < 0.01

    def test_file_not_found(self) -> None:
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_fasta("nonexistent.fasta")

    def test_empty_fasta(self, tmp_empty_fasta: Path) -> None:
        """Test ValueError for empty FASTA."""
        with pytest.raises(ValueError, match="empty"):
            parse_fasta(tmp_empty_fasta)

    def test_duplicate_contig_names(self, tmp_path: Path) -> None:
        """Test ValueError for duplicate contig names."""
        fasta_content = """>contig1
ATCG
>contig1
GCTA
"""
        dup_file = tmp_path / "dup.fasta"
        dup_file.write_text(fasta_content)
        with pytest.raises(ValueError, match="Duplicate"):
            parse_fasta(dup_file)

    def test_invalid_characters(self, tmp_path: Path) -> None:
        """Test ValueError for invalid DNA characters."""
        fasta_content = """>contig1
ATCGXYZ
"""
        invalid_file = tmp_path / "invalid.fasta"
        invalid_file.write_text(fasta_content)
        with pytest.raises(ValueError, match="Invalid"):
            parse_fasta(invalid_file)

    def test_empty_sequence(self, tmp_path: Path) -> None:
        """Test ValueError for empty sequence."""
        fasta_content = """>contig1
>contig2
ATCG
"""
        empty_seq_file = tmp_path / "empty_seq.fasta"
        empty_seq_file.write_text(fasta_content)
        with pytest.raises(ValueError, match="Empty sequence"):
            parse_fasta(empty_seq_file)

    def test_multiline_sequence(self, tmp_path: Path) -> None:
        """Test parsing multi-line sequences."""
        fasta_content = """>contig1
ATCGATCG
ATCGATCG
ATCGATCG
"""
        multiline_file = tmp_path / "multiline.fasta"
        multiline_file.write_text(fasta_content)
        contigs = parse_fasta(multiline_file)
        assert contigs["contig1"].length == 24

    def test_lowercase_input(self, tmp_path: Path) -> None:
        """Test parsing lowercase sequences."""
        fasta_content = """>contig1
atcgatcg
"""
        lowercase_file = tmp_path / "lowercase.fasta"
        lowercase_file.write_text(fasta_content)
        contigs = parse_fasta(lowercase_file)
        assert contigs["contig1"].sequence == "ATCGATCG"

    def test_with_description(self, tmp_path: Path) -> None:
        """Test parsing FASTA with description."""
        fasta_content = """>contig1 This is a description
ATCG
"""
        desc_file = tmp_path / "desc.fasta"
        desc_file.write_text(fasta_content)
        contigs = parse_fasta(desc_file)
        assert "contig1" in contigs
        assert contigs["contig1"].sequence == "ATCG"

    def test_ambiguous_bases(self, tmp_path: Path) -> None:
        """Test parsing sequences with ambiguous bases."""
        fasta_content = """>contig1
ATCGRYSWKMBDHVN
"""
        ambiguous_file = tmp_path / "ambiguous.fasta"
        ambiguous_file.write_text(fasta_content)
        contigs = parse_fasta(ambiguous_file)
        # A T C G R Y S W K M B D H V N = 15 characters
        assert contigs["contig1"].length == 15


class TestParseFastaString:
    """Tests for parse_fasta_string function."""

    def test_basic_string(self) -> None:
        """Test parsing basic FASTA string."""
        fasta = ">contig1\nATCGATCG\n>contig2\nGCGCGCGC\n"
        contigs = parse_fasta_string(fasta)
        assert len(contigs) == 2
        assert contigs["contig1"].sequence == "ATCGATCG"
        assert contigs["contig2"].sequence == "GCGCGCGC"

    def test_multiline_string(self) -> None:
        """Test parsing multi-line FASTA string."""
        fasta = ">contig1\nATCG\nATCG\nATCG\n"
        contigs = parse_fasta_string(fasta)
        assert contigs["contig1"].length == 12

    def test_empty_string(self) -> None:
        """Test parsing empty string."""
        with pytest.raises(ValueError, match="empty"):
            parse_fasta_string("")

    def test_no_header(self) -> None:
        """Test parsing string without header."""
        with pytest.raises(ValueError, match="empty"):
            parse_fasta_string("ATCGATCG")


class TestGetContig:
    """Tests for get_contig function."""

    def test_get_existing_contig(self, tmp_fasta: Path) -> None:
        """Test getting existing contig."""
        contig = get_contig(tmp_fasta, "contig1")
        assert contig.name == "contig1"
        assert contig.length == 22

    def test_get_nonexistent_contig(self, tmp_fasta: Path) -> None:
        """Test getting nonexistent contig."""
        with pytest.raises(ValueError, match="not found"):
            get_contig(tmp_fasta, "nonexistent")


class TestGetContigNames:
    """Tests for get_contig_names function."""

    def test_get_names(self, tmp_fasta: Path) -> None:
        """Test getting contig names."""
        names = get_contig_names(tmp_fasta)
        assert names == ["contig1", "contig2"]

    def test_single_contig(self, tmp_single_fasta: Path) -> None:
        """Test getting names from single contig."""
        names = get_contig_names(tmp_single_fasta)
        assert names == ["contig1"]


class TestCountContigs:
    """Tests for count_contigs function."""

    def test_count_multi(self, tmp_fasta: Path) -> None:
        """Test counting multiple contigs."""
        assert count_contigs(tmp_fasta) == 2

    def test_count_single(self, tmp_single_fasta: Path) -> None:
        """Test counting single contig."""
        assert count_contigs(tmp_single_fasta) == 1


class TestValidateFasta:
    """Tests for validate_fasta function."""

    def test_valid_fasta(self, tmp_fasta: Path) -> None:
        """Test validating valid FASTA."""
        is_valid, errors = validate_fasta(tmp_fasta)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_fasta(self, tmp_path: Path) -> None:
        """Test validating invalid FASTA."""
        fasta_content = """>contig1
ATCGXYZ
"""
        invalid_file = tmp_path / "invalid.fasta"
        invalid_file.write_text(fasta_content)
        is_valid, errors = validate_fasta(invalid_file)
        assert is_valid is False
        assert len(errors) > 0

    def test_nonexistent_file(self) -> None:
        """Test validating nonexistent file."""
        is_valid, errors = validate_fasta("nonexistent.fasta")
        assert is_valid is False
        assert len(errors) == 1


class TestWriteFasta:
    """Tests for write_fasta function."""

    def test_write_dict(self, tmp_path: Path) -> None:
        """Test writing contigs from dictionary."""
        contigs = {
            "contig1": Contig(name="contig1", sequence="ATCGATCG"),
            "contig2": Contig(name="contig2", sequence="GCGCGCGC"),
        }
        output_file = tmp_path / "output.fasta"
        write_fasta(contigs, output_file)

        # Read back and verify
        parsed = parse_fasta(output_file)
        assert len(parsed) == 2
        assert parsed["contig1"].sequence == "ATCGATCG"
        assert parsed["contig2"].sequence == "GCGCGCGC"

    def test_write_list(self, tmp_path: Path) -> None:
        """Test writing contigs from list."""
        contigs = [
            Contig(name="contig1", sequence="ATCGATCG"),
            Contig(name="contig2", sequence="GCGCGCGC"),
        ]
        output_file = tmp_path / "output.fasta"
        write_fasta(contigs, output_file)

        parsed = parse_fasta(output_file)
        assert len(parsed) == 2

    def test_write_line_width(self, tmp_path: Path) -> None:
        """Test writing with custom line width."""
        contigs = {"contig1": Contig(name="contig1", sequence="A" * 100)}
        output_file = tmp_path / "output.fasta"
        write_fasta(contigs, output_file, line_width=20)

        with open(output_file) as f:
            lines = f.readlines()

        # Header + 5 lines of 20 chars
        assert len(lines) == 6
        assert lines[0].strip() == ">contig1"
        assert len(lines[1].strip()) == 20


class TestWriteFastaString:
    """Tests for write_fasta_string function."""

    def test_write_string(self) -> None:
        """Test writing FASTA string."""
        contigs = {
            "contig1": Contig(name="contig1", sequence="ATCGATCG"),
            "contig2": Contig(name="contig2", sequence="GCGCGCGC"),
        }
        fasta_str = write_fasta_string(contigs)
        assert ">contig1" in fasta_str
        assert "ATCGATCG" in fasta_str
        assert ">contig2" in fasta_str
        assert "GCGCGCGC" in fasta_str

    def test_write_string_line_width(self) -> None:
        """Test writing FASTA string with custom line width."""
        contigs = {"contig1": Contig(name="contig1", sequence="A" * 100)}
        fasta_str = write_fasta_string(contigs, line_width=20)
        lines = fasta_str.strip().split("\n")
        assert len(lines) == 6  # Header + 5 lines


class TestExtractRegion:
    """Tests for extract_region function."""

    def test_extract_region(self, tmp_fasta: Path) -> None:
        """Test extracting a region."""
        region = extract_region(tmp_fasta, "contig1", 2, 5)
        assert region == "TCGA"

    def test_extract_region_out_of_range(self, tmp_fasta: Path) -> None:
        """Test extracting region out of range."""
        with pytest.raises(IndexError):
            extract_region(tmp_fasta, "contig1", 1, 100)

    def test_extract_region_nonexistent_contig(self, tmp_fasta: Path) -> None:
        """Test extracting from nonexistent contig."""
        with pytest.raises(ValueError, match="not found"):
            extract_region(tmp_fasta, "nonexistent", 1, 10)
