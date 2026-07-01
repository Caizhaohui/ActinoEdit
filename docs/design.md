# ActinoEdit Design Document

## Architecture Overview

ActinoEdit follows a layered architecture:

```
┌─────────────────────────────────────────┐
│           User Interfaces               │
│  ┌──────────┐  ┌─────────────────────┐  │
│  │   CLI    │  │  NiceGUI Web App    │  │
│  └────┬─────┘  └──────────┬──────────┘  │
│       │                   │              │
│       └─────────┬─────────┘              │
│                 │                         │
│       ┌─────────▼─────────┐              │
│       │  Design Pipeline  │              │
│       └─────────┬─────────┘              │
│                 │                         │
│  ┌──────────────▼──────────────┐         │
│  │      Core Algorithms        │         │
│  │  ┌─────┐ ┌─────┐ ┌──────┐  │         │
│  │  │ PAM │ │Scan │ │Score │  │         │
│  │  └─────┘ └─────┘ └──────┘  │         │
│  │  ┌─────┐ ┌─────┐ ┌──────┐  │         │
│  │  │ FASTA│ │ GFF │ │ GBK  │  │         │
│  │  └─────┘ └─────┘ └──────┘  │         │
│  └─────────────────────────────┘         │
└─────────────────────────────────────────┘
```

## Coordinate System

- **External (User-facing)**: 1-based inclusive coordinates
  - Example: Gene at positions 100-200 means bases 100 through 200 inclusive
  - Used in: GFF files, CSV output, HTML reports

- **Internal (Python)**: 0-based half-open coordinates
  - Example: `sequence[99:200]` gives bases 100-200
  - Used in: All internal calculations

- **Conversion**: Always use explicit `to_slice()` and `from_slice()` methods

## Design Pipeline

The core design pipeline (`run_design_pipeline`) is the central orchestrator:

1. Parse input files (FASTA, GFF/GBK)
2. Resolve target region
3. Scan for guide candidates
4. Search for off-target hits
5. Score guides
6. Generate reports

The pipeline is independent of any UI framework and can be called from CLI or web.

## Data Models

All core data models use Python dataclasses:

- `Contig`: DNA sequence with metadata
- `GeneFeature`: Gene annotation
- `TargetRegion`: Target region for design
- `GuideCandidate`: Candidate guide RNA
- `OffTargetHit`: Off-target match
- `GuideScore`: Guide scoring
- `OrganismProfile`: Organism-specific parameters
