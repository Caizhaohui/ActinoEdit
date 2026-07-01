"""Reusable UI components for ActinoEdit web application."""

from __future__ import annotations

from nicegui import ui

from actinoedit.web.state import WebState


def create_header() -> None:
    """Create the application header."""
    with ui.header().classes("bg-blue-900"):
        ui.label("ActinoEdit").classes("text-h4 text-white font-bold")
        ui.label("CRISPR Design Toolkit for Actinomycetes").classes("text-subtitle2 text-blue-200 ml-4")
        ui.link("Projects (DB)", "/projects").classes("text-white ml-auto mr-4")
        ui.link("Design", "/").classes("text-white")


def create_footer() -> None:
    """Create the application footer."""
    with ui.footer().classes("bg-grey-2"):
        ui.label("ActinoEdit v0.2.0 - Local CRISPR Design Tool (with DB)").classes("text-caption text-grey-7")


def create_file_inputs(state: WebState) -> None:
    """Create file input section with upload support.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full"):
        ui.label("Input Files").classes("text-h6")

        def handle_genome_upload(e):  # type: ignore[no-untyped-def]
            # NiceGUI upload event
            import os
            import shutil
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".fasta") as tmp:
                shutil.copyfileobj(e.content, tmp)
                state.genome_path = tmp.name
            ui.notify(f"Uploaded genome: {os.path.basename(state.genome_path)}")

        def handle_ann_upload(e):  # type: ignore[no-untyped-def]
            import os
            import shutil
            import tempfile
            suffix = ".gff" if state.annotation_format == "gff" else ".gbk"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(e.content, tmp)
                state.annotation_path = tmp.name
            ui.notify(f"Uploaded annotation: {os.path.basename(state.annotation_path)}")

        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1"):
                ui.upload(label="Upload Genome FASTA", on_upload=handle_genome_upload, auto_upload=True).classes("w-full")
                ui.input("or path", value=state.genome_path).bind_value(state, "genome_path").classes("w-full")

            ui.select(
                ["gff", "gbk"],
                label="Annotation Format",
                value=state.annotation_format,
            ).classes("w-32").bind_value(state, "annotation_format")

        with ui.column().classes("w-full"):
            ui.upload(label="Upload Annotation", on_upload=handle_ann_upload, auto_upload=True).classes("w-full")
            ui.input("or path", value=state.annotation_path).bind_value(state, "annotation_path").classes("w-full")


def create_profile_selector(state: WebState, profiles: list[str]) -> None:
    """Create organism profile selector.

    Args:
        state: Application state.
        profiles: List of available profile names.
    """
    with ui.card().classes("w-full"):
        ui.label("Organism Profile").classes("text-h6")
        ui.select(
            profiles,
            label="Profile",
            value=state.profile_name,
        ).classes("w-full").bind_value(state, "profile_name")


def create_crispr_params(state: WebState) -> None:
    """Create CRISPR parameter inputs.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full"):
        ui.label("CRISPR Parameters").classes("text-h6")

        with ui.row().classes("w-full gap-4"):
            ui.input(
                label="PAM Pattern",
                value=state.pam,
                placeholder="NGG",
            ).classes("flex-1").bind_value(state, "pam")

            ui.number(
                label="Spacer Length",
                value=state.spacer_length,
                min=15,
                max=30,
                step=1,
            ).classes("flex-1").bind_value(state, "spacer_length")

            ui.number(
                label="Max Mismatches",
                value=state.max_mismatches,
                min=0,
                max=5,
                step=1,
            ).classes("flex-1").bind_value(state, "max_mismatches")


def create_target_input(state: WebState) -> None:
    """Create target gene input.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full"):
        ui.label("Target").classes("text-h6")
        ui.input(
            label="Target Gene",
            placeholder="locus_tag, gene name, or contig:start-end",
            value=state.target,
        ).classes("w-full").bind_value(state, "target")

    # Optional BGC annotation (actinomycete feature)
    with ui.card().classes("w-full"):
        ui.input(
            label="BGC Regions (optional .bed/.tsv)",
            placeholder="Path to BGC regions for context (e.g. antiSMASH)",
            value=state.bgc_path,
        ).classes("w-full").bind_value(state, "bgc_path")


def create_progress_panel(state: WebState) -> None:
    """Create progress display panel.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full").bind_visibility_from(state, "is_running"):
        ui.label("Progress").classes("text-h6")
        log_area = ui.log(max_lines=20).classes("w-full h-48")
        for msg in state.progress_messages:
            log_area.push(msg)


def create_error_display(state: WebState) -> None:
    """Create error message display.

    Args:
        state: Application state.
    """
    ui.label().bind_text_from(state, "error_message").classes("text-negative text-h6").bind_visibility_from(
        state, "error_message"
    )


def create_summary_panel(state: WebState) -> None:
    """Create result summary panel.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full").bind_visibility_from(state, "has_result"):
        ui.label("Design Summary").classes("text-h6")

        if state.result and state.result.target_region:
            tr = state.result.target_region
            with ui.row().classes("gap-4"):
                ui.chip(f"Target: {tr.display_label}", color="primary")
                ui.chip(f"Region: {tr.contig}:{tr.start}-{tr.end}", color="secondary")
                ui.chip(f"Guides: {state.guide_count}", color="positive")

        if state.result and state.result.warnings:
            with ui.expansion("Warnings", icon="warning").classes("w-full"):
                for w in state.result.warnings:
                    ui.label(w).classes("text-warning")


def create_results_table(state: WebState) -> None:
    """Create interactive results table.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full").bind_visibility_from(state, "has_result"):
        ui.label("Guide Candidates").classes("text-h6")

        # Filter controls
        with ui.row().classes("w-full gap-4 mb-4"):
            ui.select(
                ["all", "excellent", "good", "caution", "avoid"],
                label="Recommendation Filter",
                value=state.filter_recommendation,
            ).classes("w-48").bind_value(state, "filter_recommendation")

            ui.number(
                label="Max Off-targets (-1=all)",
                value=state.filter_max_offtargets,
                min=-1,
            ).classes("w-48").bind_value(state, "filter_max_offtargets")

        # Build table data
        columns = [
            {"name": "guide_id", "label": "Guide ID", "field": "guide_id", "sortable": True},
            {"name": "contig", "label": "Contig", "field": "contig", "sortable": True},
            {"name": "position", "label": "Position", "field": "position", "sortable": True},
            {"name": "strand", "label": "Strand", "field": "strand", "sortable": True},
            {"name": "spacer", "label": "Spacer (20bp)", "field": "spacer", "sortable": False},
            {"name": "pam", "label": "PAM", "field": "pam", "sortable": True},
            {"name": "gc", "label": "GC%", "field": "gc", "sortable": True},
            {"name": "off_targets", "label": "Off-targets", "field": "off_targets", "sortable": True},
            {"name": "score", "label": "Score", "field": "score", "sortable": True},
            {"name": "recommendation", "label": "Recommendation", "field": "recommendation", "sortable": True},
        ]

        rows = []
        for guide, score, ot_count in state.filtered_guides:
            rows.append({
                "guide_id": guide.guide_id,
                "contig": guide.contig,
                "position": f"{guide.start}-{guide.end}",
                "strand": guide.strand,
                "spacer": guide.spacer[:20] + "..." if len(guide.spacer) > 20 else guide.spacer,
                "pam": guide.pam,
                "gc": f"{guide.gc_content:.1%}",
                "off_targets": ot_count,
                "score": f"{score.final_score:.3f}" if score else "N/A",
                "recommendation": score.recommendation if score else "N/A",
            })

        table = ui.table(
            columns=columns,
            rows=rows,
            row_key="guide_id",
            pagination=20,
        ).classes("w-full")

        # Color code recommendations
        table.add_slot("body-cell-recommendation", """
            <q-td :props="props">
                <q-badge
                    :color="props.value === 'excellent' ? 'green' :
                            props.value === 'good' ? 'blue' :
                            props.value === 'caution' ? 'orange' : 'red'"
                    :label="props.value"
                />
            </q-td>
        """)


def create_download_buttons(state: WebState) -> None:
    """Create download buttons for results.

    Args:
        state: Application state.
    """
    with ui.card().classes("w-full").bind_visibility_from(state, "has_result"):
        ui.label("Download Results").classes("text-h6")

        with ui.row().classes("gap-4"):
            ui.button("Download CSV", icon="download", on_click=lambda: _download_csv(state)).props("color=primary")
            ui.button("Download Excel", icon="download", on_click=lambda: _download_excel(state)).props("color=secondary")
            ui.button("Download HTML", icon="download", on_click=lambda: _download_html(state)).props("color=positive")


def _download_csv(state: WebState) -> None:
    """Generate CSV via reports module and trigger download."""
    if state.result is None:
        return
    import uuid
    from pathlib import Path

    from actinoedit.reports import write_csv_report

    tmp_dir = Path("/tmp") / "actinoedit_downloads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"guides_{uuid.uuid4().hex[:8]}.csv"
    write_csv_report(
        state.result.guide_candidates,
        tmp_path,
        state.result.guide_scores,
        state.result.off_target_hits,
    )
    ui.download(str(tmp_path), filename="actinoedit_guides.csv")
    ui.notify("CSV download started", type="positive")


def _download_excel(state: WebState) -> None:
    """Generate Excel via reports and trigger download."""
    if state.result is None:
        return
    import uuid
    from pathlib import Path

    from actinoedit.reports import write_excel_report

    tmp_dir = Path("/tmp") / "actinoedit_downloads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"report_{uuid.uuid4().hex[:8]}.xlsx"
    write_excel_report(
        state.result.guide_candidates,
        tmp_path,
        state.result.guide_scores,
        state.result.off_target_hits,
        {"source": "ActinoEdit Web"},
        state.result.warnings,
    )
    ui.download(str(tmp_path), filename="actinoedit_report.xlsx")
    ui.notify("Excel download started", type="positive")


def _download_html(state: WebState) -> None:
    """Generate HTML report via reports module and trigger download."""
    if state.result is None:
        return
    import uuid
    from pathlib import Path

    from actinoedit.reports import write_html_report

    tmp_dir = Path("/tmp") / "actinoedit_downloads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"report_{uuid.uuid4().hex[:8]}.html"
    write_html_report(
        state.result.guide_candidates,
        tmp_path,
        state.result.target_region,
        state.result.guide_scores,
        state.result.off_target_hits,
        {"source": "ActinoEdit Web"},
        state.result.warnings,
    )
    ui.download(str(tmp_path), filename="actinoedit_report.html")
    ui.notify("HTML report download started", type="positive")
