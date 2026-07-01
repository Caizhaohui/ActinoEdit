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
    """Create a simple page to browse projects and saved guides from DB."""
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Saved Projects (Local DB)").classes("text-h5 text-primary")

        if not _db_available():
            ui.label("Database module not available or not initialized. Run 'actinoedit db init'.").classes("text-negative")
            return

        from actinoedit.db import get_project_guides, list_projects

        projs = list_projects()
        if not projs:
            ui.label("No projects found. Use CLI 'actinoedit db save-guides' or design from Web.").classes("text-grey")
            return

        for p in projs:
            with ui.expansion(f"Project: {p.get('name')} (id={p.get('id')})", icon="folder").classes("w-full"):
                guides = get_project_guides(p.get("name", ""), limit=30)
                if guides:
                    cols = [{"name": k, "label": k, "field": k} for k in ["guide_id", "contig", "start", "final_score", "recommendation", "bgc_context"]]
                    rows = [{k: g.get(k, "") for k in ["guide_id", "contig", "start", "final_score", "recommendation", "bgc_context"]} for g in guides]
                    ui.table(columns=cols, rows=rows, pagination=10).classes("w-full")
                else:
                    ui.label("No guides saved for this project yet.")

                name_val = p.get("name") or ""
                ui.button("Export CSV", on_click=lambda n=name_val: _export_project(n)).props("size=sm")

    create_footer()


def _db_available() -> bool:
    try:
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
