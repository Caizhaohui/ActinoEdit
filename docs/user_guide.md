# ActinoEdit User Guide

## Getting Started

### Installation

```bash
pip install actinoedit
```

Or install from source:

```bash
git clone https://github.com/actinoedit/actinoedit.git
cd actinoedit
pip install -e .
```

### Basic Usage

#### Design Guide RNAs

```bash
actinoedit design \
  --genome your_genome.fasta \
  --gff your_annotation.gff \
  --target your_gene \
  --profile streptomyces \
  --output-prefix results/my_design
```

#### Use Organism Profile

```bash
actinoedit design \
  --genome your_genome.fasta \
  --gff your_annotation.gff \
  --target your_gene \
  --profile streptomyces \
  --output-prefix results/output
```

This will generate:
- `results/output_guides.csv`
- `results/output_report.xlsx`
- `results/output_report.html`

## Input Files

### Genome FASTA

Standard FASTA format with DNA sequences:

```
>contig1 Chromosome
ATCGATCGATCG...
>contig2 Plasmid
GCGCGCGCGC...
```

### Annotation GFF3

Standard GFF3 format:

```
##gff-version 3
contig1	Prodigal	CDS	1	300	.	+	0	ID=geneA;locus_tag=SCO0001
```

### GenBank Format

Standard GenBank format (parsed using Biopython).

## Organism Profiles

Profiles provide default parameters for different organisms:

| Profile | Best For |
|---------|----------|
| `streptomyces` | Streptomyces and other actinomycetes |
| `ecoli` | Escherichia coli |
| `bacillus` | Bacillus species |
| `yeast` | Yeast and small fungal genomes |
| `custom` | Custom parameters |

## Output Formats

### CSV

Simple comma-separated values with guide candidates.

### Excel

Multi-sheet workbook with:
- Guide candidates
- Off-target hits
- Parameters
- Warnings

### HTML

Interactive HTML report with summary and detailed tables.

## Tips

1. **High GC Genomes**: Use `streptomyces` profile for actinomycetes
2. **Target Selection**: Use locus_tag for unambiguous gene targeting
3. **PAM Patterns**: NGG is default for SpCas9; use TTTV for Cas12a
