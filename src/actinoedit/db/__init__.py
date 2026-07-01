"""Local SQLite database support for ActinoEdit.

Optional persistence layer for genomes, projects, saved guide designs.
Core design pipeline does NOT depend on the database.

Usage (CLI):
    actinoedit db init
    actinoedit db import-genome --name my_strep --genome ...
    actinoedit db save-guides --project myproject results/xxx_guides.csv
"""

from actinoedit.db.crud import (
    create_project,
    delete_project,
    export_project_guides,
    get_genes_for_genome,
    get_project_guides,
    import_genome,
    list_genomes,
    list_projects,
    list_saved_guides,
    save_genes,
    save_genome,
    save_guides_from_result,
)
from actinoedit.db.database import get_connection, init_database

__all__ = [
    "get_connection",
    "init_database",
    "save_genome",
    "save_guides_from_result",
    "list_projects",
    "get_project_guides",
    "list_saved_guides",
    "import_genome",
    "export_project_guides",
    "list_genomes",
    "get_genes_for_genome",
    "save_genes",
    "delete_project",
    "create_project",
]
