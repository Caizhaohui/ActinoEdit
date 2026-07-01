# ActinoEdit

**CRISPR Design Toolkit for Actinomycetes and Industrial Microbes**

ActinoEdit is a Python toolkit and local web application for CRISPR guide RNA design in actinomycetes and industrial microbes.

## Features

- 🧬 Custom microbial genome support
- 🔬 Organism-specific sgRNA design profiles
- 🧪 High GC content optimization for actinomycetes
- 🔒 Local-first design for data privacy
- 📊 CSV, Excel, and HTML report generation
- 🌐 NiceGUI local web interface (run with `actinoedit-web`)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/actinoedit/actinoedit.git
cd actinoedit

# Install in development mode
pip install -e ".[dev]"
```

### Requirements

- Python 3.10+
- Dependencies: biopython, pandas, openpyxl, typer, rich, jinja2, pyyaml

## Quick Start

### CLI Usage

```bash
# Show help
actinoedit --help

# Design guide RNAs (full pipeline: off-targets + scoring + reports)
actinoedit design \
  --genome examples/demo_genome.fasta \
  --gff examples/demo_annotation.gff \
  --target geneA \
  --profile streptomyces \
  --output-prefix results/geneA

# This produces:
#   results/geneA_guides.csv
#   results/geneA_report.xlsx
#   results/geneA_report.html

# View target information
actinoedit target-info \
  --genome examples/demo_genome.fasta \
  --gff examples/demo_annotation.gff \
  --target geneA

# Base editing analysis
actinoedit base-edit --genome ... --gff ... --target geneA --editor CBE

# Local DB
actinoedit db init
actinoedit db import-genome --name mystrain --genome genome.fasta --gff ann.gff
actinoedit db save-guides --prefix results/design --project myproj
actinoedit db export --project myproj --output myguides.csv
```

### Web Interface

```bash
# Start local web application
actinoedit-web
# or
python -m actinoedit.web.app

# Open browser to http://127.0.0.1:8080 (or use --show to auto-open)
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src
```

### Project Structure

```
actinoedit/
├── src/
│   └── actinoedit/
│       ├── cli.py           # Command line interface
│       ├── config.py        # Configuration management
│       ├── io/              # File parsers (FASTA, GFF, GBK)
│       ├── core/            # Core CRISPR design algorithms
│       ├── annotation/      # Gene and BGC annotation
│       ├── reports/         # Report generation
│       ├── web/             # NiceGUI web application
│       └── db/              # Database modules
├── tests/                   # Test suite
├── examples/                # Example data and profiles
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

## Organism Profiles

ActinoEdit supports organism-specific design profiles:

| Profile | Description | Default PAM | GC Range |
|---------|-------------|-------------|----------|
| actinomycete | General actinomycete | NGG | 40-80% |
| streptomyces | Streptomyces species | NGG | 40-80% |
| ecoli | Escherichia coli | NGG | 35-70% |
| bacillus | Bacillus species | NGG | 35-70% |
| yeast | Yeast / small fungal genomes | NGG | 30-70% |
| custom | Custom microorganism | NGG | 30-80% |

## Roadmap

- [x] v0.1: CLI MVP
- [x] v0.2: CLI with off-target search and scoring (pipeline + reports)
- [x] v0.3: Local Web MVP (NiceGUI with full pipeline + uploads)
- [x] v0.4: One-click / packaged launcher
- [x] v0.5: BGC annotation (Phase 5 start)
- [x] v0.6 partial: CRISPRi mode + base editing analysis + DB skeleton (import/export/projects)
- [ ] v0.7: Full local SQLite project management + Web DB browsing
- [ ] v1.0: Industrial microbe database platform


## License

MIT License

## Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/contributing.md) for details.

## Citation

If you use ActinoEdit in your research, please cite:

```
ActinoEdit: CRISPR Design Toolkit for Actinomycetes and Industrial Microbes
```
