# ActinoEdit Developer Guide

## Development Setup

### Prerequisites

- Python 3.10+
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/actinoedit/actinoedit.git
cd actinoedit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"
```

## Code Quality

### Linting

```bash
ruff check .
```

### Type Checking

```bash
mypy src
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=actinoedit

# Run specific test file
pytest tests/test_models.py
```

## Project Structure

```
src/actinoedit/
├── __init__.py          # Package initialization
├── cli.py               # Typer CLI commands
├── config.py            # Configuration management
├── core/                # Core algorithms
│   ├── models.py        # Data models
│   ├── pam.py           # PAM matching
│   ├── scanner.py       # Guide scanning
│   ├── target.py        # Target resolution
│   ├── offtarget.py     # Off-target search
│   ├── scoring.py       # Guide scoring
│   └── pipeline.py      # Design pipeline
├── io/                  # File parsers
│   ├── fasta.py         # FASTA parser
│   ├── gff.py           # GFF3 parser
│   └── gbk.py           # GenBank parser
├── annotation/          # Annotation modules
│   └── bgc.py           # BGC annotation
├── reports/             # Report generation
│   ├── tables.py        # DataFrame conversion
│   ├── excel.py         # Excel export
│   └── html.py          # HTML report
├── web/                 # NiceGUI web app
│   ├── app.py           # Web application
│   ├── pages.py         # Page definitions
│   └── components.py    # UI components
└── db/                  # Database modules
    ├── models.py        # Database models
    └── crud.py          # CRUD operations
```

## Adding New Features

### 1. Core Algorithm

Add to `src/actinoedit/core/`:

```python
# my_module.py
def my_function() -> None:
    """My function documentation."""
    pass
```

### 2. CLI Command

Add to `src/actinoedit/cli.py`:

```python
@app.command()
def my_command(
    param: str = typer.Option(..., help="Parameter description"),
) -> None:
    """Command description."""
    # Implementation
```

### 3. Tests

Add to `tests/`:

```python
# test_my_module.py
def test_my_function() -> None:
    """Test my function."""
    assert True
```

## Coordinate System

Always use the coordinate conversion methods:

```python
# 1-based inclusive to 0-based half-open
start_0, end_0 = contig.to_slice(start_1, end_1)

# 0-based half-open to 1-based inclusive
start_1, end_1 = Contig.from_slice(start_0, end_0)
```

## Pull Request Process

1. Create feature branch from `develop`
2. Implement changes
3. Add tests
4. Run `pytest`, `ruff check .`, `mypy src`
5. Submit PR to `develop` branch

## Release Process

1. Update version in `src/actinoedit/__init__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Merge to `main`
5. Tag release
6. Publish to PyPI
