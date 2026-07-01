# ActinoEdit Database

## Overview

ActinoEdit supports optional local database for project management.

## Database Modes

### Local Mode (SQLite)

Default mode for single-user local installations.

- Database file: `~/.actinoedit/actinoedit.db`
- No configuration required
- Data stays on local machine

### Lab Server Mode (PostgreSQL)

For multi-user laboratory intranet deployments.

- Requires PostgreSQL server
- Configure in `lab_server.yaml`
- Supports concurrent users

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `organism` | Organism/strain records |
| `genome` | Genome sequences |
| `gene` | Gene annotations |
| `bgc` | Biosynthetic gene clusters |
| `guide` | Guide RNA candidates |
| `editing_project` | Editing projects |
| `validation_result` | Sequencing validation results |

## CLI Commands

```bash
# Initialize database
actinoedit db init

# Import genome
actinoedit db import-genome --fasta genome.fasta --gff annotation.gff

# List organisms
actinoedit db list-organisms

# Save guides
actinoedit db save-guides --input results/guides.csv --project my_project
```

## Data Privacy

- Local mode: All data stays on user's machine
- Lab server mode: Data stored on laboratory intranet server
- No data sent to external services
- User controls all data export

## Backup Strategy

### Local Mode

Backup the SQLite database file:

```bash
cp ~/.actinoedit/actinoedit.db ~/backups/actinoedit_$(date +%Y%m%d).db
```

### Lab Server Mode

Use PostgreSQL backup tools:

```bash
pg_dump actinoedit > backup.sql
```
