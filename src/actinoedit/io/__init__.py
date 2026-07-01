"""Input/Output modules for parsing genomic files."""

from actinoedit.io.fasta import (
    count_contigs,
    extract_region,
    get_contig,
    get_contig_names,
    parse_fasta,
    parse_fasta_string,
    validate_fasta,
    write_fasta,
    write_fasta_string,
)
from actinoedit.io.gbk import parse_gbk, parse_gbk_string
from actinoedit.io.gff import (
    filter_by_feature_type,
    find_by_gene_name,
    find_by_locus_tag,
    find_features_in_region,
    find_genes_by_contig,
    get_cds_features,
    get_gene_features,
    get_unique_contigs,
    parse_gff,
    parse_gff_string,
)

__all__ = [
    # FASTA
    "count_contigs",
    "extract_region",
    "get_contig",
    "get_contig_names",
    "parse_fasta",
    "parse_fasta_string",
    "validate_fasta",
    "write_fasta",
    "write_fasta_string",
    # GFF3
    "filter_by_feature_type",
    "find_by_gene_name",
    "find_by_locus_tag",
    "find_features_in_region",
    "find_genes_by_contig",
    "get_cds_features",
    "get_gene_features",
    "get_unique_contigs",
    "parse_gff",
    "parse_gff_string",
    # GenBank
    "parse_gbk",
    "parse_gbk_string",
]
