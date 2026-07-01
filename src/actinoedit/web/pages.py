"""Page definitions for ActinoEdit web application."""

from __future__ import annotations

import traceback

from nicegui import ui

from actinoedit.web.components import (
    create_crispr_params,
    create_download_buttons,
    create_error_display,
    create_file_inputs,
    create_footer,
    create_header,
    create_profile_selector,
    create_progress_panel,
    create_results_table,
    create_summary_panel,
    create_target_input,
)
from actinoedit.web.runner import get_profile_names, run_design
from actinoedit.web.state import WebState


def create_main_page(state: WebState) -> None:
    """Create the main design page.

    Args:
        state: Application state.
    """
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("CRISPR Guide RNA Design").classes("text-h5 text-primary")
        ui.label("Design sgRNAs for actinomycetes and industrial microbes").classes("text-subtitle1 text-grey-7")

        # Input section
        create_file_inputs(state)
        create_profile_selector(state, get_profile_names())
        create_crispr_params(state)
        create_target_input(state)

        # Run button
        ui.button(
            "Run Design",
            icon="play_arrow",
            on_click=lambda: _run_design_handler(state),
        ).props("color=primary size-lg").classes("w-full")

        # Output section
        create_error_display(state)
        create_progress_panel(state)
        create_summary_panel(state)
        create_results_table(state)
        create_download_buttons(state)

        # Quick DB save from design (full Web CRUD)
        with ui.card().classes("w-full").bind_visibility_from(state, "has_result"):
            ui.label("Save to Local DB Project").classes("text-h6")
            proj_name = ui.input("Project name", value="web_design").classes("w-64")
            def save_now() -> None:
                res = state.result
                if res:
                    from actinoedit.db import save_guides_from_result
                    try:
                        n = save_guides_from_result(res, proj_name.value or "web_design")
                        ui.notify(f"Saved {n} guides to DB project", type="positive")
                    except Exception as e:
                        ui.notify(str(e), type="negative")
            ui.button("Save current guides to DB", on_click=save_now).props("size=sm color=green")

    create_footer()


def _run_design_handler(state: WebState) -> None:
    """Handle design run button click.

    Args:
        state: Application state.
    """
    state.reset()
    state.is_running = True

    try:
        result = run_design(state)
        state.result = result

        # Auto-save reports locally for convenience
        try:
            from pathlib import Path

            from actinoedit.reports import write_design_reports
            auto_dir = Path("results") / "web_autosave"
            auto_prefix = str(auto_dir / "last_design")
            write_design_reports(
                result.guide_candidates,
                result.guide_scores,
                result.off_target_hits,
                result.target_region,
                result.warnings,
                auto_prefix,
                {"source": "web-auto"},
            )
            ui.notify("Reports auto-saved to results/web_autosave/", type="info")
        except Exception as save_err:
            ui.notify(f"Auto-save skipped: {save_err}", type="warning")

        if result.warnings:
            ui.notify(f"Design complete with {len(result.warnings)} warnings", type="warning")
        else:
            ui.notify(f"Design complete: {len(result.guide_candidates)} guides found", type="positive")

    except FileNotFoundError as e:
        state.error_message = str(e)
        ui.notify(str(e), type="negative")
    except ValueError as e:
        state.error_message = str(e)
        ui.notify(str(e), type="negative")
    except Exception as e:
        state.error_message = f"Unexpected error: {e}"
        traceback.print_exc()
        ui.notify(f"Error: {e}", type="negative")
    finally:
        state.is_running = False


def create_demo_page(state: WebState) -> None:
    """Create demo page with pre-filled example data.

    Args:
        state: Application state.
    """
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Demo Mode").classes("text-h5 text-primary")
        ui.label("Try ActinoEdit with example Streptomyces data").classes("text-subtitle1 text-grey-7")

        ui.button(
            "Load Demo Data",
            icon="science",
            on_click=lambda: _load_demo(state),
        ).props("color=secondary").classes("w-full")

        # Same layout as main page
        create_file_inputs(state)
        create_profile_selector(state, get_profile_names())
        create_crispr_params(state)
        create_target_input(state)

        ui.button(
            "Run Design",
            icon="play_arrow",
            on_click=lambda: _run_design_handler(state),
        ).props("color=primary size-lg").classes("w-full")

        create_error_display(state)
        create_progress_panel(state)
        create_summary_panel(state)
        create_results_table(state)
        create_download_buttons(state)

    create_footer()


def _load_demo(state: WebState) -> None:
    """Load demo data into state.

    Args:
        state: Application state.
    """
    from pathlib import Path

    examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
    state.genome_path = str(examples_dir / "demo_genome.fasta")
    state.annotation_path = str(examples_dir / "demo_annotation.gff")
    state.annotation_format = "gff"
    state.profile_name = "streptomyces"
    state.pam = "NGG"
    state.spacer_length = 20
    state.max_mismatches = 3
    state.target = "geneA"

    ui.notify("Demo data loaded", type="info")


def create_projects_page(state: WebState) -> None:
    """Create full CRUD page for DB projects, genes, and saving designs."""
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Projects & Database (Local SQLite)").classes("text-h5 text-primary")

        if not _db_available():
            ui.label("DB not available. Run 'actinoedit db init' from CLI first.").classes("text-negative")
            return

        from actinoedit.db import (
            create_project as db_create_project,
        )
        from actinoedit.db import (
            delete_project,
            get_genes_for_genome,
            get_project_guides,
            list_genomes,
            list_projects,
            save_guides_from_result,
        )

        # Create project
        with ui.card().classes("w-full"):
            ui.label("Create New Project").classes("text-h6")
            new_name = ui.input("Project name", placeholder="my_crispr_project").classes("w-full")
            new_desc = ui.input("Description (optional)").classes("w-full")
            def do_create() -> None:
                if not new_name.value:
                    ui.notify("Name required", type="negative")
                    return
                db_create_project(new_name.value, new_desc.value or "", state.profile_name)
                ui.notify(f"Project '{new_name.value}' created", type="positive")
                new_name.value = ""
                # refresh page manually if needed
            ui.button("Create Project", on_click=do_create).props("color=primary")

        # List projects with CRUD + guides
        projs = list_projects()
        if projs:
            ui.label("Projects").classes("text-h6 mt-4")
            for p in projs:
                pname = p.get("name", "")
                with ui.expansion(f"{pname} (profile: {p.get('organism_profile','')})", icon="folder").classes("w-full"):
                    # Guides
                    guides = get_project_guides(pname, limit=20)
                    if guides:
                        cols = [{"name": k, "label": k, "field": k} for k in ["guide_id", "contig", "start", "final_score", "recommendation", "bgc_context"]]
                        rows = [{k: g.get(k, "") for k in ["guide_id", "contig", "start", "final_score", "recommendation", "bgc_context"]} for g in guides]
                        ui.table(columns=cols, rows=rows, pagination=5).classes("w-full")
                    else:
                        ui.label("No saved guides yet.")

                    # Actions
                    with ui.row():
                        ui.button("Export CSV", on_click=lambda n=pname: _export_project(n)).props("size=sm")
                        def do_delete(n=pname) -> None:  # type: ignore[no-untyped-def]
                            if delete_project(n):
                                ui.notify(f"Deleted {n}", type="warning")
                                # manual page refresh recommended
                            else:
                                ui.notify("Delete failed", type="negative")
                        ui.button("Delete Project", on_click=do_delete, color="red").props("size=sm outline")

                    # Save current design if available
                    if state.result and state.result.guide_candidates:
                        def do_save(n=pname) -> None:  # type: ignore[no-untyped-def]
                            res = state.result
                            if res:
                                try:
                                    n_saved = save_guides_from_result(res, n, replace_existing=False)
                                    ui.notify(f"Saved {n_saved} guides to {n}", type="positive")
                                except Exception as ex:
                                    ui.notify(f"Save failed: {ex}", type="negative")
                        ui.button(f"Save Current Design to '{pname}'", on_click=do_save, color="green").props("size=sm")

        # Genomes & Genes (for import-genome use)
        genomes = list_genomes()
        if genomes:
            ui.label("Imported Genomes & Genes").classes("text-h6 mt-4")
            for g in genomes[:5]:  # limit
                gid = g.get("id")
                with ui.expansion(f"Genome: {g.get('name')} ({g.get('contigs')} contigs)", icon="dna"):
                    genes = get_genes_for_genome(genome_id=gid, limit=10) if gid else []
                    if genes:
                        gcols = [{"name": "locus_tag", "label": "Locus", "field": "locus_tag"},
                                 {"name": "gene_name", "label": "Gene", "field": "gene_name"},
                                 {"name": "contig", "label": "Contig", "field": "contig"},
                                 {"name": "start", "label": "Start", "field": "start"}]
                        grows = genes
                        ui.table(columns=gcols, rows=grows, pagination=5)
                    else:
                        ui.label("No genes stored (import with annotation).")

    create_footer()


def _db_available() -> bool:
    try:
        from actinoedit.db import list_projects
        list_projects()
        return True
    except Exception:
        return False


def _export_project(project_name: str) -> None:
    from pathlib import Path

    from actinoedit.db import export_project_guides
    try:
        out = Path("results") / "db_exports" / f"{project_name}_guides.csv"
        export_project_guides(project_name, str(out))
        ui.notify(f"Exported to {out}", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")
