"""Guide RNA scanner for ActinoEdit.

This module provides functions for scanning DNA sequences to find candidate guide RNAs.
Supports both forward and reverse strand scanning with configurable PAM patterns.
"""

from __future__ import annotations

from dataclasses import dataclass

from actinoedit.core.models import Contig, GuideCandidate, TargetRegion
from actinoedit.core.pam import is_pam_match
from actinoedit.core.sequence import (
    calculate_gc_content,
    generate_stable_id,
    reverse_complement,
)


@dataclass
class ScannerConfig:
    """Configuration for guide RNA scanning.

    Attributes:
        pam_pattern: PAM pattern (e.g., "NGG").
        spacer_length: Length of the spacer sequence.
        cut_offset: Cut site offset from PAM (bp upstream for Cas9).
        nuclease_name: Name of the nuclease.
    """

    pam_pattern: str = "NGG"
    spacer_length: int = 20
    cut_offset: int = 3  # bp upstream of PAM for SpCas9
    nuclease_name: str = "SpCas9"


def scan_guides(
    contig: Contig,
    target: TargetRegion,
    config: ScannerConfig | None = None,
) -> list[GuideCandidate]:
    """Scan for guide RNA candidates in a target region.

    Scans both forward and reverse strands for potential guide RNAs
    that match the specified PAM pattern.

    Args:
        contig: Contig object with sequence.
        target: Target region to scan.
        config: Scanner configuration (uses defaults if None).

    Returns:
        List of GuideCandidate objects.

    Raises:
        ValueError: If target region is invalid.

    Examples:
        >>> contigs = parse_fasta("genome.fasta")
        >>> target = TargetRegion(contig="contig1", start=100, end=500, strand="+")
        >>> guides = scan_guides(contigs["contig1"], target)
        >>> print(len(guides))
        5
    """
    if config is None:
        config = ScannerConfig()

    # Validate target region
    is_valid, error = target.validate()
    if not is_valid:
        raise ValueError(f"Invalid target region: {error}")

    # Get target sequence
    start_0based, end_halfopen = target.to_slice()
    if start_0based < 0 or end_halfopen > contig.length:
        raise ValueError(
            f"Target region ({target.start}, {target.end}) exceeds "
            f"contig length ({contig.length})"
        )

    guides: list[GuideCandidate] = []

    # Scan forward strand
    guides.extend(
        _scan_strand(
            contig=contig,
            target=target,
            config=config,
            strand="+",
        )
    )

    # Scan reverse strand
    guides.extend(
        _scan_strand(
            contig=contig,
            target=target,
            config=config,
            strand="-",
        )
    )

    return guides


def _scan_strand(
    contig: Contig,
    target: TargetRegion,
    config: ScannerConfig,
    strand: str,
) -> list[GuideCandidate]:
    """Scan one strand for guide RNA candidates.

    Args:
        contig: Contig object.
        target: Target region.
        config: Scanner configuration.
        strand: Strand to scan ('+' or '-').

    Returns:
        List of GuideCandidate objects.
    """
    guides: list[GuideCandidate] = []
    pam_len = len(config.pam_pattern)

    # Get the sequence to scan
    start_0based, end_halfopen = target.to_slice()

    if strand == "+":
        # For forward strand: scan 5' to 3'
        # Guide is upstream of PAM: [spacer][PAM]
        scan_start = start_0based
        scan_end = end_halfopen - config.spacer_length - pam_len + 1

        for pos in range(scan_start, scan_end):
            # Extract spacer
            spacer_start = pos
            spacer_end = pos + config.spacer_length
            spacer = contig.sequence[spacer_start:spacer_end]

            # Extract PAM (immediately after spacer)
            pam_start = spacer_end
            pam_end = pam_start + pam_len
            pam = contig.sequence[pam_start:pam_end]

            # Check PAM match
            if is_pam_match(pam, config.pam_pattern):
                # Calculate cut site (upstream of PAM)
                cut_site_0based = pam_start - config.cut_offset

                # Convert to 1-based coordinates
                guide_start_1based = spacer_start + 1
                guide_end_1based = spacer_end
                pam_start_1based = pam_start + 1
                pam_end_1based = pam_end
                cut_site_1based = cut_site_0based + 1

                guide_id = generate_stable_id(
                    "guide",
                    contig.name,
                    guide_start_1based,
                    guide_end_1based,
                    strand,
                )

                guides.append(
                    GuideCandidate(
                        guide_id=guide_id,
                        contig=contig.name,
                        spacer=spacer,
                        pam=pam,
                        start=guide_start_1based,
                        end=guide_end_1based,
                        strand=strand,
                        pam_start=pam_start_1based,
                        pam_end=pam_end_1based,
                        cut_site=cut_site_1based,
                        gc_content=calculate_gc_content(spacer),
                        target_label=target.label,
                    )
                )
    else:
        # For reverse strand: scan 3' to 5' on forward, but guide is on reverse
        # PAM is upstream of guide on reverse: [PAM_RC][spacer_RC]
        # On forward strand: [spacer][PAM] but we need reverse complement
        scan_start = start_0based + config.spacer_length + pam_len - 1
        scan_end = end_halfopen

        for pos in range(scan_start, scan_end):
            # On forward strand, PAM is at pos, spacer is upstream
            pam_start_fwd = pos
            pam_end_fwd = pos + pam_len
            pam_fwd = contig.sequence[pam_start_fwd:pam_end_fwd]

            # Check if PAM on forward strand matches (this is PAM on reverse)
            # We need to check reverse complement of PAM
            pam_rc = reverse_complement(pam_fwd)

            if is_pam_match(pam_rc, config.pam_pattern):
                # Spacer is upstream of PAM on forward strand
                spacer_start_fwd = pos - config.spacer_length
                spacer_end_fwd = pos
                spacer_fwd = contig.sequence[spacer_start_fwd:spacer_end_fwd]

                # Get reverse complement of spacer
                spacer = reverse_complement(spacer_fwd)

                # Cut site is downstream of PAM on reverse strand
                cut_site_0based = pam_end_fwd + config.cut_offset - 1

                # Convert to 1-based coordinates
                guide_start_1based = spacer_start_fwd + 1
                guide_end_1based = spacer_end_fwd
                pam_start_1based = pam_start_fwd + 1
                pam_end_1based = pam_end_fwd
                cut_site_1based = cut_site_0based + 1

                guide_id = generate_stable_id(
                    "guide",
                    contig.name,
                    guide_start_1based,
                    guide_end_1based,
                    strand,
                )

                guides.append(
                    GuideCandidate(
                        guide_id=guide_id,
                        contig=contig.name,
                        spacer=spacer,
                        pam=pam_rc,
                        start=guide_start_1based,
                        end=guide_end_1based,
                        strand=strand,
                        pam_start=pam_start_1based,
                        pam_end=pam_end_1based,
                        cut_site=cut_site_1based,
                        gc_content=calculate_gc_content(spacer),
                        target_label=target.label,
                    )
                )

    return guides


def scan_entire_contig(
    contig: Contig,
    config: ScannerConfig | None = None,
) -> list[GuideCandidate]:
    """Scan an entire contig for guide RNA candidates.

    Args:
        contig: Contig object.
        config: Scanner configuration.

    Returns:
        List of GuideCandidate objects.
    """
    if config is None:
        config = ScannerConfig()

    target = TargetRegion(
        contig=contig.name,
        start=1,
        end=contig.length,
        strand=".",
    )

    return scan_guides(contig, target, config)


def filter_guides_by_gc(
    guides: list[GuideCandidate],
    gc_min: float = 0.0,
    gc_max: float = 1.0,
) -> list[GuideCandidate]:
    """Filter guides by GC content.

    Args:
        guides: List of GuideCandidate objects.
        gc_min: Minimum GC content (0-1).
        gc_max: Maximum GC content (0-1).

    Returns:
        Filtered list of GuideCandidate objects.
    """
    return [g for g in guides if gc_min <= g.gc_content <= gc_max]


def sort_guides_by_gc(
    guides: list[GuideCandidate],
    reverse: bool = False,
) -> list[GuideCandidate]:
    """Sort guides by GC content.

    Args:
        guides: List of GuideCandidate objects.
        reverse: If True, sort in descending order.

    Returns:
        Sorted list of GuideCandidate objects.
    """
    return sorted(guides, key=lambda g: g.gc_content, reverse=reverse)
