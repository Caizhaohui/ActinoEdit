"""Web-facing database service layer.

Pages should call these helpers instead of importing CRUD directly.
All DB access for the web UI goes through this module.
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from actinoedit.core.pipeline import DesignResult
from actinoedit.db import (
    create_project,
    delete_genome,
    delete_organism,
    delete_project,
    export_project_guides,
    get_genes_for_genome,
    get_project,
    get_project_guides,
    import_genome,
    link_genome_to_organism,
    link_project_genome,
    link_project_organism,
    list_genomes,
    list_genomes_for_organism,
    list_organisms,
    list_projects,
    list_projects_for_organism,
    save_guides_from_result,
    save_organism,
    update_organism,
    update_project,
)
from actinoedit.db.database import test_connection

GUIDE_TABLE_COLUMNS = [
    "guide_id",
    "contig",
    "start",
    "final_score",
    "recommendation",
    "bgc_context",
]

ORGANISM_TABLE_COLUMNS = ["name", "species", "strain", "description"]

GENOME_TABLE_COLUMNS = ["name", "organism_name", "contigs", "total_length", "gc"]

PROJECT_LINK_COLUMNS = ["organism_name", "genome_name", "guide_count"]

GENE_TABLE_COLUMNS = ["locus_tag", "gene_name", "contig", "start"]


def is_db_available() -> bool:
    """Return True if the configured database is reachable."""
    try:
        return test_connection()
    except Exception:
        return False


def db_unavailable_message() -> str:
    """User-facing hint when the database cannot be reached."""
    return "DB not available. Run 'actinoedit db init' from CLI first."


# ------------------------------------------------------------------
# Projects
# ------------------------------------------------------------------


def list_projects_summary() -> list[dict[str, Any]]:
    return list_projects()


def filter_projects(
    projects: list[dict[str, Any]],
    search_term: str = "",
) -> list[dict[str, Any]]:
    """Filter projects by name, profile, or linked organism/genome."""
    if not search_term:
        return projects
    needle = search_term.lower()
    return [
        p
        for p in projects
        if needle in p.get("name", "").lower()
        or needle in str(p.get("organism_profile", "")).lower()
        or needle in str(p.get("organism_name", "")).lower()
        or needle in str(p.get("genome_name", "")).lower()
    ]


def organism_name_options() -> list[str]:
    return [o["name"] for o in list_organisms() if o.get("name")]


def genome_name_options() -> list[str]:
    return [g["name"] for g in list_genomes() if g.get("name")]


def create_project_record(
    name: str,
    description: str = "",
    profile: str | None = None,
    organism_name: str | None = None,
    genome_name: str | None = None,
) -> int:
    return create_project(
        name,
        description,
        profile,
        organism_name=organism_name or None,
        genome_name=genome_name or None,
    )


def get_project_detail(name: str) -> dict[str, Any] | None:
    return get_project(name)


def update_project_links(
    name: str,
    *,
    organism_name: str = "",
    genome_name: str = "",
) -> bool:
    """Update project links; empty string clears the association."""
    return update_project(
        name,
        organism_name=organism_name if organism_name else None,
        genome_name=genome_name if genome_name else None,
        clear_organism=organism_name == "",
        clear_genome=genome_name == "",
    )


def link_project_to_organism(project_name: str, organism_name: str) -> bool:
    return link_project_organism(project_name, organism_name)


def link_project_to_genome(project_name: str, genome_name: str) -> bool:
    return link_project_genome(project_name, genome_name)


def delete_project_record(name: str) -> bool:
    return delete_project(name)


def get_project_guides_summary(project_name: str, limit: int = 100) -> list[dict[str, Any]]:
    return get_project_guides(project_name, limit=limit)


def guides_to_table_rows(guides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape guide dicts for NiceGUI table display."""
    return [{col: g.get(col, "") for col in GUIDE_TABLE_COLUMNS} for g in guides]


def save_design_to_project(
    result: DesignResult,
    project_name: str,
    replace_existing: bool = False,
    *,
    design_run_meta: dict[str, Any] | None = None,
) -> int:
    return save_guides_from_result(
        result,
        project_name,
        replace_existing=replace_existing,
        design_run_meta=design_run_meta,
    )


def export_guides_csv(project_name: str, output_path: str | Path) -> str:
    return export_project_guides(project_name, output_path, format="csv")


def default_project_export_path(
    project_name: str,
    *,
    base_dir: str | Path = "results/db_exports",
    suffix: str = "_guides",
) -> Path:
    """Default filesystem path for exporting a project's guides."""
    return Path(base_dir) / f"{project_name}{suffix}.csv"


# ------------------------------------------------------------------
# Organisms
# ------------------------------------------------------------------


def list_organisms_summary() -> list[dict[str, Any]]:
    return list_organisms()


def filter_organisms(
    organisms: list[dict[str, Any]],
    search_term: str = "",
) -> list[dict[str, Any]]:
    """Filter organisms by name, species, or strain."""
    if not search_term:
        return organisms
    needle = search_term.lower()
    return [
        o
        for o in organisms
        if needle
        in (str(o.get("name", "")) + str(o.get("species", "")) + str(o.get("strain", ""))).lower()
    ]


def add_organism(name: str, species: str | None = None, strain: str | None = None) -> int:
    return save_organism(name, species, strain)


def remove_organism(name: str) -> bool:
    return delete_organism(name)


def patch_organism(
    name: str,
    species: str | None = None,
    strain: str | None = None,
) -> bool:
    return update_organism(name, species, strain)


def organisms_to_table_rows(organisms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape organism dicts for NiceGUI table display."""
    return [{col: o.get(col, "") for col in ORGANISM_TABLE_COLUMNS} for o in organisms]


def export_organisms_csv_bytes(organisms: list[dict[str, Any]]) -> bytes:
    """Serialize organisms to CSV bytes for browser download."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=ORGANISM_TABLE_COLUMNS)
    writer.writeheader()
    for org in organisms:
        writer.writerow({col: org.get(col, "") for col in ORGANISM_TABLE_COLUMNS})
    return output.getvalue().encode()


# ------------------------------------------------------------------
# Genomes
# ------------------------------------------------------------------


def list_genomes_summary() -> list[dict[str, Any]]:
    return list_genomes()


def filter_genomes(
    genomes: list[dict[str, Any]],
    search_term: str = "",
) -> list[dict[str, Any]]:
    """Filter genomes by name or linked organism."""
    if not search_term:
        return genomes
    needle = search_term.lower()
    return [
        g
        for g in genomes
        if needle in g.get("name", "").lower()
        or needle in str(g.get("organism_name", "")).lower()
    ]


def import_genome_record(
    name: str,
    genome_path: str,
    annotation_path: str | None = None,
    organism_name: str | None = None,
) -> dict[str, Any]:
    """Import a genome and optional annotation from filesystem paths."""
    return import_genome(
        name,
        genome_path,
        annotation_path,
        organism_name=organism_name or None,
    )


def link_genome_organism(genome_name: str, organism_name: str) -> bool:
    return link_genome_to_organism(genome_name, organism_name)


def list_genomes_for_organism_summary(organism_name: str) -> list[dict[str, Any]]:
    return list_genomes_for_organism(organism_name)


def list_projects_for_organism_summary(organism_name: str) -> list[dict[str, Any]]:
    return list_projects_for_organism(organism_name)


def remove_genome(name: str) -> bool:
    return delete_genome(name)


def genomes_to_table_rows(genomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Shape genome dicts for NiceGUI table display."""
    return [{col: g.get(col, "") for col in GENOME_TABLE_COLUMNS} for g in genomes]


def export_genomes_csv_bytes(genomes: list[dict[str, Any]]) -> bytes:
    """Serialize genomes to CSV bytes for browser download."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=GENOME_TABLE_COLUMNS)
    writer.writeheader()
    for genome in genomes:
        writer.writerow({col: genome.get(col, "") for col in GENOME_TABLE_COLUMNS})
    return output.getvalue().encode()


def get_genome_genes(genome_id: int, limit: int = 50) -> list[dict[str, Any]]:
    return get_genes_for_genome(genome_id=genome_id, limit=limit)


# ------------------------------------------------------------------
# E2E acceptance (headless demo workflow)
# ------------------------------------------------------------------


def run_demo_acceptance(
    output_dir: str | Path | None = None,
    db_url: str | None = None,
) -> dict[str, Any]:
    """Headless v0.2/v0.3 acceptance: design -> reports -> DB -> export."""
    from actinoedit.web.demo import run_demo_acceptance as _run

    return _run(output_dir=output_dir, db_url=db_url)
