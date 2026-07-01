# AGENTS.md

## Project

ActinoEdit is a Python toolkit and local web application for CRISPR guide RNA design in actinomycetes and industrial microbes.

The project supports custom microbial genomes and organism-specific sgRNA design profiles.

## Product roadmap

1. CLI core tool
2. Reusable design pipeline
3. Local web application
4. One-click local launcher
5. Local database
6. Industrial microbe database platform

## Architecture rules

- Core CRISPR design logic must be independent from CLI and web UI.
- CLI and web UI must both call the same reusable pipeline.
- Do not duplicate biological algorithms in UI code.
- Keep all core modules small and testable.
- The web application is local-first. User data should stay on the user's machine unless explicitly configured otherwise.

## Coding rules

- Use Python 3.10+.
- Use type hints.
- Use dataclasses or pydantic models for core objects.
- Use pytest for testing.
- Use ruff for linting.
- Use mypy for type checking.
- Prefer small, deterministic functions.
- Do not copy GPL or AGPL licensed code from external projects.
- Implement algorithms independently.

## Coordinate system

- External reports use 1-based inclusive genomic coordinates.
- Internal Python slicing uses 0-based half-open coordinates.
- Coordinate conversion must be explicit and tested.

## Sequence rules

- DNA sequences should be normalized to uppercase.
- Ambiguous bases should be handled safely.
- Invalid sequence characters should raise clear errors.
- FASTA, GFF3, and GenBank parsers should provide clear error messages.

## Safety and scope

This is a computational design and annotation tool.

Do not include wet-lab protocols, transformation conditions, culture conditions, or strain-specific operational instructions.

## Validation commands

Run these commands before considering a task complete:

```bash
pytest
ruff check .
mypy src
```
