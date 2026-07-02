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

For multi-user laboratory intranet deployments (Phase 7 preparation).

- Requires PostgreSQL server
- Set env: ACTINOEDIT_DB_URL=postgresql://user:pass@host:5432/actinoedit
- Or config in `lab_server.yaml`
- Supports concurrent users (future full impl with SQLAlchemy)
- Use Alembic for migrations in future

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `organisms` | Organism/strain records |
| `genomes` | Genome sequences |
| `genes` | Gene annotations |
| `bgc` | Biosynthetic gene clusters |
| `guides` | Guide RNA candidates |
| `projects` | Editing projects |
| `validation_results` | Sequencing validation results (stub) |

## CLI Commands

```bash
# Initialize database
actinoedit db init

# Import genome (also saves genes)
actinoedit db import-genome --name my_strep --genome genome.fasta --gff annotation.gff

# List
actinoedit db list-organisms
actinoedit db list-genomes
actinoedit db list-genes --genome my_strep

# Save guides from design
actinoedit db save-guides --prefix results/design --project myproj

# Organism and validation
actinoedit db set-organism --name "S. coelicolor A3(2)"
actinoedit db save-validation --project myproj --guide-id g123 --result success
actinoedit db list-validations --project myproj

# Web UI (independent pages)
# Visit /organisms , /genomes , /projects for full CRUD and exports
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

## Configuration

### Environment
- ACTINOEDIT_DB_URL : e.g. sqlite:////absolute/path.db or postgresql://...

### Production Postgres Config (pooling, SSL)
```yaml
# lab_server.yaml example for production
database:
  url: postgresql://actinoedit:secret@dbserver:5432/actinoedit
  pool_size: 10
  max_overflow: 20
  echo: false
  connect_args:
    sslmode: require
    connect_timeout: 10
```

Use in code:
```python
from actinoedit.db.database import get_engine, get_session
from actinoedit.db.config import load_config, get_engine_options
config = load_config("lab")
engine = get_engine(extra_options=get_engine_options(config))
session = get_session(extra_options=get_engine_options(config))
```

### Example local.yaml
```yaml
database:
  url: sqlite:////home/user/.actinoedit/actinoedit.db
```

### Example lab_server.yaml
```yaml
database:
  url: postgresql://actinoedit:secret@dbserver:5432/actinoedit
```

## Migrations (Alembic)
Alembic is set up for schema migrations, supporting SQLite and PostgreSQL.

### Run Example
```bash
# After setting DB URL
export ACTINOEDIT_DB_URL=sqlite:///./test.db

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration after model change
alembic revision --autogenerate -m "add new table"

# View current
alembic current
```

See alembic/versions/ for scripts. Run from project root with alembic.ini.

Actual demo output:
INFO [alembic.runtime.migration] Running upgrade  -> 001, Initial schema for ActinoEdit v0.2+

## Postgres Testing
Full support with psycopg2-binary + SQLAlchemy.
Test engine + connect (connection will fail without running server, as expected):

```bash
export ACTINOEDIT_DB_URL=postgresql://test:test@localhost/test_actino
python -c "
from actinoedit.db.database import get_engine, test_connection
from actinoedit.db.config import get_db_url, is_postgres
url = get_db_url()
print('postgres?', is_postgres(url))
engine = get_engine(url)
print('dialect:', engine.dialect.name)
print('connect test:', test_connection(url))  # False without server
"
python -m pytest -k "postgres or db"
```
Example output:
Postgres driver test done.
Connection test failed: (psycopg2.OperationalError) connection refused
Tests cover config, engine creation, and expected connection errors (driver is used).
Example with conda python (psycopg2 installed):
Connection test failed: (psycopg2.OperationalError) connection refused
Full E2E test command:
 /hpcfs/fpublic/app/miniforge3/conda/bin/python -c '
import os
os.environ["ACTINOEDIT_DB_URL"] = "postgresql://user:pass@localhost:5432/testdb"
from actinoedit.db.database import get_engine, test_connection
from actinoedit.db.config import get_db_url, is_postgres
url = get_db_url()
print("postgres?", is_postgres(url))
engine = get_engine(url)
print("dialect:", engine.dialect.name)
print("connect test:", test_connection(url))
'
python -m pytest -k "postgres or db"
```
```

## CI for Postgres E2E
See .github/workflows/db-migrations.yml for GitHub Actions that starts Postgres service and runs:
- alembic upgrade
- pytest -k "postgres or db" against the live service
```
```
```

## Test isolation

CRUD functions accept optional `session` and `db_url` parameters. Tests should set:

```bash
export ACTINOEDIT_DB_URL=sqlite:////tmp/actinoedit_test.db
```

or use the `db_url` pytest fixture from `tests/conftest.py`, which routes all DB calls to a temporary SQLite file.

## Web DB Pages

Web pages call `actinoedit.web.db_service` (not CRUD directly):

- `/organisms`: add/update/delete, search, export filtered CSV
- `/genomes`: list/delete, search, export filtered CSV
- `/projects`: CRUD, save current design, export guides CSV

CRISPRi columns (promoter/early_cds, distance, strand_rel) appear in the design results table when `mode=crispri`. These are **computational screening annotations** — see README "Scientific scope".

## PostgreSQL / multi-user (deferred)

Keep `examples/lab_server.yaml`, Alembic migrations, and `ACTINOEDIT_DB_URL` for Postgres smoke tests. Primary focus remains local SQLite stability, repeatable schema migration, and reliable test isolation.
