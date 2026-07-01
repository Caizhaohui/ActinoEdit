"""Tests for sequence utility functions."""

import pytest

from actinoedit.core.sequence import (
    calculate_gc_content,
    complement,
    count_homopolymer_runs,
    generate_stable_id,
    has_homopolymer_run,
    normalize_sequence,
    reverse_complement,
    validate_dna_sequence,
)


class TestComplement:
    """Tests for complement function."""

    def test_basic_complement(self) -> None:
        """Test basic complement."""
        assert complement("ATCG") == "TAGC"

    def test_complement_with_ambiguous(self) -> None:
        """Test complement with ambiguous bases."""
        # R(A/G) -> Y(C/T), Y(C/T) -> R(A/G), S(G/C) -> S(G/C), W(A/T) -> W(A/T)
        assert complement("RYSW") == "YRSW"

    def test_complement_lowercase(self) -> None:
        """Test complement with lowercase input."""
        assert complement("atcg") == "TAGC"

    def test_complement_invalid_char(self) -> None:
        """Test complement with invalid character."""
        with pytest.raises(ValueError, match="Invalid DNA character"):
            complement("ATCGX")


class TestReverseComplement:
    """Tests for reverse_complement function."""

    def test_basic_reverse_complement(self) -> None:
        """Test basic reverse complement."""
        assert reverse_complement("ATCG") == "CGAT"

    def test_reverse_complement_palindrome(self) -> None:
        """Test reverse complement of palindrome."""
        assert reverse_complement("AATT") == "AATT"

    def test_reverse_complement_single(self) -> None:
        """Test reverse complement of single base."""
        assert reverse_complement("A") == "T"

    def test_reverse_complement_lowercase(self) -> None:
        """Test reverse complement with lowercase."""
        assert reverse_complement("atcg") == "CGAT"


class TestCalculateGcContent:
    """Tests for calculate_gc_content function."""

    def test_all_gc(self) -> None:
        """Test all GC content."""
        assert calculate_gc_content("GCGC") == 1.0

    def test_no_gc(self) -> None:
        """Test no GC content."""
        assert calculate_gc_content("ATAT") == 0.0

    def test_mixed(self) -> None:
        """Test mixed GC content."""
        assert calculate_gc_content("ATCG") == 0.5

    def test_lowercase(self) -> None:
        """Test lowercase input."""
        assert calculate_gc_content("atcg") == 0.5

    def test_empty_raises(self) -> None:
        """Test empty sequence raises error."""
        with pytest.raises(ValueError, match="empty"):
            calculate_gc_content("")

    def test_single_gc(self) -> None:
        """Test single GC base."""
        assert calculate_gc_content("G") == 1.0

    def test_single_at(self) -> None:
        """Test single AT base."""
        assert calculate_gc_content("A") == 0.0


class TestCountHomopolymerRuns:
    """Tests for count_homopolymer_runs function."""

    def test_no_runs(self) -> None:
        """Test sequence with no homopolymer runs."""
        assert count_homopolymer_runs("ATCGATCG") == []

    def test_single_run(self) -> None:
        """Test sequence with single homopolymer run."""
        runs = count_homopolymer_runs("AAAACGCG")
        assert len(runs) == 1
        assert runs[0] == ("A", 0, 4)

    def test_multiple_runs(self) -> None:
        """Test sequence with multiple homopolymer runs."""
        runs = count_homopolymer_runs("AAAACCCCG")
        assert len(runs) == 2
        assert runs[0] == ("A", 0, 4)
        assert runs[1] == ("C", 4, 4)

    def test_min_length(self) -> None:
        """Test minimum length filter."""
        runs = count_homopolymer_runs("AAACGCG", min_length=4)
        assert len(runs) == 0

    def test_empty_sequence(self) -> None:
        """Test empty sequence."""
        assert count_homopolymer_runs("") == []

    def test_at_end(self) -> None:
        """Test homopolymer run at end of sequence."""
        runs = count_homopolymer_runs("CGCGAAAA")
        assert len(runs) == 1
        assert runs[0] == ("A", 4, 4)


class TestHasHomopolymerRun:
    """Tests for has_homopolymer_run function."""

    def test_has_run(self) -> None:
        """Test sequence with homopolymer run."""
        assert has_homopolymer_run("AAAACGCG") is True

    def test_no_run(self) -> None:
        """Test sequence without homopolymer run."""
        assert has_homopolymer_run("ATCGATCG") is False

    def test_custom_min_length(self) -> None:
        """Test custom minimum length."""
        assert has_homopolymer_run("AAACGCG", min_length=4) is False
        assert has_homopolymer_run("AAACGCG", min_length=3) is True


class TestValidateDnaSequence:
    """Tests for validate_dna_sequence function."""

    def test_valid_sequence(self) -> None:
        """Test valid DNA sequence."""
        is_valid, error = validate_dna_sequence("ATCG")
        assert is_valid is True
        assert error is None

    def test_valid_ambiguous(self) -> None:
        """Test valid ambiguous DNA sequence."""
        is_valid, error = validate_dna_sequence("RYSWKMBDHVN")
        assert is_valid is True
        assert error is None

    def test_invalid_character(self) -> None:
        """Test invalid character."""
        is_valid, error = validate_dna_sequence("ATCGX")
        assert is_valid is False
        assert "Invalid" in error

    def test_empty_sequence(self) -> None:
        """Test empty sequence."""
        is_valid, error = validate_dna_sequence("")
        assert is_valid is False
        assert "empty" in error.lower()


class TestNormalizeSequence:
    """Tests for normalize_sequence function."""

    def test_uppercase(self) -> None:
        """Test uppercase normalization."""
        assert normalize_sequence("atcg") == "ATCG"

    def test_already_uppercase(self) -> None:
        """Test already uppercase."""
        assert normalize_sequence("ATCG") == "ATCG"

    def test_invalid_raises(self) -> None:
        """Test invalid character raises error."""
        with pytest.raises(ValueError):
            normalize_sequence("ATCGX")


class TestGenerateStableId:
    """Tests for generate_stable_id function."""

    def test_basic_id(self) -> None:
        """Test basic ID generation."""
        result = generate_stable_id("guide", "contig1", 100, 200, "+")
        assert result == "guide_contig1_100_200_+"

    def test_different_prefix(self) -> None:
        """Test different prefix."""
        result = generate_stable_id("target", "contig1", 100, 200, "-")
        assert result == "target_contig1_100_200_-"
