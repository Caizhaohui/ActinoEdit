"""GenBank file parser for ActinoEdit.

This module provides functions for reading GenBank format files using Biopython.
Extracts gene and CDS features with locus tags, gene names, and products.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from actinoedit.core.models import GeneFeature


def parse_gbk(gbk_path: str | Path) -> list[GeneFeature]:
    """Parse a GenBank file and return a list of GeneFeature objects.

    Uses Biopython to parse GenBank format files and extract gene features.

    Args:
        gbk_path: Path to the GenBank file.

    Returns:
        List of GeneFeature objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If Biopython is not installed.
        ValueError: If the file cannot be parsed.

    Examples:
        >>> features = parse_gbk("annotation.gbk")
        >>> print(len(features))
        150
        >>> print(features[0].locus_tag)
        'SCO0001'
    """
    gbk_path = Path(gbk_path)
    if not gbk_path.exists():
        raise FileNotFoundError(f"GenBank file not found: {gbk_path}")

    try:
        from Bio import SeqIO
    except ImportError as err:
        raise ImportError(
            "Biopython is required for GenBank parsing. "
            "Install it with: pip install biopython"
        ) from err

    features: list[GeneFeature] = []

    for record in SeqIO.parse(str(gbk_path), "genbank"):
        contig_name = record.id or record.name

        for feature in record.features:
            if feature.type not in ("gene", "CDS"):
                continue

            gene_feature = _biopython_feature_to_gene_feature(
                feature, contig_name
            )
            if gene_feature is not None:
                features.append(gene_feature)

    return features


def _biopython_feature_to_gene_feature(
    feature: Any, contig_name: str
) -> GeneFeature | None:
    """Convert a Biopython feature to a GeneFeature.

    Args:
        feature: Biopython SeqFeature object.
        contig_name: Contig/record name.

    Returns:
        GeneFeature object or None if conversion fails.
    """
    # Get coordinates (Biopython uses 0-based)
    start = int(feature.location.start) + 1  # Convert to 1-based
    end = int(feature.location.end)

    # Get strand
    if feature.location.strand == 1:
        strand = "+"
    elif feature.location.strand == -1:
        strand = "-"
    else:
        strand = "."

    # Get qualifiers
    qualifiers = feature.qualifiers

    # Extract locus_tag
    locus_tag = None
    if "locus_tag" in qualifiers:
        locus_tag = qualifiers["locus_tag"][0]

    # Extract gene name
    gene_name = None
    if "gene" in qualifiers:
        gene_name = qualifiers["gene"][0]

    # Extract product
    product = None
    if "product" in qualifiers:
        product = qualifiers["product"][0]

    return GeneFeature(
        contig=contig_name,
        start=start,
        end=end,
        strand=strand,
        locus_tag=locus_tag,
        gene_name=gene_name,
        product=product,
        feature_type=feature.type,
    )


def parse_gbk_string(gbk_string: str) -> list[GeneFeature]:
    """Parse a GenBank format string and return a list of GeneFeature objects.

    Args:
        gbk_string: GenBank format string.

    Returns:
        List of GeneFeature objects.

    Raises:
        ImportError: If Biopython is not installed.
    """
    try:
        from io import StringIO

        from Bio import SeqIO
    except ImportError as err:
        raise ImportError(
            "Biopython is required for GenBank parsing. "
            "Install it with: pip install biopython"
        ) from err

    features: list[GeneFeature] = []

    for record in SeqIO.parse(StringIO(gbk_string), "genbank"):
        contig_name = record.id or record.name

        for feature in record.features:
            if feature.type not in ("gene", "CDS"):
                continue

            gene_feature = _biopython_feature_to_gene_feature(
                feature, contig_name
            )
            if gene_feature is not None:
                features.append(gene_feature)

    return features


def find_by_locus_tag(
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


def find_by_gene_name(
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


def find_features_in_region(
    features: list[GeneFeature],
    contig: str,
    start: int,
    end: int,
) -> list[GeneFeature]:
    """Find features within a genomic region.

    Args:
        features: List of GeneFeature objects.
        contig: Contig name.
        start: Region start (1-based inclusive).
        end: Region end (1-based inclusive).

    Returns:
        List of GeneFeature objects within the region.
    """
    result: list[GeneFeature] = []
    for feature in features:
        if feature.contig == contig and feature.start <= end and feature.end >= start:
            result.append(feature)
    return result
