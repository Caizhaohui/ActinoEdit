"""Sequence utility functions for ActinoEdit."""

from __future__ import annotations

# IUPAC ambiguity code complement mapping
COMPLEMENT_TABLE: dict[str, str] = {
    "A": "T",
    "T": "A",
    "C": "G",
    "G": "C",
    "R": "Y",  # R = A/G, Y = C/T
    "Y": "R",
    "S": "S",  # S = G/C
    "W": "W",  # W = A/T
    "K": "M",  # K = G/T, M = A/C
    "M": "K",
    "B": "V",  # B = C/G/T, V = A/C/G
    "V": "B",
    "D": "H",  # D = A/G/T, H = A/C/T
    "H": "D",
    "N": "N",  # N = any
}

# Valid IUPAC DNA characters
VALID_DNA_CHARS: set[str] = set("ACGTRYSWKMBDHVN")

# Ambiguous bases (not A, C, G, T)
AMBIGUOUS_BASES: set[str] = set("RYSWKMBDHVN")


def complement(sequence: str) -> str:
    """Return the complement of a DNA sequence.

    Args:
        sequence: DNA sequence string.

    Returns:
        Complement sequence.

    Raises:
        ValueError: If sequence contains invalid characters.
    """
    sequence = sequence.upper()
    result: list[str] = []
    for char in sequence:
        if char not in COMPLEMENT_TABLE:
            raise ValueError(f"Invalid DNA character: {char}")
        result.append(COMPLEMENT_TABLE[char])
    return "".join(result)


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a DNA sequence.

    Args:
        sequence: DNA sequence string.

    Returns:
        Reverse complement sequence.

    Raises:
        ValueError: If sequence contains invalid characters.
    """
    return complement(sequence)[::-1]


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content of a DNA sequence.

    Args:
        sequence: DNA sequence string.

    Returns:
        GC content as a fraction (0.0 to 1.0).

    Raises:
        ValueError: If sequence is empty.
    """
    if not sequence:
        raise ValueError("Cannot calculate GC content of empty sequence")

    sequence = sequence.upper()
    gc_count = sequence.count("G") + sequence.count("C")
    return gc_count / len(sequence)


def count_homopolymer_runs(sequence: str, min_length: int = 4) -> list[tuple[str, int, int]]:
    """Find homopolymer runs in a DNA sequence.

    Args:
        sequence: DNA sequence string.
        min_length: Minimum length of a homopolymer run to report.

    Returns:
        List of (base, start_0based, length) tuples.
    """
    if not sequence:
        return []

    sequence = sequence.upper()
    runs: list[tuple[str, int, int]] = []
    current_base = sequence[0]
    current_start = 0
    current_length = 1

    for i in range(1, len(sequence)):
        if sequence[i] == current_base:
            current_length += 1
        else:
            if current_length >= min_length:
                runs.append((current_base, current_start, current_length))
            current_base = sequence[i]
            current_start = i
            current_length = 1

    # Check last run
    if current_length >= min_length:
        runs.append((current_base, current_start, current_length))

    return runs


def has_homopolymer_run(sequence: str, min_length: int = 4) -> bool:
    """Check if a sequence contains a homopolymer run.

    Args:
        sequence: DNA sequence string.
        min_length: Minimum length to consider as a homopolymer run.

    Returns:
        True if homopolymer run found.
    """
    return len(count_homopolymer_runs(sequence, min_length)) > 0


def validate_dna_sequence(sequence: str) -> tuple[bool, str | None]:
    """Validate a DNA sequence.

    Args:
        sequence: DNA sequence string.

    Returns:
        Tuple of (is_valid, error_message).
        error_message is None if valid.
    """
    if not sequence:
        return False, "Sequence is empty"

    sequence = sequence.upper()
    invalid_chars = set(sequence) - VALID_DNA_CHARS
    if invalid_chars:
        return False, f"Invalid DNA characters: {invalid_chars}"

    return True, None


def normalize_sequence(sequence: str) -> str:
    """Normalize a DNA sequence to uppercase.

    Args:
        sequence: DNA sequence string.

    Returns:
        Uppercase sequence.

    Raises:
        ValueError: If sequence contains invalid characters.
    """
    sequence = sequence.upper()
    is_valid, error = validate_dna_sequence(sequence)
    if not is_valid:
        raise ValueError(error)
    return sequence


def generate_stable_id(prefix: str, contig: str, start: int, end: int, strand: str) -> str:
    """Generate a stable ID for a genomic feature.

    Args:
        prefix: ID prefix (e.g., "guide", "target").
        contig: Contig name.
        start: Start position (1-based).
        end: End position (1-based).
        strand: Strand ('+' or '-').

    Returns:
        Stable ID string.
    """
    return f"{prefix}_{contig}_{start}_{end}_{strand}"
