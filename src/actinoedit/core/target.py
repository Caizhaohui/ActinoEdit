"""Target region selection for ActinoEdit.

This module provides functions for selecting target regions by locus tag,
gene name, or coordinate string.
"""

from __future__ import annotations

import re

from actinoedit.core.models import GeneFeature, TargetRegion

# Regular expression for coordinate string: contig:start-end
COORD_RE = re.compile(r"^([^:]+):(\d+)-(\d+)$")


def resolve_target(
    features: list[GeneFeature],
    target_str: str,
    contig_length: int | None = None,
    upstream_flank: int = 0,
    downstream_flank: int = 0,
) -> TargetRegion:
    """Resolve a target string to a TargetRegion.

    The target string can be:
    - A locus tag (e.g., "SCO0001")
    - A gene name (e.g., "dnaA")
    - A coordinate string (e.g., "contig1:100-500")

    Args:
        features: List of GeneFeature objects from annotation.
        target_str: Target string to resolve.
        contig_length: Optional contig length for validation.
        upstream_flank: Bases to extend upstream.
        downstream_flank: Bases to extend downstream.

    Returns:
        TargetRegion object.

    Raises:
        ValueError: If target cannot be resolved or is ambiguous.

    Examples:
        >>> features = parse_gff("annotation.gff")
        >>> target = resolve_target(features, "SCO0001")
        >>> print(target.start, target.end)
        100 500
    """
    # Try coordinate string first
    coord_match = COORD_RE.match(target_str)
    if coord_match:
        contig = coord_match.group(1)
        start = int(coord_match.group(2))
        end = int(coord_match.group(3))
        return TargetRegion(
            contig=contig,
            start=start,
            end=end,
            strand=".",
            label=target_str,
        )

    # Try locus tag
    locus_match = _find_by_locus_tag(features, target_str)
    if locus_match is not None:
        return _gene_to_target(locus_match, upstream_flank, downstream_flank)

    # Try gene name
    gene_matches = _find_by_gene_name(features, target_str)
    if len(gene_matches) == 1:
        return _gene_to_target(gene_matches[0], upstream_flank, downstream_flank)
    elif len(gene_matches) > 1:
        genes_info = [
            f"{g.locus_tag or 'unknown'} ({g.contig}:{g.start}-{g.end})"
            for g in gene_matches
        ]
        raise ValueError(
            f"Ambiguous gene name '{target_str}'. "
            f"Found {len(gene_matches)} matches: {genes_info}. "
            f"Use locus_tag or coordinate string instead."
        )

    raise ValueError(
        f"Target '{target_str}' not found. "
        f"Searched by locus_tag, gene_name, and coordinate format."
    )


def _find_by_locus_tag(
    features: list[GeneFeature],
    locus_tag: str,
) -> GeneFeature | None:
    """Find a feature by locus_tag.

    Args:
        features: List of GeneFeature objects.
        locus_tag: Locus tag to search for.

    Returns:
        GeneFeature if found, None otherwise.
    """
    for feature in features:
        if feature.locus_tag == locus_tag:
            return feature
    return None


def _find_by_gene_name(
    features: list[GeneFeature],
    gene_name: str,
) -> list[GeneFeature]:
    """Find features by gene name.

    Args:
        features: List of GeneFeature objects.
        gene_name: Gene name to search for.

    Returns:
        List of matching GeneFeature objects.
    """
    return [f for f in features if f.gene_name == gene_name]


def _gene_to_target(
    gene: GeneFeature,
    upstream_flank: int = 0,
    downstream_flank: int = 0,
) -> TargetRegion:
    """Convert a GeneFeature to a TargetRegion.

    Args:
        gene: GeneFeature object.
        upstream_flank: Bases to extend upstream.
        downstream_flank: Bases to extend downstream.

    Returns:
        TargetRegion object.
    """
    start = max(1, gene.start - upstream_flank)
    end = gene.end + downstream_flank

    return TargetRegion(
        contig=gene.contig,
        start=start,
        end=end,
        strand=gene.strand,
        label=gene.display_name,
    )


def get_target_info(
    features: list[GeneFeature],
    target_str: str,
) -> dict:
    """Get detailed information about a target.

    Args:
        features: List of GeneFeature objects.
        target_str: Target string to resolve.

    Returns:
        Dictionary with target information.

    Raises:
        ValueError: If target cannot be resolved.
    """
    target = resolve_target(features, target_str)

    # Find the gene feature if target is a gene
    gene = None
    coord_match = COORD_RE.match(target_str)
    if not coord_match:
        gene = _find_by_locus_tag(features, target_str)
        if gene is None:
            gene_matches = _find_by_gene_name(features, target_str)
            if gene_matches:
                gene = gene_matches[0]

    info = {
        "target_str": target_str,
        "contig": target.contig,
        "start": target.start,
        "end": target.end,
        "strand": target.strand,
        "length": target.length,
        "label": target.display_label,
    }

    if gene is not None:
        info.update({
            "locus_tag": gene.locus_tag,
            "gene_name": gene.gene_name,
            "product": gene.product,
            "feature_type": gene.feature_type,
        })

    return info


def list_targets(
    features: list[GeneFeature],
    contig: str | None = None,
) -> list[dict]:
    """List all available targets.

    Args:
        features: List of GeneFeature objects.
        contig: Optional contig name to filter by.

    Returns:
        List of dictionaries with target information.
    """
    targets: list[dict] = []

    for feature in features:
        if contig is not None and feature.contig != contig:
            continue

        targets.append({
            "locus_tag": feature.locus_tag,
            "gene_name": feature.gene_name,
            "contig": feature.contig,
            "start": feature.start,
            "end": feature.end,
            "strand": feature.strand,
            "length": feature.length,
            "product": feature.product,
        })

    return targets
