"""CRUD operations for the local ActinoEdit database.

These functions are intentionally simple and use only stdlib sqlite3.
They are meant to be called from CLI or (optionally) from the web app.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from actinoedit.core.models import GeneFeature
from actinoedit.core.pipeline import DesignResult
from actinoedit.db.database import get_connection, init_database
from actinoedit.io.fasta import parse_fasta
from actinoedit.io.gbk import parse_gbk
from actinoedit.io.gff import parse_gff


def ensure_db(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """Get or initialize a DB connection."""
    if conn is None:
        conn = get_connection()
    init_database(conn)
    return conn


def create_project(name: str, description: str = "", profile: str | None = None) -> int:
    """Create a new project and return its id."""
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO projects (name, description, organism_profile) VALUES (?, ?, ?)",
        (name, description, profile),
    )
    conn.commit()
    row = cur.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    return int(row["id"]) if row else -1


def save_genome(
    name: str,
    fasta_path: str | None = None,
    contigs: int = 0,
    total_length: int = 0,
    gc: float = 0.0,
) -> int:
    """Import/register a genome."""
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO genomes (name, fasta_path, contigs, total_length, gc)
           VALUES (?, ?, ?, ?, ?)""",
        (name, fasta_path, contigs, total_length, gc),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def save_guides_from_result(
    result: DesignResult,
    project_name: str,
    replace_existing: bool = False,
) -> int:
    """Persist the guide results of a design run into the database.

    Returns number of guides saved.
    """
    if not result.guide_candidates:
        return 0

    conn = ensure_db()
    project_id = create_project(project_name)

    if replace_existing:
        conn.execute("DELETE FROM guides WHERE project_id = ?", (project_id,))

    cur = conn.cursor()

    count = 0
    score_map = {s.guide_id: s for s in result.guide_scores}

    for guide in result.guide_candidates:
        sc = score_map.get(guide.guide_id)
        ot_hits = result.off_target_hits.get(guide.guide_id, [])
        ot_count = len(ot_hits)

        cur.execute(
            """
            INSERT INTO guides (
                project_id, guide_id, contig, start, end, strand,
                spacer, pam, gc_content, final_score, recommendation,
                bgc_id, bgc_context, off_target_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                guide.guide_id,
                guide.contig,
                guide.start,
                guide.end,
                guide.strand,
                guide.spacer,
                guide.pam,
                guide.gc_content,
                sc.final_score if sc else None,
                sc.recommendation if sc else None,
                guide.bgc_id,
                guide.bgc_context,
                ot_count,
            ),
        )
        count += 1

    conn.commit()
    return count


def list_projects() -> list[dict[str, Any]]:
    conn = ensure_db()
    rows = conn.execute(
        "SELECT id, name, description, organism_profile, created_at FROM projects ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_project_guides(project_name: str, limit: int = 100) -> list[dict[str, Any]]:
    conn = ensure_db()
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
    if not row:
        return []
    pid = row["id"]
    rows = conn.execute(
        "SELECT * FROM guides WHERE project_id = ? ORDER BY final_score DESC LIMIT ?",
        (pid, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def list_saved_guides(project_name: str | None = None) -> list[dict[str, Any]]:
    """Convenience wrapper."""
    if project_name:
        return get_project_guides(project_name)
    conn = ensure_db()
    rows = conn.execute("SELECT * FROM guides ORDER BY created_at DESC LIMIT 200").fetchall()
    return [dict(r) for r in rows]


def import_genome(
    name: str,
    genome_path: str,
    annotation_path: str | None = None,
) -> dict[str, Any]:
    """Import a genome (and optional annotation) into the DB.

    Computes basic stats using the IO parsers and stores in genomes table.
    Returns summary dict.
    """
    genome_p = Path(genome_path)
    if not genome_p.exists():
        raise FileNotFoundError(f"Genome not found: {genome_path}")

    contigs = parse_fasta(str(genome_p))
    total_length = sum(c.length for c in contigs.values())
    # Average GC (weighted rough)
    gc = sum(c.gc_content * c.length for c in contigs.values()) / max(1, total_length)

    genome_id = save_genome(
        name=name,
        fasta_path=str(genome_p),
        contigs=len(contigs),
        total_length=total_length,
        gc=round(gc, 4),
    )

    feature_count = 0
    if annotation_path:
        ann_p = Path(annotation_path)
        if ann_p.exists():
            suffix = ann_p.suffix.lower()
            if suffix in (".gff", ".gff3"):
                features = parse_gff(str(ann_p))
            else:
                features = parse_gbk(str(ann_p))
            feature_count = len(features)
            save_genes(genome_id, features)

    return {
        "genome_id": genome_id,
        "name": name,
        "contigs": len(contigs),
        "total_length": total_length,
        "gc": round(gc, 4),
        "features_imported": feature_count,
    }


def export_project_guides(
    project_name: str,
    output_path: str | Path,
    format: str = "csv",
) -> str:
    """Export saved guides for a project to CSV or Excel.

    Returns the path written.
    """
    guides = get_project_guides(project_name, limit=10000)
    if not guides:
        raise ValueError(f"No guides found for project '{project_name}'")

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(guides)

    # Drop internal ids for clean export
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    if "project_id" in df.columns:
        df = df.drop(columns=["project_id"])

    if format.lower() == "xlsx":
        if not str(out_p).endswith(".xlsx"):
            out_p = out_p.with_suffix(".xlsx")
        df.to_excel(out_p, index=False, engine="openpyxl")
    else:
        if not str(out_p).endswith(".csv"):
            out_p = out_p.with_suffix(".csv")
        df.to_csv(out_p, index=False)

    return str(out_p)


def save_genes(genome_id: int, features: list[GeneFeature]) -> int:
    """Save GeneFeature list into the genes table for a genome."""
    if not features:
        return 0
    conn = ensure_db()
    cur = conn.cursor()
    count = 0
    for f in features:
        cur.execute(
            """
            INSERT INTO genes (genome_id, contig, start, end, strand,
                               locus_tag, gene_name, product, feature_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                genome_id,
                f.contig,
                f.start,
                f.end,
                f.strand,
                f.locus_tag,
                f.gene_name,
                f.product,
                f.feature_type,
            ),
        )
        count += 1
    conn.commit()
    return count


def get_genes_for_genome(genome_name: str | None = None, genome_id: int | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """Retrieve genes for a genome."""
    conn = ensure_db()
    if genome_id is None and genome_name:
        row = conn.execute("SELECT id FROM genomes WHERE name = ?", (genome_name,)).fetchone()
        if not row:
            return []
        genome_id = row["id"]
    if genome_id is None:
        return []
    rows = conn.execute(
        "SELECT * FROM genes WHERE genome_id = ? ORDER BY contig, start LIMIT ?",
        (genome_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def list_genomes() -> list[dict[str, Any]]:
    """List all imported genomes."""
    conn = ensure_db()
    rows = conn.execute(
        "SELECT id, name, fasta_path, contigs, total_length, gc, imported_at FROM genomes ORDER BY imported_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_project(project_name: str) -> bool:
    """Delete a project and its guides (cascades not auto, so manual)."""
    conn = ensure_db()
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
    if not row:
        return False
    pid = row["id"]
    conn.execute("DELETE FROM guides WHERE project_id = ?", (pid,))
    conn.execute("DELETE FROM projects WHERE id = ?", (pid,))
    conn.commit()
    return True
