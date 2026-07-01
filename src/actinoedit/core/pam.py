"""PAM (Protospacer Adjacent Motif) pattern matching for ActinoEdit.

This module provides functions for matching PAM sequences using IUPAC DNA ambiguity codes.
Supports common PAM patterns like NGG, NGA, NAG, TTTV, NNGRRT for various nucleases.
"""

from __future__ import annotations

import re
from re import Pattern

# IUPAC ambiguity code to regex mapping
IUPAC_TO_REGEX: dict[str, str] = {
    "A": "A",
    "C": "C",
    "G": "G",
    "T": "T",
    "R": "[AG]",      # puRine (A or G)
    "Y": "[CT]",      # pYrimidine (C or T)
    "S": "[GC]",      # Strong (G or C)
    "W": "[AT]",      # Weak (A or T)
    "K": "[GT]",      # Keto (G or T)
    "M": "[AC]",      # aMino (A or C)
    "B": "[CGT]",     # not A
    "D": "[AGT]",     # not C
    "H": "[ACT]",     # not G
    "V": "[ACG]",     # not T
    "N": "[ACGT]",    # aNy
}

# Common PAM patterns for different nucleases
COMMON_PAMS: dict[str, dict[str, str | int]] = {
    "SpCas9": {
        "pam": "NGG",
        "description": "Streptococcus pyogenes Cas9 (most common)",
        "cut_offset": 3,  # bp upstream of PAM
    },
    "SpCas9-NGA": {
        "pam": "NGA",
        "description": "SpCas9 variant with expanded PAM",
        "cut_offset": 3,
    },
    "SpCas9-NAG": {
        "pam": "NAG",
        "description": "SpCas9 with NAG PAM (lower efficiency)",
        "cut_offset": 3,
    },
    "SaCas9": {
        "pam": "NNGRRT",
        "description": "Staphylococcus aureus Cas9",
        "cut_offset": 3,
    },
    "Cas12a": {
        "pam": "TTTV",
        "description": "Cas12a (Cpf1) - TTTV PAM",
        "cut_offset": 18,  # 18 bp downstream of PAM
    },
    "Cas12b": {
        "pam": "TTN",
        "description": "Cas12b",
        "cut_offset": 18,
    },
}


def compile_pam(pam_pattern: str) -> Pattern[str]:
    """Compile a PAM pattern to a regular expression.

    Converts IUPAC DNA ambiguity codes to regex character classes.

    Args:
        pam_pattern: PAM pattern using IUPAC codes (e.g., "NGG", "TTTV").

    Returns:
        Compiled regex pattern.

    Raises:
        ValueError: If the pattern contains invalid IUPAC characters.

    Examples:
        >>> pattern = compile_pam("NGG")
        >>> pattern.match("AGG")
        <re.Match object; span=(0, 3), match='AGG'>
        >>> pattern.match("NCC") is None
        True
    """
    pam_pattern = pam_pattern.upper()
    regex_parts: list[str] = []

    for char in pam_pattern:
        if char not in IUPAC_TO_REGEX:
            raise ValueError(
                f"Invalid IUPAC character in PAM pattern: '{char}'. "
                f"Valid characters: {', '.join(sorted(IUPAC_TO_REGEX.keys()))}"
            )
        regex_parts.append(IUPAC_TO_REGEX[char])

    regex_str = "".join(regex_parts)
    return re.compile(regex_str)


def is_pam_match(sequence: str, pam_pattern: str) -> bool:
    """Check if a sequence matches a PAM pattern.

    Args:
        sequence: DNA sequence to check.
        pam_pattern: PAM pattern using IUPAC codes.

    Returns:
        True if the sequence matches the PAM pattern.

    Examples:
        >>> is_pam_match("AGG", "NGG")
        True
        >>> is_pam_match("ACC", "NGG")
        False
        >>> is_pam_match("TTTA", "TTTV")
        True
    """
    sequence = sequence.upper()
    pam_pattern = pam_pattern.upper()

    if len(sequence) != len(pam_pattern):
        return False

    pattern = compile_pam(pam_pattern)
    return pattern.fullmatch(sequence) is not None


def find_pam_matches(
    sequence: str,
    pam_pattern: str,
) -> list[tuple[int, str]]:
    """Find all PAM matches in a sequence.

    Args:
        sequence: DNA sequence to search.
        pam_pattern: PAM pattern using IUPAC codes.

    Returns:
        List of (position_0based, matched_sequence) tuples.

    Examples:
        >>> matches = find_pam_matches("ATCGAGGATCGAGG", "NGG")
        >>> len(matches)
        2
    """
    sequence = sequence.upper()
    pam_pattern = pam_pattern.upper()
    pattern = compile_pam(pam_pattern)

    matches: list[tuple[int, str]] = []
    for match in pattern.finditer(sequence):
        matches.append((match.start(), match.group()))

    return matches


def get_pam_regex(pam_pattern: str) -> str:
    """Get the regex string for a PAM pattern.

    Args:
        pam_pattern: PAM pattern using IUPAC codes.

    Returns:
        Regex string.
    """
    pam_pattern = pam_pattern.upper()
    regex_parts: list[str] = []

    for char in pam_pattern:
        if char not in IUPAC_TO_REGEX:
            raise ValueError(f"Invalid IUPAC character: '{char}'")
        regex_parts.append(IUPAC_TO_REGEX[char])

    return "".join(regex_parts)


def get_nuclease_info(nuclease_name: str) -> dict[str, str | int] | None:
    """Get information about a nuclease.

    Args:
        nuclease_name: Nuclease name (e.g., "SpCas9", "Cas12a").

    Returns:
        Dictionary with nuclease info, or None if not found.
    """
    return COMMON_PAMS.get(nuclease_name)


def list_nucleases() -> list[str]:
    """List available nucleases.

    Returns:
        List of nuclease names.
    """
    return list(COMMON_PAMS.keys())


def get_default_pam(nuclease_name: str) -> str | None:
    """Get the default PAM for a nuclease.

    Args:
        nuclease_name: Nuclease name.

    Returns:
        PAM pattern, or None if nuclease not found.
    """
    info = COMMON_PAMS.get(nuclease_name)
    if info is not None:
        return str(info.get("pam"))
    return None
