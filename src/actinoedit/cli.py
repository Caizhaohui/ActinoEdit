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
        save_guides_from_result,
    )
    from actinoedit.db import (
        list_projects as db_list_projects,
    )
    from actinoedit.db.config import get_db_url
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
    table.add_column("CRISPRi", style="cyan")
    table.add_column("Dist", style="magenta")
    table.add_column("StrandRel", style="yellow")
    table.add_column("Score", style="blue")
    table.add_column("Rec", style="white")

    for guide in guides[:15]:
        sc = score_map.get(guide.guide_id)
        hits = ot_map.get(guide.guide_id, [])
        ot_count = len([h for h in hits if h.mismatch_count > 0])  # count only real off
        score_str = f"{sc.final_score:.3f}" if sc else "N/A"
        rec = sc.recommendation if sc else "N/A"
        crispri = guide.crispri_region_type or ""
        dist = str(guide.distance_to_start_codon) if guide.distance_to_start_codon is not None else ""
        rel = guide.target_strand_relation or ""
        table.add_row(
            guide.guide_id,
            f"{guide.contig}:{guide.start}-{guide.end}",
            guide.strand,
            f"{guide.gc_content:.1%}",
            str(ot_count),
            crispri,
            dist,
            rel,
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
    """Screen base editing outcomes for designed guides (computational screening only)."""
    from actinoedit.core.base_editor import analyze_base_editing
    from actinoedit.io.fasta import parse_fasta

    console.print("[bold blue]ActinoEdit[/bold blue] - Base Editing Screening")
    console.print("[dim]Computational screening / rough annotation — not experimental validation.[/dim]")
    console.print(f"Editor: {editor}")

    if not gff and not gbk:
        _exit_with_error("Either --gff or --gbk must be provided")

    annotation_path: str = gff or gbk  # type: ignore[assignment]
    inp = DesignInput(
        genome_path=genome,
        annotation_path=annotation_path,
        target=target,
    )
    result = run_design_pipeline(inp)
    if not result.guide_candidates:
        _exit_with_error("No guide candidates found for base editing screening")
    if result.target_region is None:
        _exit_with_error("Could not resolve target region")
    target_region = result.target_region
    assert target_region is not None
    contigs = parse_fasta(genome)
    contig = contigs.get(target_region.contig)
    if contig is None:
        _exit_with_error("Contig not found")
    assert contig is not None

    score_map = {s.guide_id: s for s in result.guide_scores}
    guide = max(
        result.guide_candidates,
        key=lambda g: score_map[g.guide_id].final_score if g.guide_id in score_map else 0.0,
    )

    cut_site = guide.cut_site or guide.start
    try:
        subseq = contig.get_subsequence(max(1, cut_site - 30), min(contig.length, cut_site + 50))
    except Exception:
        subseq = "N" * 80

    editor_type: Literal["CBE", "ABE"] = "CBE" if editor.upper() == "CBE" else "ABE"
    pred = analyze_base_editing(
        guide,
        subseq,
        editor=editor_type,
        cds_start=target_region.start,
        cds_end=target_region.end,
    )

    top_score = score_map.get(guide.guide_id)
    console.print(f"\nTop guide: {guide.guide_id} (score={top_score.final_score if top_score else 'N/A'})")
    console.print(f"Guide position: {guide.start}-{guide.end}")
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
    """Initialize the local database via Alembic migrations."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    if db_path:
        db_url = f"sqlite:///{Path(db_path).expanduser().resolve()}"
    else:
        db_url = get_db_url()
    from actinoedit.db.migrations import upgrade_database

    revision = upgrade_database(db_url)
    from actinoedit.db.config import get_sqlite_path

    sqlite_path = get_sqlite_path(db_url)
    location = str(sqlite_path) if sqlite_path else db_url
    console.print(f"[green]Database initialized at[/green] {location}")
    console.print(f"[dim]Schema revision:[/dim] {revision}")


@db_app.command("migrate")
def db_migrate(
    db_path: str | None = typer.Option(None, "--db", help="Custom database path"),
    revision: str = typer.Option("head", "--revision", "-r", help="Target Alembic revision"),
) -> None:
    """Apply pending Alembic migrations."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    if db_path:
        db_url = f"sqlite:///{Path(db_path).expanduser().resolve()}"
    else:
        db_url = get_db_url()
    from actinoedit.db.migrations import upgrade_database

    current = upgrade_database(db_url, revision=revision)
    console.print(f"[green]Migrations applied[/green] (now at {current})")


@db_app.command("status")
def db_status(db_path: str | None = typer.Option(None, "--db", help="Custom database path")) -> None:
    """Show Alembic migration status for the configured database."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    if db_path:
        db_url = f"sqlite:///{Path(db_path).expanduser().resolve()}"
    else:
        db_url = get_db_url()
    from actinoedit.db.migrations import get_database_status

    status = get_database_status(db_url)
    table = Table(title="Database Migration Status")
    table.add_column("Property")
    table.add_column("Value")
    table.add_row("DB URL", status["db_url"])
    table.add_row("Current revision", status["current_revision"] or "(none)")
    table.add_row("Head revision", status["head_revision"] or "(none)")
    table.add_row("Pending migrations", "yes" if status["pending_migrations"] else "no")
    table.add_row("Up to date", "yes" if status["up_to_date"] else "no")
    console.print(table)


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
    table.add_column("Organism")
    table.add_column("Genome")
    table.add_column("Guides")
    table.add_column("Created")
    for p in projs:
        table.add_row(
            str(p.get("id")),
            p.get("name", ""),
            p.get("organism_profile") or "",
            p.get("organism_name") or "",
            p.get("genome_name") or "",
            str(p.get("guide_count", 0)),
            str(p.get("created_at", ""))[:19],
        )
    console.print(table)


@db_app.command("show-project")
def db_show_project(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
) -> None:
    """Show project details including linked organism and genome."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import get_project

    detail = get_project(project)
    if detail is None:
        _exit_with_error(f"Project not found: {project}")
        return
    console.print(f"[bold]{detail['name']}[/bold] (id={detail['id']})")
    console.print(f"  Description: {detail.get('description') or '—'}")
    console.print(f"  Profile: {detail.get('organism_profile') or '—'}")
    console.print(f"  Organism: {detail.get('organism_name') or '—'}")
    console.print(f"  Genome: {detail.get('genome_name') or '—'}")
    console.print(f"  Guides saved: {detail.get('guide_count', 0)}")
    console.print(f"  Created: {detail.get('created_at')}")


@db_app.command("create-project")
def db_create_project(
    name: str = typer.Option(..., "--name", "-n", help="Project name"),
    description: str = typer.Option("", "--description", "-d", help="Description"),
    profile: str | None = typer.Option(None, "--profile", "-r", help="Design profile"),
    organism: str | None = typer.Option(None, "--organism", help="Link to organism name"),
    genome: str | None = typer.Option(None, "--genome", "-g", help="Link to genome name"),
) -> None:
    """Create a project with optional organism and genome links."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import create_project

    try:
        pid = create_project(name, description, profile, organism_name=organism, genome_name=genome)
    except ValueError as exc:
        _exit_with_error(str(exc))
    console.print(f"[green]Project created[/green] (id={pid}): {name}")
    if organism:
        console.print(f"  Organism: {organism}")
    if genome:
        console.print(f"  Genome: {genome}")


@db_app.command("link-project")
def db_link_project(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    organism: str | None = typer.Option(None, "--organism", help="Organism name"),
    genome: str | None = typer.Option(None, "--genome", "-g", help="Genome name"),
) -> None:
    """Link a project to an organism and/or genome."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import update_project

    if not organism and not genome:
        _exit_with_error("Provide --organism and/or --genome")
    try:
        if not update_project(project, organism_name=organism, genome_name=genome):
            _exit_with_error(f"Project not found: {project}")
    except ValueError as exc:
        _exit_with_error(str(exc))
    console.print(f"[green]Updated links for project[/green] '{project}'")


@db_app.command("link-genome")
def db_link_genome(
    genome: str = typer.Option(..., "--genome", "-g", help="Genome name"),
    organism: str = typer.Option(..., "--organism", help="Organism name"),
) -> None:
    """Link an imported genome to an organism record."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import link_genome_to_organism

    try:
        if not link_genome_to_organism(genome, organism):
            _exit_with_error(f"Genome not found: {genome}")
    except ValueError as exc:
        _exit_with_error(str(exc))
    console.print(f"[green]Linked genome[/green] '{genome}' → organism '{organism}'")


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
    organism: str | None = typer.Option(None, "--organism", help="Associated organism name"),
) -> None:
    """Import a genome (and annotation) into the local DB for project management."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")

    ann = gff or gbk
    summary = import_genome(name, genome, ann, organism)
    console.print("[green]Genome imported successfully[/green]")
    console.print(f"  ID: {summary['genome_id']}")
    console.print(f"  Contigs: {summary['contigs']}, Length: {summary['total_length']}, GC: {summary['gc']:.2%}")
    if summary.get("features_imported"):
        console.print(f"  Features: {summary['features_imported']}")
    if organism:
        console.print(f"  Organism: {organism}")


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
    table.add_column("Organism")
    table.add_column("GC")
    for g in genomes:
        table.add_row(
            str(g.get("id")),
            g.get("name", ""),
            str(g.get("contigs", "")),
            str(g.get("total_length", "")),
            g.get("organism_name") or "",
            f"{g.get('gc', 0):.2%}",
        )
    console.print(table)


@db_app.command("list-organisms")
def db_list_organisms() -> None:
    """List organisms/strains."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import list_organisms
    orgs = list_organisms()
    if not orgs:
        console.print("No organisms recorded yet. Use db import-genome or save.")
        return
    table = Table(title="Organisms")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Species")
    table.add_column("Strain")
    for o in orgs:
        table.add_row(str(o.get("id")), o.get("name",""), o.get("species") or "", o.get("strain") or "")
    console.print(table)


@db_app.command("set-organism")
def db_set_organism(
    name: str = typer.Option(..., "--name", "-n", help="Organism name"),
    project: str = typer.Option(None, "--project", "-p", help="Associate to project (optional)"),
) -> None:
    """Record an organism/strain (optionally link to project)."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import save_organism
    oid = save_organism(name)
    console.print(f"[green]Organism '{name}' recorded (id={oid})[/green]")
    if project:
        console.print("  (Note: project association via save-guides or future enhancement)")


@db_app.command("save-validation")
def db_save_validation(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    guide_id: str = typer.Option(..., "--guide-id", help="Guide ID from design"),
    result: str = typer.Option(..., "--result", help="Validation result (e.g. success/fail)"),
    details: str = typer.Option("", "--details", help="Details"),
) -> None:
    """Save validation result linked to guide in project."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import save_validation_result
    vid = save_validation_result(project, guide_id, result, details)
    console.print(f"[green]Validation saved (id={vid}) for guide {guide_id} in {project}[/green]")


@db_app.command("list-validations")
def db_list_validations(
    project: str = typer.Option(None, "--project", "-p", help="Filter by project"),
    guide_id: str = typer.Option(None, "--guide-id", help="Filter by guide_id"),
) -> None:
    """List validation results."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import get_validation_results
    vals = get_validation_results(project, guide_id)
    if not vals:
        console.print("No validation results found.")
        return
    table = Table(title="Validation Results")
    table.add_column("ID")
    table.add_column("Project ID")
    table.add_column("Guide ID")
    table.add_column("Result")
    table.add_column("Details")
    for v in vals:
        table.add_row(str(v.get("id")), str(v.get("project_id")), v.get("guide_id",""), v.get("result",""), (v.get("details") or "")[:30])
    console.print(table)


@db_app.command("db-info")
def db_info() -> None:
    """Show current database config and mode."""
    if not DB_AVAILABLE:
        _exit_with_error("Database module not available")
    from actinoedit.db import get_db_url, is_postgres, load_config
    url = get_db_url()
    cfg = load_config()
    console.print(f"DB URL: {url}")
    console.print(f"Is Postgres: {is_postgres(url)}")
    console.print(f"Config loaded: {bool(cfg)}")
    if cfg:
        console.print(cfg)


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
