"""SQLite database connection and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".actinoedit" / "actinoedit.db"


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Return a connection to the ActinoEdit local database.

    Creates parent directories if needed.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """Initialize the database schema if it does not exist.

    Creates tables for:
      - projects
      - genomes
      - guides (saved designs)
      - bgc (optional)
    """
    if conn is None:
        conn = get_connection()

    cur = conn.cursor()

    # Projects / editing sessions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            organism_profile TEXT
        )
    """)

    # Genomes / strains
    cur.execute("""
        CREATE TABLE IF NOT EXISTS genomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            fasta_path TEXT,
            contigs INTEGER,
            total_length INTEGER,
            gc REAL,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Saved guide designs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            guide_id TEXT,
            contig TEXT,
            start INTEGER,
            end INTEGER,
            strand TEXT,
            spacer TEXT,
            pam TEXT,
            gc_content REAL,
            final_score REAL,
            recommendation TEXT,
            bgc_id TEXT,
            bgc_context TEXT,
            off_target_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)

    # BGC regions (cached)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bgc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genome_id INTEGER,
            bgc_id TEXT,
            contig TEXT,
            start INTEGER,
            end INTEGER,
            bgc_type TEXT,
            product TEXT,
            FOREIGN KEY(genome_id) REFERENCES genomes(id)
        )
    """)

    conn.commit()
    return conn
