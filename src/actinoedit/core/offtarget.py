"""Off-target search module for ActinoEdit.

This module provides functions for searching off-target sites across the genome.
Supports configurable mismatch tolerance and strand searching.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from actinoedit.core.models import Contig, GuideCandidate, OffTargetHit

if TYPE_CHECKING:
    from actinoedit.core.offtarget_index import GenomeOffTargetIndex


def search_offtargets(
    guide: GuideCandidate,
    contigs: dict[str, Contig],
    max_mismatches: int = 3,
    ignore_on_target: bool = True,
    genome_index: GenomeOffTargetIndex | None = None,
) -> list[OffTargetHit]:
    """Search for off-target sites across the genome.

    Args:
        guide: GuideCandidate object to search for.
        contigs: Dictionary of Contig objects (genome).
        max_mismatches: Maximum number of mismatches to allow.
        ignore_on_target: If True, exclude the on-target site from results.

    Returns:
        List of OffTargetHit objects.

    Examples:
        >>> contigs = parse_fasta("genome.fasta")
        >>> guides = scan_guides(contigs["contig1"], target)
        >>> hits = search_offtargets(guides[0], contigs, max_mismatches=3)
        >>> print(len(hits))
        5
    """
    if genome_index is not None:
        return genome_index.search_guide(
            guide,
            max_mismatches=max_mismatches,
            ignore_on_target=ignore_on_target,
        )

    hits: list[OffTargetHit] = []
    spacer = guide.spacer.upper()
    spacer_len = len(spacer)

    for contig_name, contig in contigs.items():
        sequence = contig.sequence

        # Search forward strand
        hits.extend(
            _search_strand(
                guide_id=guide.guide_id,
                contig_name=contig_name,
                sequence=sequence,
                spacer=spacer,
                spacer_len=spacer_len,
                strand="+",
                max_mismatches=max_mismatches,
            )
        )

        # Search reverse strand
        from actinoedit.core.sequence import reverse_complement
        rc_sequence = reverse_complement(sequence)
        hits.extend(
            _search_strand(
                guide_id=guide.guide_id,
                contig_name=contig_name,
                sequence=rc_sequence,
                spacer=spacer,
                spacer_len=spacer_len,
                strand="-",
                max_mismatches=max_mismatches,
            )
        )

    # Remove on-target if requested
    if ignore_on_target:
        hits = [
            h for h in hits
            if not (h.contig == guide.contig and h.start == guide.start and h.mismatch_count == 0)
        ]

    return hits


def _search_strand(
    guide_id: str,
    contig_name: str,
    sequence: str,
    spacer: str,
    spacer_len: int,
    strand: str,
    max_mismatches: int,
) -> list[OffTargetHit]:
    """Search one strand for off-target sites.

    Args:
        guide_id: Guide RNA identifier.
        contig_name: Contig name.
        sequence: DNA sequence to search.
        spacer: Spacer sequence.
        spacer_len: Length of spacer.
        strand: Strand ('+' or '-').
        max_mismatches: Maximum mismatches.

    Returns:
        List of OffTargetHit objects.
    """
    hits: list[OffTargetHit] = []
    seq_len = len(sequence)

    for i in range(seq_len - spacer_len + 1):
        window = sequence[i:i + spacer_len]
        mismatches = _count_mismatches(spacer, window)

        if mismatches <= max_mismatches:
            # Convert to 1-based coordinates
            start_1based = i + 1
            end_1based = i + spacer_len

            # Find mismatch positions
            mismatch_positions = _get_mismatch_positions(spacer, window)

            hits.append(
                OffTargetHit(
                    guide_id=guide_id,
                    contig=contig_name,
                    start=start_1based,
                    end=end_1based,
                    strand=strand,
                    sequence=window,
                    mismatch_count=mismatches,
                    mismatch_positions=mismatch_positions,
                )
            )

    return hits


def _count_mismatches(seq1: str, seq2: str) -> int:
    """Count mismatches between two sequences.

    Args:
        seq1: First sequence.
        seq2: Second sequence.

    Returns:
        Number of mismatches.
    """
    return sum(1 for a, b in zip(seq1, seq2, strict=True) if a != b)


def _get_mismatch_positions(seq1: str, seq2: str) -> list[int]:
    """Get positions where two sequences differ.

    Args:
        seq1: First sequence.
        seq2: Second sequence.

    Returns:
        List of mismatch positions (0-based).
    """
    return [i for i, (a, b) in enumerate(zip(seq1, seq2, strict=True)) if a != b]


def count_offtargets_by_mismatch(
    hits: list[OffTargetHit],
    max_mismatches: int = 3,
) -> dict[int, int]:
    """Count off-target hits by mismatch number.

    Args:
        hits: List of OffTargetHit objects.
        max_mismatches: Maximum mismatches to count.

    Returns:
        Dictionary mapping mismatch count to number of hits.
    """
    counts: dict[int, int] = {i: 0 for i in range(max_mismatches + 1)}

    for hit in hits:
        if hit.mismatch_count <= max_mismatches:
            counts[hit.mismatch_count] += 1

    return counts


def filter_offtargets(
    hits: list[OffTargetHit],
    max_mismatches: int = 3,
    exclude_contigs: list[str] | None = None,
) -> list[OffTargetHit]:
    """Filter off-target hits.

    Args:
        hits: List of OffTargetHit objects.
        max_mismatches: Maximum mismatches to include.
        exclude_contigs: Contigs to exclude (e.g., plasmids).

    Returns:
        Filtered list of OffTargetHit objects.
    """
    filtered = hits

    # Filter by mismatch count
    filtered = [h for h in filtered if h.mismatch_count <= max_mismatches]

    # Filter by contig
    if exclude_contigs:
        filtered = [h for h in filtered if h.contig not in exclude_contigs]

    return filtered


def get_offtarget_summary(
    guide: GuideCandidate,
    hits: list[OffTargetHit],
) -> dict:
    """Get summary of off-target analysis.

    Args:
        guide: GuideCandidate object.
        hits: List of OffTargetHit objects.

    Returns:
        Dictionary with summary information.
    """
    counts = count_offtargets_by_mismatch(hits)

    return {
        "guide_id": guide.guide_id,
        "spacer": guide.spacer,
        "total_hits": len(hits),
        "0_mismatch": counts.get(0, 0),
        "1_mismatch": counts.get(1, 0),
        "2_mismatch": counts.get(2, 0),
        "3_mismatch": counts.get(3, 0),
    }
