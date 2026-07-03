"""Page definitions for ActinoEdit web application."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from nicegui import ui

from actinoedit.web import db_service
from actinoedit.web.components import (
    create_crispr_params,
    create_db_status_banner,
    create_download_buttons,
    create_empty_result_panel,
    create_error_display,
    create_file_inputs,
    create_footer,
    create_header,
    create_profile_selector,
    create_progress_panel,
    create_results_table,
    create_summary_panel,
    create_target_input,
    create_task_status_panel,
)
from actinoedit.web.runner import (
    autosave_design_reports,
    build_design_run_meta,
    cancel_design,
    get_profile_names,
    run_design_background,
)
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

        create_db_status_banner()

        # Input section
        create_file_inputs(state)
        create_profile_selector(state, get_profile_names())
        create_crispr_params(state)
        create_target_input(state)

        with ui.row().classes("w-full gap-2"):
            ui.button(
                "Run Design",
                icon="play_arrow",
                on_click=lambda: _run_design_handler(state),
            ).props("color=primary size-lg").classes("flex-1")
            ui.button(
                "Cancel",
                icon="stop",
                on_click=lambda: cancel_design(state),
            ).props("color=negative outline").bind_enabled_from(state, "show_progress")

        # Output section
        create_error_display(state)
        create_task_status_panel(state)
        create_progress_panel(state)
        create_empty_result_panel(state)
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
                    try:
                        n = db_service.save_design_to_project(
                            res,
                            proj_name.value or "web_design",
                            design_run_meta=build_design_run_meta(state, res),
                        )
                        ui.notify(f"Saved {n} guides to DB project", type="positive")
                    except Exception as e:
                        ui.notify(str(e), type="negative")
            ui.button("Save current guides to DB", on_click=save_now).props("size=sm color=green")

    create_footer()


def _run_design_handler(state: WebState) -> None:
    """Handle design run button click (background thread with cancel/timeout)."""

    def _on_complete(result: Any, error: str | None) -> None:
        if error:
            ui.notify(error, type="negative")
            return
        if result is None:
            ui.notify(state.status_message or "Design did not complete", type="warning")
            return

        if result.cancelled:
            ui.notify(state.status_message or "Design cancelled", type="warning")
            return

        try:
            autosave_design_reports(state, result)
            ui.notify(f"Reports auto-saved to {state.report_output_dir}/", type="info")
        except Exception as save_err:
            ui.notify(f"Auto-save skipped: {save_err}", type="warning")

        if result.warnings:
            ui.notify(f"Design complete with {len(result.warnings)} warnings", type="warning")
        elif result.guide_candidates:
            ui.notify(
                f"Design complete: {len(result.guide_candidates)} guides found",
                type="positive",
            )
        else:
            ui.notify("Design finished with no guide candidates", type="warning")

    try:
        run_design_background(state, on_complete=_on_complete)
        ui.notify("Design started", type="info")
    except Exception as e:
        state.error_message = f"Unexpected error: {e}"
        state.task_status = "failed"
        traceback.print_exc()
        ui.notify(f"Error: {e}", type="negative")


def create_demo_page(
    state: WebState,
    *,
    demo_banner: bool = False,
    auto_run: bool = False,
) -> None:
    """Create demo page with pre-filled example data.

    Args:
        state: Application state.
        demo_banner: Show one-click demo banner (``actinoedit-web --demo``).
        auto_run: Automatically run design when the page loads.
    """
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Demo Mode").classes("text-h5 text-primary")
        ui.label("Try ActinoEdit with example Streptomyces data").classes("text-subtitle1 text-grey-7")

        if demo_banner:
            ui.chip(
                "One-click demo: Streptomyces example loaded — click Run Design or wait for auto-run",
                icon="rocket_launch",
                color="positive",
            ).classes("w-full")

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

        if auto_run:
            ui.timer(0.5, lambda: _run_design_handler(state), once=True)

    create_footer()


def _load_demo(state: WebState) -> None:
    """Load demo data into state.

    Args:
        state: Application state.
    """
    from actinoedit.web.demo import load_demo_state

    load_demo_state(state)
    ui.notify("Demo data loaded", type="info")


def create_projects_page(state: WebState) -> None:
    """Create full CRUD page for DB projects, genes, and saving designs."""
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Projects & Database (Local SQLite)").classes("text-h5 text-primary")

        if not db_service.is_db_available():
            ui.label(db_service.db_unavailable_message()).classes("text-negative")
            return

        _render_project_create_card(state)
        _render_project_export_card(state)
        _render_projects_list(state)
        _render_organisms_preview()
        _render_genomes_preview()

    create_footer()


def _render_project_create_card(state: WebState) -> None:
    with ui.card().classes("w-full"):
        ui.label("Create New Project").classes("text-h6")
        new_name = ui.input("Project name", placeholder="my_crispr_project").classes("w-full")
        new_desc = ui.input("Description (optional)").classes("w-full")
        org_options = [""] + db_service.organism_name_options()
        genome_options = [""] + db_service.genome_name_options()
        link_org = ui.select(org_options, label="Link organism (optional)", value="").classes("w-full")
        link_genome = ui.select(genome_options, label="Link genome (optional)", value="").classes("w-full")

        def do_create() -> None:
            if not new_name.value:
                ui.notify("Name required", type="negative")
                return
            try:
                db_service.create_project_record(
                    new_name.value,
                    new_desc.value or "",
                    state.profile_name,
                    organism_name=link_org.value or None,
                    genome_name=link_genome.value or None,
                )
                ui.notify(f"Project '{new_name.value}' created", type="positive")
                new_name.value = ""
            except Exception as exc:
                ui.notify(str(exc), type="negative")

        ui.button("Create Project", on_click=do_create).props("color=primary")


def _render_project_export_card(state: WebState) -> None:
    with ui.card().classes("w-full"):
        ui.label("Export DB Reports").classes("text-h6")
        exp_proj = ui.input("Project to export guides").classes("w-full")
        exp_dir = ui.input(
            "Export directory",
            value=state.export_output_dir,
        ).classes("w-full").bind_value(state, "export_output_dir")
        exp_name = ui.input(
            "Output filename (optional, defaults to <project>_guides.csv)",
            value="",
        ).classes("w-full")

        def do_export_db() -> None:
            if not exp_proj.value:
                return
            if exp_name.value.strip():
                out = Path(exp_dir.value or state.export_output_dir) / exp_name.value.strip()
            else:
                out = db_service.default_project_export_path(
                    exp_proj.value,
                    base_dir=exp_dir.value or state.export_output_dir,
                    suffix="_db",
                )
            try:
                db_service.export_guides_csv(exp_proj.value, out)
                ui.notify(f"Exported to {out}")
            except Exception as e:
                ui.notify(str(e), type="negative")

        ui.button("Export Project Guides", on_click=do_export_db)


def _render_projects_list(state: WebState) -> None:
    projs = db_service.list_projects_summary()
    psearch = ui.input("Search projects", value="").classes("w-full")
    pfiltered = db_service.filter_projects(projs, psearch.value)
    if not pfiltered:
        return

    ui.label("Projects").classes("text-h6 mt-4")
    for p in pfiltered:
        pname = p.get("name", "")
        org_label = p.get("organism_name") or "—"
        genome_label = p.get("genome_name") or "—"
        guide_count = p.get("guide_count", 0)
        with ui.expansion(
            f"{pname} · {guide_count} guides · org: {org_label} · genome: {genome_label}",
            icon="folder",
        ).classes("w-full"):
            ui.label(
                f"Profile: {p.get('organism_profile', '') or '—'} · "
                f"Organism: {org_label} · Genome: {genome_label}",
            ).classes("text-caption text-grey-7")
            guides = db_service.get_project_guides_summary(pname, limit=20)
            if guides:
                cols = [
                    {"name": col, "label": col, "field": col}
                    for col in db_service.GUIDE_TABLE_COLUMNS
                ]
                ui.table(
                    columns=cols,
                    rows=db_service.guides_to_table_rows(guides),
                    pagination=5,
                ).classes("w-full")
            else:
                ui.label("No saved guides yet.")

            org_options = [""] + db_service.organism_name_options()
            genome_options = [""] + db_service.genome_name_options()
            with ui.row().classes("w-full gap-2 items-end"):
                rel_org = ui.select(
                    org_options,
                    label="Organism",
                    value=p.get("organism_name") or "",
                ).classes("flex-1")
                rel_genome = ui.select(
                    genome_options,
                    label="Genome",
                    value=p.get("genome_name") or "",
                ).classes("flex-1")

                def do_link(
                    n: str = pname,
                    org_select: Any = rel_org,
                    genome_select: Any = rel_genome,
                ) -> None:
                    try:
                        db_service.update_project_links(
                            n,
                            organism_name=org_select.value or "",
                            genome_name=genome_select.value or "",
                        )
                        ui.notify(f"Updated links for {n}", type="positive")
                    except Exception as exc:
                        ui.notify(str(exc), type="negative")

                ui.button("Update Links", on_click=do_link).props("size=sm")

            with ui.row():
                ui.button(
                    "Export CSV",
                    on_click=lambda n=pname: _export_project(n, export_dir=state.export_output_dir),
                ).props("size=sm")

                def do_delete(n: str = pname) -> None:
                    _confirm_delete(
                        title=f"Delete project '{n}'?",
                        message="This permanently removes the project and all saved guides.",
                        on_confirm=lambda: _delete_project_confirmed(n),
                    )

                ui.button("Delete Project", on_click=do_delete, color="red").props("size=sm outline")

            if state.result and state.result.guide_candidates:

                def do_save(n: str = pname) -> None:
                    res = state.result
                    if not res:
                        return
                    try:
                        n_saved = db_service.save_design_to_project(
                            res,
                            n,
                            replace_existing=False,
                            design_run_meta=build_design_run_meta(state, res),
                        )
                        ui.notify(f"Saved {n_saved} guides to {n}", type="positive")
                    except Exception as ex:
                        ui.notify(f"Save failed: {ex}", type="negative")

                ui.button(
                    f"Save Current Design to '{pname}'",
                    on_click=do_save,
                    color="green",
                ).props("size=sm")


def _render_organisms_preview() -> None:
    orgs = db_service.list_organisms_summary()
    if not orgs:
        return
    ui.label("Organisms").classes("text-h6 mt-4")
    ocols = [
        {"name": col, "label": col.title(), "field": col}
        for col in ("name", "species", "strain")
    ]
    orows = db_service.organisms_to_table_rows(orgs[:10])
    ui.table(columns=ocols, rows=orows, pagination=5).classes("w-full")


def _render_genomes_preview() -> None:
    genomes = db_service.list_genomes_summary()
    if not genomes:
        return
    ui.label("Imported Genomes & Genes").classes("text-h6 mt-4")
    for g in genomes[:5]:
        gid = g.get("id")
        with ui.expansion(f"Genome: {g.get('name')} ({g.get('contigs')} contigs)", icon="dna"):
            genes = db_service.get_genome_genes(gid, limit=10) if gid else []
            if genes:
                gcols = [
                    {"name": col, "label": col.replace("_", " ").title(), "field": col}
                    for col in db_service.GENE_TABLE_COLUMNS
                ]
                ui.table(columns=gcols, rows=genes, pagination=5)
            else:
                ui.label("No genes stored (import with annotation).")


def _export_project(project_name: str, *, export_dir: str = "results/db_exports") -> None:
    try:
        out = db_service.default_project_export_path(
            project_name,
            base_dir=export_dir,
        )
        db_service.export_guides_csv(project_name, out)
        ui.notify(f"Exported to {out}", type="positive")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")


def _confirm_delete(
    *,
    title: str,
    message: str,
    on_confirm: Any,
) -> None:
    """Show a confirmation dialog before destructive DB actions."""
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-h6")
        ui.label(message).classes("text-body2")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete",
                on_click=lambda: (on_confirm(), dialog.close()),
                color="negative",
            )
    dialog.open()


def _delete_project_confirmed(project_name: str) -> None:
    if db_service.delete_project_record(project_name):
        ui.notify(f"Deleted {project_name}", type="warning")
    else:
        ui.notify("Delete failed", type="negative")


def create_organisms_page(state: WebState) -> None:
    """Standalone page for browsing/creating organisms."""
    create_header()
    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Organisms").classes("text-h5 text-primary")

        if not db_service.is_db_available():
            ui.label(db_service.db_unavailable_message()).classes("text-negative")
            return

        with ui.card().classes("w-full"):
            ui.label("Add Organism").classes("text-h6")
            o_name = ui.input("Name").classes("w-full")
            o_species = ui.input("Species").classes("w-full")
            o_strain = ui.input("Strain").classes("w-full")

            def do_add() -> None:
                if o_name.value:
                    db_service.add_organism(o_name.value, o_species.value, o_strain.value)
                    ui.notify("Organism added")

            ui.button("Add", on_click=do_add)

        with ui.card().classes("w-full"):
            ui.label("Delete Organism").classes("text-h6")
            del_name = ui.input("Name to delete").classes("w-full")

            def do_del() -> None:
                if not del_name.value:
                    return
                name = del_name.value

                def _confirmed() -> None:
                    if db_service.remove_organism(name):
                        ui.notify(f"Deleted {name}")
                        del_name.value = ""
                    else:
                        ui.notify("Not found or delete failed")

                _confirm_delete(
                    title=f"Delete organism '{name}'?",
                    message="This permanently removes the organism record.",
                    on_confirm=_confirmed,
                )

            ui.button("Delete", on_click=do_del, color="negative")

        with ui.card().classes("w-full"):
            ui.label("Update Organism").classes("text-h6")
            up_name = ui.input("Name").classes("w-full")
            up_species = ui.input("New Species").classes("w-full")
            up_strain = ui.input("New Strain").classes("w-full")

            def do_up() -> None:
                if up_name.value:
                    if db_service.patch_organism(
                        up_name.value,
                        up_species.value or None,
                        up_strain.value or None,
                    ):
                        ui.notify(f"Updated {up_name.value}")
                    else:
                        ui.notify("Not found")

            ui.button("Update", on_click=do_up)

        orgs = db_service.list_organisms_summary()
        search_term = ui.input(
            "Search organisms (name/species/strain)",
            value="",
        ).classes("w-full")
        filtered = db_service.filter_organisms(orgs, search_term.value)
        table = ui.table(
            columns=[
                {"name": col, "label": col, "field": col}
                for col in db_service.ORGANISM_TABLE_COLUMNS
            ],
            rows=db_service.organisms_to_table_rows(filtered),
        )

        def do_search() -> None:
            table.rows = db_service.organisms_to_table_rows(
                db_service.filter_organisms(orgs, search_term.value),
            )
            table.update()

        ui.button("Search", on_click=do_search)

        def export_orgs() -> None:
            ui.download(
                db_service.export_organisms_csv_bytes(
                    db_service.filter_organisms(orgs, search_term.value),
                ),
                "organisms.csv",
            )

        ui.button("Export Filtered Organisms CSV", on_click=export_orgs)

        ui.label("Organism Details").classes("text-h6 mt-4")
        for org in filtered[:20]:
            oname = org.get("name", "")
            genomes = db_service.list_genomes_for_organism_summary(oname)
            projects = db_service.list_projects_for_organism_summary(oname)
            with ui.expansion(
                f"{oname} · {len(genomes)} genomes · {len(projects)} projects",
                icon="biotech",
            ).classes("w-full"):
                if genomes:
                    ui.label("Linked genomes").classes("text-subtitle2")
                    gcols = [
                        {"name": col, "label": col, "field": col}
                        for col in ("name", "contigs", "total_length")
                    ]
                    ui.table(
                        columns=gcols,
                        rows=[{c: g.get(c, "") for c in ("name", "contigs", "total_length")} for g in genomes],
                        pagination=5,
                    )
                else:
                    ui.label("No linked genomes.")

                if projects:
                    ui.label("Linked projects").classes("text-subtitle2 mt-2")
                    ui.table(
                        columns=[
                            {"name": "name", "label": "Project", "field": "name"},
                            {"name": "guide_count", "label": "Guides", "field": "guide_count"},
                        ],
                        rows=[{"name": pr.get("name", ""), "guide_count": pr.get("guide_count", 0)} for pr in projects],
                        pagination=5,
                    )
    create_footer()


def create_genomes_page(state: WebState) -> None:
    """Standalone page for genomes."""
    create_header()
    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-4"):
        ui.label("Genomes").classes("text-h5 text-primary")

        if not db_service.is_db_available():
            ui.label(db_service.db_unavailable_message()).classes("text-negative")
            return

        with ui.card().classes("w-full"):
            ui.label("Import Genome").classes("text-h6")
            imp_name = ui.input("Genome name").classes("w-full")
            imp_genome = ui.input("FASTA path").classes("w-full")
            imp_ann = ui.input("Annotation path (GFF/GBK, optional)").classes("w-full")
            org_options = [""] + db_service.organism_name_options()
            imp_org = ui.select(org_options, label="Link organism (optional)", value="").classes("w-full")

            def do_import() -> None:
                if not imp_name.value or not imp_genome.value:
                    ui.notify("Name and FASTA path required", type="negative")
                    return
                try:
                    summary = db_service.import_genome_record(
                        imp_name.value,
                        imp_genome.value,
                        imp_ann.value or None,
                        organism_name=imp_org.value or None,
                    )
                    ui.notify(
                        f"Imported {summary['name']}: {summary['contigs']} contigs, "
                        f"{summary.get('features_imported', 0)} features",
                        type="positive",
                    )
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            ui.button("Import Genome", on_click=do_import).props("color=primary")

        with ui.card().classes("w-full"):
            ui.label("Link Genome to Organism").classes("text-h6")
            link_g = ui.input("Genome name").classes("w-full")
            link_o = ui.select(org_options, label="Organism", value="").classes("w-full")

            def do_link() -> None:
                if not link_g.value or not link_o.value:
                    ui.notify("Genome and organism required", type="negative")
                    return
                try:
                    if db_service.link_genome_organism(link_g.value, link_o.value):
                        ui.notify(f"Linked {link_g.value} → {link_o.value}", type="positive")
                    else:
                        ui.notify("Genome not found", type="negative")
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            ui.button("Link", on_click=do_link)

        with ui.card().classes("w-full"):
            ui.label("Delete Genome").classes("text-h6")
            del_g = ui.input("Genome name to delete").classes("w-full")

            def do_del_g() -> None:
                if not del_g.value:
                    return
                name = del_g.value

                def _confirmed() -> None:
                    if db_service.remove_genome(name):
                        ui.notify(f"Deleted genome {name}")
                        del_g.value = ""
                    else:
                        ui.notify("Delete failed", type="negative")

                _confirm_delete(
                    title=f"Delete genome '{name}'?",
                    message="This permanently removes the genome and linked gene records.",
                    on_confirm=_confirmed,
                )

            ui.button("Delete Genome", on_click=do_del_g, color="negative")

        genomes = db_service.list_genomes_summary()
        gsearch = ui.input("Search genomes (name)", value="").classes("w-full")
        gfiltered = db_service.filter_genomes(genomes, gsearch.value)
        if gfiltered:
            cols = [
                {"name": col, "label": col, "field": col}
                for col in db_service.GENOME_TABLE_COLUMNS
            ]
            ui.table(columns=cols, rows=db_service.genomes_to_table_rows(gfiltered))

            def export_genomes() -> None:
                ui.download(
                    db_service.export_genomes_csv_bytes(
                        db_service.filter_genomes(genomes, gsearch.value),
                    ),
                    "genomes.csv",
                )

            ui.button("Export Filtered Genomes CSV", on_click=export_genomes)

            ui.label("Genome Details").classes("text-h6 mt-4")
            for genome in gfiltered[:20]:
                gname = genome.get("name", "")
                gid = genome.get("id")
                with ui.expansion(
                    f"{gname} · organism: {genome.get('organism_name') or '—'}",
                    icon="dna",
                ).classes("w-full"):
                    genes = db_service.get_genome_genes(gid, limit=10) if gid else []
                    if genes:
                        gcols = [
                            {"name": col, "label": col.replace("_", " ").title(), "field": col}
                            for col in db_service.GENE_TABLE_COLUMNS
                        ]
                        ui.table(columns=gcols, rows=genes, pagination=5)
                    else:
                        ui.label("No genes stored (import with annotation).")
        else:
            ui.label("No genomes yet. Import via the form above or CLI.")
    create_footer()
