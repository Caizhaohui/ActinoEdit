"""ActinoEdit CLI - Command line interface for CRISPR guide RNA design."""

from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from actinoedit import __version__
from actinoedit.core.pipeline import DesignInput, run_design_pipeline
from actinoedit.reports import write_design_reports

# DB subcommand group (optional)
try:
    from actinoedit.db import (
        export_project_guides,
        import_genome,
        init_database,
        save_guides_from_result,
    )
    from actinoedit.db import (
        list_projects as db_list_projects,
    )
    from actinoedit.db.database import get_connection
    DB_AVAILABLE = True
except Exception:  # pragma: no cover
    DB_AVAILABLE = False

app = typer.Typer(
    name="actinoedit",
    help="CRISPR Design Toolkit for Actinomycetes and Industrial Microbes",
    add_completion=False,
)
console = Console()


def _exit_with_error(message: str) -> None:
    """Print error message and exit."""
    console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(1) from None


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]ActinoEdit[/bold blue] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """ActinoEdit: CRISPR Design Toolkit for Actinomycetes and Industrial Microbes."""
    pass


@app.command()
def design(
    genome: str = typer.Option(..., "--genome", "-g", help="Path to genome FASTA file"),
    gff: str | None = typer.Option(None, "--gff", help="Path to GFF3 annotation file"),
    gbk: str | None = typer.Option(None, "--gbk", help="Path to GenBank annotation file"),
    target: str = typer.Option(..., "--target", "-t", help="Target gene (locus_tag, gene name, or contig:start-end)"),
    profile: str | None = typer.Option(None, "--profile", "-r", help="Organism profile (streptomyces, actinomycete, ecoli, etc.)"),
    pam: str = typer.Option("NGG", "--pam", "-p", help="PAM pattern (overrides profile)"),
    spacer_length: int = typer.Option(20, "--spacer-length", "-s", help="Spacer length (overrides profile)"),
    max_mismatches: int = typer.Option(3, "--max-mismatches", "-m", help="Max mismatches for off-target search"),
    output_prefix: str = typer.Option("results/design", "--output-prefix", "-o", help="Output file prefix (produces <prefix>_guides.csv, <prefix>_report.xlsx, <prefix>_report.html)"),
    bgc: str | None = typer.Option(None, "--bgc", help="Path to BGC regions file (BED/TSV) for actinomycete context"),
    mode: str = typer.Option("knockout", "--mode", help="Design mode: knockout or crispri"),
    output: str | None = typer.Option(None, "--output", help="Legacy: path to single CSV output (for compatibility)"),
) -> None:
    """Design CRISPR guide RNAs for a target gene using the full pipeline.

    Uses the unified design pipeline (off-target search + scoring + profiles + reports).
    """
    console.print("[bold blue]ActinoEdit[/bold blue] - CRISPR Guide RNA Design")
    console.print()

    # Resolve annotation path (already validated by CLI options but double-check)
    if not gff and not gbk:
        _exit_with_error("Either --gff or --gbk must be provided")
    annotation_path: str = gff or gbk  # type: ignore[assignment]

    # Support legacy --output as csv -> derive prefix
    effective_prefix = output_prefix
    if output:
        out_p = Path(output)
        # If user passed a .csv, strip extension for prefix
        if out_p.suffix.lower() == ".csv":
            effective_prefix = str(out_p.with_suffix(""))
        else:
            effective_prefix = output

    # Build pipeline input
    inp = DesignInput(
        genome_path=genome,
        annotation_path=annotation_path,
        target=target,
        pam=pam,
        spacer_length=spacer_length,
        max_mismatches=max_mismatches,
        organism_profile=profile,
        output_prefix=effective_prefix,
        bgc_path=bgc,
        design_mode=mode,
    )

    # Run pipeline (this does genome load, annotation, target resolve, scan, offtarget, score)
    console.print("Running design pipeline...")
    try:
        result = run_design_pipeline(inp, progress_callback=lambda msg: console.print(f"  {msg}"))
    except FileNotFoundError as e:
        _exit_with_error(str(e))
    except ValueError as e:
        _exit_with_error(str(e))
    except Exception as e:
        _exit_with_error(f"Pipeline error: {e}")

    if result.target_region is None or not result.guide_candidates:
        if result.warnings:
            for w in result.warnings:
                console.print(f"[yellow]Warning:[/yellow] {w}")
        console.print("[yellow]No guide candidates produced.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[green]Found {len(result.guide_candidates)} guide candidates[/green]")

    # Generate reports (CSV + Excel + HTML)
    params: dict[str, str] = {
        "genome": genome,
        "annotation": annotation_path,
        "target": target,
        "profile": profile or "default",
        "pam": result.guide_candidates[0].pam if result.guide_candidates else pam,
        "spacer_length": str(spacer_length),
        "max_mismatches": str(max_mismatches),
        "bgc": bgc or "",
    }
    try:
        created = write_design_reports(
            result.guide_candidates,
            result.guide_scores,
            result.off_target_hits,
            result.target_region,
            result.warnings,
            effective_prefix,
            params,
        )
        console.print("\n[bold]Reports generated:[/bold]")
        for p in created:
            console.print(f"  [green]{p}[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Report generation issue: {e}")
        # Fallback: at least try basic csv using old helper? but skip for now

    # Show rich summary of top scored
    _display_scored_summary_table(result.guide_candidates, result.guide_scores, result.off_target_hits)

    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for w in result.warnings[:5]:
            console.print(f"  - {w}")


def _display_scored_summary_table(
    guides: list,
    scores: list | None = None,
    off_target_hits: dict | None = None,
) -> None:
    """Display a summary table including score and off-target counts."""
    score_map = {s.guide_id: s for s in (scores or [])}
    ot_map = off_target_hits or {}

    table = Table(title="Guide RNA Candidates (with scores)")
    table.add_column("Guide ID", style="cyan")
    table.add_column("Position", style="green")
    table.add_column("Strand", style="magenta")
    table.add_column("GC%", style="red")
    table.add_column("OffT", style="yellow")
    table.add_column("Score", style="blue")
    table.add_column("Rec", style="white")

    for guide in guides[:15]:
        sc = score_map.get(guide.guide_id)
        hits = ot_map.get(guide.guide_id, [])
        ot_count = len([h for h in hits if h.mismatch_count > 0])  # count only real off
        score_str = f"{sc.final_score:.3f}" if sc else "N/A"
        rec = sc.recommendation if sc else "N/A"
        table.add_row(
            guide.guide_id,
            f"{guide.contig}:{guide.start}-{guide.end}",
            guide.strand,
            f"{guide.gc_content:.1%}",
            str(ot_count),
            score_str,
            rec,
        )

    if len(guides) > 15:
        table.add_row("...", "...", "...", "...", "...", "...", "...")

    console.print()
    console.print(table)


@app.command()
def target_info(
    genome: str = typer.Option(..., "--genome", "-g", help="Path to genome FASTA file"),
    gff: str | None = typer.Option(None, "--gff", help="Path to GFF3 annotation file"),
    gbk: str | None = typer.Option(None, "--gbk", help="Path to GenBank annotation file"),
    target: str = typer.Option(..., "--target", "-t", help="Target gene (locus_tag, gene name, or contig:start-end)"),
) -> None:
    """Show information about a target gene or region."""
    from actinoedit.core.target import get_target_info
    from actinoedit.io.gbk import parse_gbk as parse_gbk_file
    from actinoedit.io.gff import parse_gff

    console.print("[bold blue]ActinoEdit[/bold blue] - Target Info")
    console.print()

    # Validate inputs
    if not gff and not gbk:
        _exit_with_error("Either --gff or --gbk must be provided")

    # Load annotation
    features: list = []
    if gff:
        gff_path = Path(gff)
        if not gff_path.exists():
            _exit_with_error(f"GFF file not found: {gff}")
        try:
            features = parse_gff(gff_path)
        except Exception as e:
            _exit_with_error(f"Error loading GFF: {e}")
    elif gbk:
        gbk_path = Path(gbk)
        if not gbk_path.exists():
            _exit_with_error(f"GenBank file not found: {gbk}")
        try:
            features = parse_gbk_file(gbk_path)
        except Exception as e:
            _exit_with_error(f"Error loading GenBank: {e}")

    # Get target info
    try:
        info = get_target_info(features, target)
    except ValueError as e:
        _exit_with_error(str(e))

    # Display info
    table = Table(title="Target Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    for key, value in info.items():
        table.add_row(key, str(value))

    console.print(table)


@app.command()
def base_edit(
    genome: str = typer.Option(..., "--genome", "-g", help="Path to genome FASTA file"),
    gff: str | None = typer.Option(None, "--gff", help="Path to GFF3 annotation file"),
    gbk: str | None = typer.Option(None, "--gbk", help="Path to GenBank annotation file"),
    target: str = typer.Option(..., "--target", "-t", help="Target gene"),
    editor: str = typer.Option("CBE", "--editor", "-e", help="Base editor type (CBE or ABE)"),
) -> None:
    """Analyze base editing opportunities for a target gene (computational only)."""
    from actinoedit.core.base_editor import analyze_base_editing
    from actinoedit.core.models import GuideCandidate
    from actinoedit.core.target import resolve_target
    from actinoedit.io.fasta import parse_fasta
    from actinoedit.io.gbk import parse_gbk as parse_gbk_file
    from actinoedit.io.gff import parse_gff

    console.print("[bold blue]ActinoEdit[/bold blue] - Base Editing Analysis")
    console.print(f"Editor: {editor}")

    if not gff and not gbk:
        _exit_with_error("Either --gff or --gbk must be provided")

    # Load minimal data
    features = parse_gff(gff) if gff else parse_gbk_file(gbk or "")
    try:
        target_region = resolve_target(features, target)
    except Exception as e:
        _exit_with_error(str(e))

    contigs = parse_fasta(genome)
    contig = contigs.get(target_region.contig)
    if contig is None:
        _exit_with_error("Contig not found")
    assert contig is not None

    # Create a dummy guide in the middle for demo analysis (real usage would come from design)
    mid = (target_region.start + target_region.end) // 2
    dummy_guide = GuideCandidate(
        guide_id="baseedit_demo",
        contig=target_region.contig,
        spacer="ATCGATCGATCGATCGATCG",  # placeholder
        pam="NGG",
        start=mid,
        end=mid + 19,
        strand="+",
        pam_start=mid + 20,
        pam_end=mid + 22,
        cut_site=mid + 17,
        gc_content=0.5,
    )

    # Extract rough subsequence
    try:
        subseq = contig.get_subsequence(max(1, mid - 30), min(contig.length, mid + 50))
    except Exception:
        subseq = "N" * 80

    editor_type: Literal["CBE", "ABE"] = "CBE" if editor.upper() == "CBE" else "ABE"
    pred = analyze_base_editing(dummy_guide, subseq, editor=editor_type, cds_start=target_region.start, cds_end=target_region.end)

    console.print(f"\nGuide position: {dummy_guide.start}-{dummy_guide.end}")
    console.print(f"Editable bases in window: {pred.editable_bases}")
    if pred.codon_change:
        console.print(f"Codon change: {pred.codon_change}")
    if pred.aa_change:
        console.print(f"AA change: {pred.aa_change}")
    console.print(f"Consequence: {pred.consequence or 'N/A'}")
    if pred.has_early_stop:
        console.print("[yellow]Potential early stop codon introduced[/yellow]")


@app.command("list-profiles")
def list_profiles_cmd() -> None:
    """List available organism profiles."""
    from actinoedit.core.profiles import list_profiles, load_profile

    console.print("[bold blue]Available organism profiles:[/bold blue]\n")
    for name in list_profiles():
        try:
            p = load_profile(name)
            console.print(f"  [cyan]{name}[/cyan]: {p.display_name}")
            console.print(f"     PAM={p.default_pam}, spacer={p.spacer_length}, GC={p.recommended_gc_min}-{p.recommended_gc_max}%")
        except Exception:
            console.print(f"  [cyan]{name}[/cyan]")
    console.print("\nUse with: actinoedit design ... --profile <name>")


# ------------------------------------------------------------------
# DB subcommands (local SQLite project storage)
# ------------------------------------------------------------------
db_app = typer.Typer(help="Local database commands (optional SQLite project storage)")


@db_app.command("init")
def db_init(db_path: str | None = typer.Option(None, "--db", help="Custom database path")) -> None:
    """Initialize (or create) the local SQLite database."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    conn = get_connection(db_path) if db_path else get_connection()
    init_database(conn)
    db_file = conn.execute("PRAGMA database_list").fetchone()[2]
    console.print(f"[green]Database initialized at[/green] {db_file}")


@db_app.command("list")
def db_list() -> None:
    """List projects in the local database."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    projs = db_list_projects()
    if not projs:
        console.print("No projects yet. Use 'actinoedit db init' and 'save-guides'.")
        return
    table = Table(title="Projects")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Profile")
    table.add_column("Created")
    for p in projs:
        table.add_row(str(p.get("id")), p.get("name", ""), p.get("organism_profile") or "", str(p.get("created_at", ""))[:19])
    console.print(table)


@db_app.command("save-guides")
def db_save_guides(
    prefix: str = typer.Option(..., "--prefix", help="Output prefix of a previous design run (e.g. results/design)"),
    project: str = typer.Option("default", "--project", "-p", help="Project name to save under"),
) -> None:
    """Save guides from previous design run (CSV + scores) into the DB."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")

    # Load the result-like data from the csv (lightweight)
    csv_path = Path(str(prefix) + "_guides.csv") if not str(prefix).endswith("_guides.csv") else Path(str(prefix))
    if not csv_path.exists():
        _exit_with_error(f"Guides CSV not found: {csv_path}")

    import pandas as pd

    df = pd.read_csv(csv_path)

    # We reconstruct a minimal DesignResult for save
    from actinoedit.core.models import GuideCandidate, GuideScore
    from actinoedit.core.pipeline import DesignResult

    guides: list[GuideCandidate] = []
    scores: list[GuideScore] = []
    for _, row in df.iterrows():
        g = GuideCandidate(
            guide_id=str(row.get("guide_id", "")),
            contig=str(row.get("contig", "")),
            spacer=str(row.get("spacer", "")),
            pam=str(row.get("pam", "")),
            start=int(row.get("start", 0)),
            end=int(row.get("end", 0)),
            strand=str(row.get("strand", "+")),
            pam_start=int(row.get("pam_start", 0)),
            pam_end=int(row.get("pam_end", 0)),
            cut_site=int(row.get("cut_site", 0)),
            gc_content=float(row.get("gc_content", 0)),
            target_label=str(row.get("target_label", "")) or None,
            bgc_id=str(row.get("bgc_id", "")) or None,
            bgc_context=str(row.get("bgc_context", "")) or None,
        )
        guides.append(g)
        if "final_score" in row and pd.notna(row["final_score"]):
            scores.append(
                GuideScore(
                    guide_id=g.guide_id,
                    final_score=float(row.get("final_score", 0)),
                    recommendation=str(row.get("recommendation", "caution")),
                )
            )

    fake_result = DesignResult(guide_candidates=guides, guide_scores=scores)
    n = save_guides_from_result(fake_result, project)
    console.print(f"[green]Saved {n} guides[/green] to project '{project}'")


@db_app.command("import-genome")
def db_import_genome(
    name: str = typer.Option(..., "--name", "-n", help="Name for the genome/strain"),
    genome: str = typer.Option(..., "--genome", "-g", help="Path to genome FASTA"),
    gff: str | None = typer.Option(None, "--gff", help="Optional GFF3 annotation"),
    gbk: str | None = typer.Option(None, "--gbk", help="Optional GenBank annotation"),
) -> None:
    """Import a genome (and annotation) into the local DB for project management."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")

    ann = gff or gbk
    summary = import_genome(name, genome, ann)
    console.print("[green]Genome imported successfully[/green]")
    console.print(f"  ID: {summary['genome_id']}")
    console.print(f"  Contigs: {summary['contigs']}, Length: {summary['total_length']}, GC: {summary['gc']:.2%}")
    if summary.get("features_imported"):
        console.print(f"  Features: {summary['features_imported']}")


@db_app.command("export")
def db_export(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    output: str = typer.Option(..., "--output", "-o", help="Output file path (csv or xlsx)"),
) -> None:
    """Export guides from a project in the DB to a report file."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    fmt = "xlsx" if output.lower().endswith(".xlsx") else "csv"
    path = export_project_guides(project, output, format=fmt)
    console.print(f"[green]Exported to[/green] {path}")


@db_app.command("list-genomes")
def db_list_genomes() -> None:
    """List imported genomes."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import list_genomes
    genomes = list_genomes()
    if not genomes:
        console.print("No genomes imported yet.")
        return
    table = Table(title="Imported Genomes")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Contigs")
    table.add_column("Length")
    table.add_column("GC")
    for g in genomes:
        table.add_row(str(g.get("id")), g.get("name",""), str(g.get("contigs","")), str(g.get("total_length","")), f"{g.get('gc',0):.2%}")
    console.print(table)


@db_app.command("list-genes")
def db_list_genes(genome: str = typer.Option(..., "--genome", "-g", help="Genome name")) -> None:
    """List genes for an imported genome."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import get_genes_for_genome
    genes = get_genes_for_genome(genome_name=genome, limit=50)
    if not genes:
        console.print(f"No genes for genome '{genome}'.")
        return
    table = Table(title=f"Genes for {genome} (first {len(genes)})")
    table.add_column("locus_tag")
    table.add_column("gene")
    table.add_column("contig")
    table.add_column("start-end")
    table.add_column("product")
    for g in genes:
        table.add_row(
            g.get("locus_tag") or "",
            g.get("gene_name") or "",
            g.get("contig",""),
            f"{g.get('start')}-{g.get('end')}",
            (g.get("product") or "")[:40],
        )
    console.print(table)


# Attach db sub-app
app.add_typer(db_app, name="db")


if __name__ == "__main__":
    app()
