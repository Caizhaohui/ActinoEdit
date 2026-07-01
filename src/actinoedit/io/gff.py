"""GFF3 file parser for ActinoEdit.

This module provides functions for reading GFF3 (General Feature Format version 3) files.
Supports standard GFF3 format, Prokka-like, and Bakta-like GFF styles.
"""

from __future__ import annotations

import re
from pathlib import Path

from actinoedit.core.models import GeneFeature

# Feature types to extract
VALID_FEATURE_TYPES = {"gene", "CDS", "rRNA", "tRNA", "ncRNA", "mRNA", "pseudogene"}

# Regular expression for GFF3 line
GFF3_LINE_RE = re.compile(
    r"^([^\t]+)\t"  # seqid
    r"([^\t]+)\t"  # source
    r"([^\t]+)\t"  # type
    r"(\d+)\t"  # start
    r"(\d+)\t"  # end
    r"([^\t]+)\t"  # score
    r"([+\-.])\t"  # strand
    r"([^\t]+)\t"  # phase
    r"(.*)$"  # attributes
)


def parse_gff(gff_path: str | Path) -> list[GeneFeature]:
    """Parse a GFF3 file and return a list of GeneFeature objects.

    Reads a GFF3 file and creates GeneFeature objects for each gene/CDS feature.
    Handles standard GFF3, Prokka-like, and Bakta-like formats.

    Args:
        gff_path: Path to the GFF3 file.

    Returns:
        List of GeneFeature objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid GFF3 format.

    Examples:
        >>> features = parse_gff("annotation.gff")
        >>> print(len(features))
        150
        >>> print(features[0].locus_tag)
        'SCO0001'
    """
    gff_path = Path(gff_path)
    if not gff_path.exists():
        raise FileNotFoundError(f"GFF3 file not found: {gff_path}")

    features: list[GeneFeature] = []
    in_fasta_section = False

    with open(gff_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check for FASTA section
            if line == "##FASTA":
                in_fasta_section = True
                continue

            # Skip FASTA sequences
            if in_fasta_section:
                continue

            # Skip comments
            if line.startswith("#"):
                continue

            # Parse GFF3 line
            feature = _parse_gff3_line(line, line_num)
            if feature is not None:
                features.append(feature)

    return features


def _parse_gff3_line(line: str, line_num: int) -> GeneFeature | None:
    """Parse a single GFF3 line.

    Args:
        line: GFF3 line to parse.
        line_num: Line number for error messages.

    Returns:
        GeneFeature object or None if line should be skipped.
    """
    match = GFF3_LINE_RE.match(line)
    if not match:
        return None

    seqid = match.group(1)
    _source = match.group(2)
    feature_type = match.group(3)
    start = int(match.group(4))
    end = int(match.group(5))
    _score = match.group(6)
    strand = match.group(7)
    _phase = match.group(8)
    attributes_str = match.group(9)

    # Skip features that are not genes/CDS
    if feature_type not in VALID_FEATURE_TYPES:
        return None

    # Parse attributes
    attributes = _parse_attributes(attributes_str)

    # Extract gene information
    locus_tag = attributes.get("locus_tag") or attributes.get("ID")
    gene_name = attributes.get("gene") or attributes.get("Name")
    product = attributes.get("product")

    return GeneFeature(
        contig=seqid,
        start=start,
        end=end,
        strand=strand,
        locus_tag=locus_tag,
        gene_name=gene_name,
        product=product,
        feature_type=feature_type,
    )


def _parse_attributes(attributes_str: str) -> dict[str, str]:
    """Parse GFF3 attributes string.

    Args:
        attributes_str: Attributes string from GFF3 format.

    Returns:
        Dictionary of attribute key-value pairs.
    """
    attributes: dict[str, str] = {}

    # Handle empty attributes
    if not attributes_str or attributes_str == ".":
        return attributes

    # Split by semicolon
    for attr in attributes_str.split(";"):
        attr = attr.strip()
        if not attr:
            continue

        # Split by first equals sign
        if "=" in attr:
            key, value = attr.split("=", 1)
            # URL decode if needed
            value = value.replace("%20", " ").replace("%3B", ";").replace("%3D", "=")
            attributes[key.strip()] = value.strip()

    return attributes


def parse_gff_string(gff_string: str) -> list[GeneFeature]:
    """Parse a GFF3 string and return a list of GeneFeature objects.

    Args:
        gff_string: GFF3 format string.

    Returns:
        List of GeneFeature objects.
    """
    from io import StringIO

    features: list[GeneFeature] = []
    in_fasta_section = False

    stream = StringIO(gff_string)
    for line_num, line in enumerate(stream, 1):
        line = line.strip()

        if not line:
            continue

        if line == "##FASTA":
            in_fasta_section = True
            continue

        if in_fasta_section:
            continue

        if line.startswith("#"):
            continue

        feature = _parse_gff3_line(line, line_num)
        if feature is not None:
            features.append(feature)

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

    Examples:
        >>> features = parse_gff("annotation.gff")
        >>> gene = find_by_locus_tag(features, "SCO0001")
        >>> print(gene.gene_name)
        'dnaA'
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

    Examples:
        >>> features = parse_gff("annotation.gff")
        >>> genes = find_by_gene_name(features, "dnaA")
        >>> print(len(genes))
        1
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

    Examples:
        >>> features = parse_gff("annotation.gff")
        >>> region_genes = find_features_in_region(features, "contig1", 1000, 5000)
        >>> print(len(region_genes))
        3
    """
    result: list[GeneFeature] = []
    for feature in features:
        if feature.contig == contig and feature.start <= end and feature.end >= start:
            result.append(feature)
    return result


def find_genes_by_contig(
    features: list[GeneFeature],
    contig: str,
) -> list[GeneFeature]:
    """Find all genes on a specific contig.

    Args:
        features: List of GeneFeature objects.
        contig: Contig name.

    Returns:
        List of GeneFeature objects on the contig.
    """
    return [f for f in features if f.contig == contig]


def get_unique_contigs(features: list[GeneFeature]) -> list[str]:
    """Get unique contig names from features.

    Args:
        features: List of GeneFeature objects.

    Returns:
        List of unique contig names in order of appearance.
    """
    seen: set[str] = set()
    result: list[str] = []
    for feature in features:
        if feature.contig not in seen:
            seen.add(feature.contig)
            result.append(feature.contig)
    return result


def filter_by_feature_type(
    features: list[GeneFeature],
    feature_type: str,
) -> list[GeneFeature]:
    """Filter features by type.

    Args:
        features: List of GeneFeature objects.
        feature_type: Feature type to filter by (gene, CDS, rRNA, tRNA, etc.).

    Returns:
        List of matching GeneFeature objects.
    """
    return [f for f in features if f.feature_type == feature_type]


def get_cds_features(features: list[GeneFeature]) -> list[GeneFeature]:
    """Get all CDS features.

    Args:
        features: List of GeneFeature objects.

    Returns:
        List of CDS GeneFeature objects.
    """
    return filter_by_feature_type(features, "CDS")


def get_gene_features(features: list[GeneFeature]) -> list[GeneFeature]:
    """Get all gene features.

    Args:
        features: List of GeneFeature objects.

    Returns:
        List of gene GeneFeature objects.
    """
    return filter_by_feature_type(features, "gene")
