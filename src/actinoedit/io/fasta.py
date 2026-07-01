"""FASTA file parser for ActinoEdit.

This module provides functions for reading and writing FASTA format files.
Supports single and multi-contig FASTA files with IUPAC DNA characters.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TextIO

from actinoedit.core.models import Contig

# Regular expression for FASTA header
FASTA_HEADER_RE = re.compile(r"^>(\S+)(.*)$")


def parse_fasta(fasta_path: str | Path) -> dict[str, Contig]:
    """Parse a FASTA file and return a dictionary of Contig objects.

    Reads a FASTA file and creates Contig objects for each sequence.
    Sequences are normalized to uppercase and validated for IUPAC DNA characters.

    Args:
        fasta_path: Path to the FASTA file.

    Returns:
        Dictionary mapping contig names to Contig objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the FASTA file is empty, contains duplicate contig names,
                   empty sequences, or invalid DNA characters.

    Examples:
        >>> contigs = parse_fasta("genome.fasta")
        >>> print(contigs.keys())
        dict_keys(['contig1', 'contig2'])
        >>> print(contigs['contig1'].length)
        1000
    """
    fasta_path = Path(fasta_path)
    if not fasta_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    with open(fasta_path) as f:
        return _parse_fasta_stream(f)


def parse_fasta_string(fasta_string: str) -> dict[str, Contig]:
    """Parse a FASTA string and return a dictionary of Contig objects.

    Args:
        fasta_string: FASTA format string.

    Returns:
        Dictionary mapping contig names to Contig objects.

    Raises:
        ValueError: If the FASTA string is empty, contains duplicate contig names,
                   empty sequences, or invalid DNA characters.

    Examples:
        >>> fasta = ">contig1\\nATCGATCG\\n>contig2\\nGCGCGCGC"
        >>> contigs = parse_fasta_string(fasta)
        >>> len(contigs)
        2
    """
    from io import StringIO

    stream = StringIO(fasta_string)
    return _parse_fasta_stream(stream)


def _parse_fasta_stream(stream: TextIO) -> dict[str, Contig]:
    """Parse FASTA data from a text stream.

    Args:
        stream: Text stream to read FASTA data from.

    Returns:
        Dictionary mapping contig names to Contig objects.

    Raises:
        ValueError: If the FASTA data is empty, contains duplicate contig names,
                   empty sequences, or invalid DNA characters.
    """
    contigs: dict[str, Contig] = {}
    current_name: str | None = None
    current_sequence: list[str] = []

    for line in stream:
        line = line.strip()
        if not line:
            continue

        if line.startswith(">"):
            # Save previous contig
            if current_name is not None:
                _save_contig(contigs, current_name, current_sequence)

            # Parse header
            match = FASTA_HEADER_RE.match(line)
            current_name = match.group(1) if match else line[1:].strip()

            current_sequence = []
        else:
            # Validate characters before adding
            _validate_sequence_line(line)
            current_sequence.append(line)

    # Save last contig
    if current_name is not None:
        _save_contig(contigs, current_name, current_sequence)

    if not contigs:
        raise ValueError("FASTA file is empty")

    return contigs


def _save_contig(
    contigs: dict[str, Contig],
    name: str,
    sequence_lines: list[str],
) -> None:
    """Save a contig to the dictionary.

    Args:
        contigs: Dictionary to save contig to.
        name: Contig name.
        sequence_lines: List of sequence lines.

    Raises:
        ValueError: If the sequence is empty or the name is duplicate.
    """
    sequence = "".join(sequence_lines).upper()
    if not sequence:
        raise ValueError(f"Empty sequence for contig: {name}")
    if name in contigs:
        raise ValueError(f"Duplicate contig name: {name}")
    contigs[name] = Contig(name=name, sequence=sequence)


def _validate_sequence_line(line: str) -> None:
    """Validate a sequence line for valid DNA characters.

    Args:
        line: Sequence line to validate.

    Raises:
        ValueError: If the line contains invalid characters.
    """
    # Allow spaces and numbers (for formatted FASTA)
    cleaned = line.replace(" ", "").replace("\t", "")
    if not cleaned:
        return

    valid_chars = set("ACGTRYSWKMBDHVNacgtryswkmbdhvn0123456789")
    invalid = set(cleaned) - valid_chars
    if invalid:
        raise ValueError(f"Invalid characters in sequence: {invalid}")


def get_contig(fasta_path: str | Path, contig_name: str) -> Contig:
    """Get a single contig from a FASTA file.

    Args:
        fasta_path: Path to the FASTA file.
        contig_name: Name of the contig to retrieve.

    Returns:
        Contig object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the contig is not found.
    """
    contigs = parse_fasta(fasta_path)
    if contig_name not in contigs:
        raise ValueError(
            f"Contig '{contig_name}' not found. "
            f"Available contigs: {list(contigs.keys())}"
        )
    return contigs[contig_name]


def get_contig_names(fasta_path: str | Path) -> list[str]:
    """Get all contig names from a FASTA file.

    Args:
        fasta_path: Path to the FASTA file.

    Returns:
        List of contig names in file order.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    fasta_path = Path(fasta_path)
    if not fasta_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    names: list[str] = []
    with open(fasta_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                match = FASTA_HEADER_RE.match(line)
                if match:
                    names.append(match.group(1))
                else:
                    names.append(line[1:].strip())

    return names


def count_contigs(fasta_path: str | Path) -> int:
    """Count the number of contigs in a FASTA file.

    Args:
        fasta_path: Path to the FASTA file.

    Returns:
        Number of contigs.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return len(get_contig_names(fasta_path))


def validate_fasta(fasta_path: str | Path) -> tuple[bool, list[str]]:
    """Validate a FASTA file.

    Checks for:
    - File existence
    - Non-empty file
    - Valid DNA characters
    - No duplicate contig names
    - No empty sequences

    Args:
        fasta_path: Path to the FASTA file.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: list[str] = []
    fasta_path = Path(fasta_path)

    # Check file existence
    if not fasta_path.exists():
        return False, [f"File not found: {fasta_path}"]

    try:
        contigs = parse_fasta(fasta_path)
        # Additional validation
        for name, contig in contigs.items():
            is_valid, error = contig.validate()
            if not is_valid:
                errors.append(f"Contig '{name}': {error}")
    except ValueError as e:
        errors.append(str(e))

    return len(errors) == 0, errors


def write_fasta(
    contigs: dict[str, Contig] | list[Contig],
    output_path: str | Path,
    line_width: int = 60,
) -> None:
    """Write contigs to a FASTA file.

    Args:
        contigs: Dictionary or list of Contig objects.
        output_path: Path to output file.
        line_width: Maximum line width for sequences (default: 60).

    Raises:
        ValueError: If line_width is less than 1.
    """
    if line_width < 1:
        raise ValueError(f"Line width must be >= 1, got {line_width}")

    output_path = Path(output_path)

    # Convert list to dict if needed
    contig_dict = {c.name: c for c in contigs} if isinstance(contigs, list) else contigs

    with open(output_path, "w") as f:
        for name, contig in contig_dict.items():
            f.write(f">{name}\n")
            sequence = contig.sequence
            for i in range(0, len(sequence), line_width):
                f.write(sequence[i : i + line_width] + "\n")


def write_fasta_string(
    contigs: dict[str, Contig] | list[Contig],
    line_width: int = 60,
) -> str:
    """Convert contigs to FASTA format string.

    Args:
        contigs: Dictionary or list of Contig objects.
        line_width: Maximum line width for sequences (default: 60).

    Returns:
        FASTA format string.

    Raises:
        ValueError: If line_width is less than 1.
    """
    if line_width < 1:
        raise ValueError(f"Line width must be >= 1, got {line_width}")

    # Convert list to dict if needed
    contig_dict = {c.name: c for c in contigs} if isinstance(contigs, list) else contigs

    lines: list[str] = []
    for name, contig in contig_dict.items():
        lines.append(f">{name}")
        sequence = contig.sequence
        for i in range(0, len(sequence), line_width):
            lines.append(sequence[i : i + line_width])

    return "\n".join(lines) + "\n"


def extract_region(
    fasta_path: str | Path,
    contig_name: str,
    start: int,
    end: int,
) -> str:
    """Extract a region from a FASTA file.

    Args:
        fasta_path: Path to the FASTA file.
        contig_name: Name of the contig.
        start: Start position (1-based inclusive).
        end: End position (1-based inclusive).

    Returns:
        Extracted sequence string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the contig is not found or coordinates are invalid.
    """
    contig = get_contig(fasta_path, contig_name)
    return contig.get_subsequence(start, end)
