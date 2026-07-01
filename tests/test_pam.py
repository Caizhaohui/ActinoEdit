"""Tests for PAM pattern matching."""

import pytest

from actinoedit.core.pam import (
    compile_pam,
    find_pam_matches,
    get_default_pam,
    get_nuclease_info,
    get_pam_regex,
    is_pam_match,
    list_nucleases,
)


class TestCompilePam:
    """Tests for compile_pam function."""

    def test_basic_pam(self) -> None:
        """Test basic PAM compilation."""
        pattern = compile_pam("NGG")
        assert pattern is not None
        assert pattern.match("AGG") is not None
        assert pattern.match("CGG") is not None
        assert pattern.match("GGG") is not None
        assert pattern.match("TGG") is not None

    def test_pam_with_ambiguous(self) -> None:
        """Test PAM with ambiguous bases."""
        pattern = compile_pam("TTTV")
        assert pattern is not None
        assert pattern.match("TTTA") is not None
        assert pattern.match("TTTC") is not None
        assert pattern.match("TTTG") is not None
        assert pattern.match("TTTT") is None

    def test_complex_pam(self) -> None:
        """Test complex PAM pattern."""
        pattern = compile_pam("NNGRRT")
        assert pattern is not None
        # NNGRRT: N=[ACGT], G=G, R=[AG], R=[AG], T=T
        assert pattern.match("AAGAAT") is not None
        assert pattern.match("CCGAGT") is not None
        assert pattern.match("TTGCGT") is None  # C is not in [AG]

    def test_invalid_character(self) -> None:
        """Test invalid PAM character."""
        with pytest.raises(ValueError, match="Invalid IUPAC character"):
            compile_pam("NGX")

    def test_lowercase_input(self) -> None:
        """Test lowercase input."""
        pattern = compile_pam("ngg")
        assert pattern.match("AGG") is not None


class TestIsPamMatch:
    """Tests for is_pam_match function."""

    def test_match_ngg(self) -> None:
        """Test NGG PAM match."""
        assert is_pam_match("AGG", "NGG") is True
        assert is_pam_match("CGG", "NGG") is True
        assert is_pam_match("GGG", "NGG") is True
        assert is_pam_match("TGG", "NGG") is True

    def test_no_match_ngg(self) -> None:
        """Test NGG PAM non-match."""
        assert is_pam_match("ACC", "NGG") is False
        assert is_pam_match("AAA", "NGG") is False
        assert is_pam_match("NGG", "NGG") is False  # N is not a DNA base

    def test_match_tttv(self) -> None:
        """Test TTTV PAM match."""
        assert is_pam_match("TTTA", "TTTV") is True
        assert is_pam_match("TTTC", "TTTV") is True
        assert is_pam_match("TTTG", "TTTV") is True
        assert is_pam_match("TTTT", "TTTV") is False

    def test_length_mismatch(self) -> None:
        """Test length mismatch."""
        assert is_pam_match("AGG", "NG") is False
        assert is_pam_match("AG", "NGG") is False

    def test_lowercase_input(self) -> None:
        """Test lowercase input."""
        assert is_pam_match("agg", "NGG") is True


class TestFindPamMatches:
    """Tests for find_pam_matches function."""

    def test_find_single(self) -> None:
        """Test finding single PAM."""
        matches = find_pam_matches("ATCGAGG", "NGG")
        assert len(matches) == 1
        assert matches[0] == (4, "AGG")

    def test_find_multiple(self) -> None:
        """Test finding multiple PAMs."""
        matches = find_pam_matches("ATCGAGGATCGAGG", "NGG")
        assert len(matches) == 2
        assert matches[0] == (4, "AGG")
        assert matches[1] == (11, "AGG")

    def test_find_none(self) -> None:
        """Test finding no PAMs."""
        matches = find_pam_matches("ATCGATCG", "NGG")
        assert len(matches) == 0

    def test_find_tttv(self) -> None:
        """Test finding TTTV PAM."""
        matches = find_pam_matches("ATCGTTTAATCGTTTC", "TTTV")
        assert len(matches) == 2


class TestGetPamRegex:
    """Tests for get_pam_regex function."""

    def test_basic_regex(self) -> None:
        """Test basic regex generation."""
        regex = get_pam_regex("NGG")
        assert regex == "[ACGT]GG"

    def test_complex_regex(self) -> None:
        """Test complex regex generation."""
        regex = get_pam_regex("TTTV")
        assert regex == "TTT[ACG]"

    def test_invalid_character(self) -> None:
        """Test invalid character."""
        with pytest.raises(ValueError):
            get_pam_regex("NGX")


class TestGetNucleaseInfo:
    """Tests for get_nuclease_info function."""

    def test_spcas9(self) -> None:
        """Test SpCas9 info."""
        info = get_nuclease_info("SpCas9")
        assert info is not None
        assert info["pam"] == "NGG"
        assert info["cut_offset"] == 3

    def test_cas12a(self) -> None:
        """Test Cas12a info."""
        info = get_nuclease_info("Cas12a")
        assert info is not None
        assert info["pam"] == "TTTV"
        assert info["cut_offset"] == 18

    def test_unknown_nuclease(self) -> None:
        """Test unknown nuclease."""
        info = get_nuclease_info("Unknown")
        assert info is None


class TestListNucleases:
    """Tests for list_nucleases function."""

    def test_list(self) -> None:
        """Test listing nucleases."""
        nucleases = list_nucleases()
        assert len(nucleases) > 0
        assert "SpCas9" in nucleases
        assert "Cas12a" in nucleases


class TestGetDefaultPam:
    """Tests for get_default_pam function."""

    def test_spcas9(self) -> None:
        """Test SpCas9 default PAM."""
        pam = get_default_pam("SpCas9")
        assert pam == "NGG"

    def test_cas12a(self) -> None:
        """Test Cas12a default PAM."""
        pam = get_default_pam("Cas12a")
        assert pam == "TTTV"

    def test_unknown(self) -> None:
        """Test unknown nuclease."""
        pam = get_default_pam("Unknown")
        assert pam is None
