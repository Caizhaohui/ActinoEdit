"""Database support for ActinoEdit (SQLite primary, Postgres prep for Phase 7).

Optional persistence layer. Core design pipeline does NOT depend on the database.

Usage (CLI):
    actinoedit db init
    actinoedit db import-genome --name my_strep --genome ...
    actinoedit db save-guides --project myproject results/xxx_guides.csv
"""

from actinoedit.db.config import get_db_url, is_postgres, load_config
from actinoedit.db.crud import (
    create_design_run,
    create_project,
    delete_genome,
    delete_organism,
    delete_project,
    export_project_guides,
    get_genes_for_genome,
    get_genome,
    get_organism,
    get_project,
    get_project_guides,
    get_validation_results,
    import_genome,
    link_genome_to_organism,
    link_project_genome,
    link_project_organism,
    list_design_runs,
    list_genomes,
    list_genomes_for_organism,
    list_organisms,
    list_projects,
    list_projects_for_organism,
    list_saved_guides,
    save_genes,
    save_genome,
    save_guides_from_result,
    save_organism,
    save_validation_result,
    update_organism,
    update_project,
)
from actinoedit.db.database import get_connection, init_database
from actinoedit.db.migrations import get_database_status, upgrade_database
from actinoedit.db.session import use_db_url

__all__ = [
    "get_connection",
    "init_database",
    "upgrade_database",
    "get_database_status",
    "create_design_run",
    "list_design_runs",
    "get_db_url",
    "use_db_url",
    "is_postgres",
    "load_config",
    "save_genome",
    "save_guides_from_result",
    "list_projects",
    "get_project",
    "update_project",
    "link_project_organism",
    "link_project_genome",
    "get_project_guides",
    "list_saved_guides",
    "import_genome",
    "export_project_guides",
    "list_genomes",
    "get_genome",
    "link_genome_to_organism",
    "list_genomes_for_organism",
    "get_genes_for_genome",
    "save_genes",
    "delete_project",
    "create_project",
    "list_organisms",
    "get_organism",
    "list_projects_for_organism",
    "save_organism",
    "update_organism",
    "save_validation_result",
    "get_validation_results",
    "delete_organism",
    "delete_genome",
]
