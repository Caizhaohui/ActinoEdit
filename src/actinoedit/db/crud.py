"""CRUD operations for the ActinoEdit database (SQLAlchemy backed).

Supports SQLite and PostgreSQL. Core logic independent of specific DB.
All functions accept optional ``session`` and ``db_url`` for test isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
from sqlalchemy.exc import IntegrityError

from actinoedit.core.models import GeneFeature
from actinoedit.core.pipeline import DesignResult
from actinoedit.db.models import (
    DesignRun,
    Gene,
    Genome,
    Guide,
    Organism,
    Project,
    ValidationResult,
)
from actinoedit.db.session import open_session
from actinoedit.db.timeutil import utc_now
from actinoedit.io.fasta import parse_fasta
from actinoedit.io.gbk import parse_gbk
from actinoedit.io.gff import parse_gff


def get_db_session(db_url: str | None = None) -> Any:
    """Get a new SQLAlchemy session and ensure schema."""
    session, _ = open_session(db_url=db_url)
    return session


def _resolve_organism_id(session: Any, name: str | None) -> int | None:
    if not name:
        return None
    org = session.query(Organism).filter_by(name=name).first()
    return cast(int, org.id) if org else None


def _resolve_genome_id(session: Any, name: str | None) -> int | None:
    if not name:
        return None
    genome = session.query(Genome).filter_by(name=name).first()
    return cast(int, genome.id) if genome else None


def _organism_name_by_id(session: Any, organism_id: int | None) -> str | None:
    if organism_id is None:
        return None
    org = session.query(Organism).filter_by(id=organism_id).first()
    return str(org.name) if org else None


def _genome_name_by_id(session: Any, genome_id: int | None) -> str | None:
    if genome_id is None:
        return None
    genome = session.query(Genome).filter_by(id=genome_id).first()
    return str(genome.name) if genome else None


def _project_to_dict(session: Any, project: Project, *, include_counts: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "organism_profile": project.organism_profile,
        "organism_id": project.organism_id,
        "genome_id": project.genome_id,
        "organism_name": _organism_name_by_id(session, cast(int | None, project.organism_id)),
        "genome_name": _genome_name_by_id(session, cast(int | None, project.genome_id)),
        "created_at": project.created_at,
    }
    if include_counts:
        data["guide_count"] = session.query(Guide).filter_by(project_id=project.id).count()
    return data


def _genome_to_dict(session: Any, genome: Genome) -> dict[str, Any]:
    return {
        "id": genome.id,
        "name": genome.name,
        "fasta_path": genome.fasta_path,
        "contigs": genome.contigs,
        "total_length": genome.total_length,
        "gc": genome.gc,
        "organism_id": genome.organism_id,
        "organism_name": _organism_name_by_id(session, cast(int | None, genome.organism_id)),
        "imported_at": genome.imported_at,
    }


def _organism_to_dict(organism: Organism) -> dict[str, Any]:
    return {
        "id": organism.id,
        "name": organism.name,
        "species": organism.species,
        "strain": organism.strain,
        "description": organism.description,
        "created_at": organism.created_at,
    }


def _ensure_project_id(
    session: Any,
    name: str,
    description: str = "",
    profile: str | None = None,
    organism_id: int | None = None,
    genome_id: int | None = None,
) -> int:
    """Get or create a project within an existing session."""
    existing = session.query(Project).filter_by(name=name).first()
    if existing:
        return cast(int, existing.id)
    proj = Project(
        name=name,
        description=description,
        organism_profile=profile,
        organism_id=organism_id,
        genome_id=genome_id,
    )
    session.add(proj)
    session.flush()
    return cast(int, proj.id)


def create_project(
    name: str,
    description: str = "",
    profile: str | None = None,
    organism_name: str | None = None,
    genome_name: str | None = None,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Create a new project and return its id."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        organism_id = _resolve_organism_id(sess, organism_name)
        genome_id = _resolve_genome_id(sess, genome_name)
        if organism_name and organism_id is None:
            raise ValueError(f"Organism not found: {organism_name}")
        if genome_name and genome_id is None:
            raise ValueError(f"Genome not found: {genome_name}")
        project_id = _ensure_project_id(
            sess,
            name,
            description,
            profile,
            organism_id=organism_id,
            genome_id=genome_id,
        )
        sess.commit()
        return project_id
    finally:
        if close:
            sess.close()


def get_project(
    name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> dict[str, Any] | None:
    """Return project details including linked organism and genome names."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        proj = sess.query(Project).filter_by(name=name).first()
        if not proj:
            return None
        return _project_to_dict(sess, proj, include_counts=True)
    finally:
        if close:
            sess.close()


def update_project(
    name: str,
    description: str | None = None,
    profile: str | None = None,
    organism_name: str | None = None,
    genome_name: str | None = None,
    *,
    clear_organism: bool = False,
    clear_genome: bool = False,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Update project metadata and optional organism/genome links."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        proj = sess.query(Project).filter_by(name=name).first()
        if not proj:
            return False
        if description is not None:
            proj.description = description
        if profile is not None:
            proj.organism_profile = profile
        if clear_organism:
            proj.organism_id = None
        elif organism_name is not None:
            organism_id = _resolve_organism_id(sess, organism_name)
            if organism_id is None:
                raise ValueError(f"Organism not found: {organism_name}")
            proj.organism_id = organism_id
        if clear_genome:
            proj.genome_id = None
        elif genome_name is not None:
            genome_id = _resolve_genome_id(sess, genome_name)
            if genome_id is None:
                raise ValueError(f"Genome not found: {genome_name}")
            proj.genome_id = genome_id
        sess.commit()
        return True
    finally:
        if close:
            sess.close()


def link_project_organism(
    project_name: str,
    organism_name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Associate a project with an organism record."""
    return update_project(
        project_name,
        organism_name=organism_name,
        session=session,
        db_url=db_url,
    )


def link_project_genome(
    project_name: str,
    genome_name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Associate a project with an imported genome."""
    return update_project(
        project_name,
        genome_name=genome_name,
        session=session,
        db_url=db_url,
    )


def save_genome(
    name: str,
    fasta_path: str | None = None,
    contigs: int = 0,
    total_length: int = 0,
    gc: float = 0.0,
    organism_name: str | None = None,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Import/register a genome."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        existing = sess.query(Genome).filter_by(name=name).first()
        if existing:
            return int(existing.id)

        organism_id = _resolve_organism_id(sess, organism_name)
        if organism_name and organism_id is None:
            raise ValueError(f"Organism not found: {organism_name}")
        genome = Genome(
            name=name,
            fasta_path=fasta_path,
            contigs=contigs,
            total_length=total_length,
            gc=gc,
            organism_id=organism_id,
        )
        sess.add(genome)
        try:
            sess.commit()
        except IntegrityError as exc:
            sess.rollback()
            again = sess.query(Genome).filter_by(name=name).first()
            if again:
                return int(again.id)
            raise ValueError(f"Genome name already exists: {name}") from exc
        sess.refresh(genome)
        return int(getattr(genome, "id", 0))
    finally:
        if close:
            sess.close()


def _design_run_to_dict(run: DesignRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "project_id": run.project_id,
        "genome_path": run.genome_path,
        "annotation_path": run.annotation_path,
        "genome_id": run.genome_id,
        "target": run.target,
        "organism_profile": run.organism_profile,
        "pam": run.pam,
        "design_mode": run.design_mode,
        "spacer_length": run.spacer_length,
        "max_mismatches": run.max_mismatches,
        "parameters_json": run.parameters_json,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "report_csv_path": run.report_csv_path,
        "report_xlsx_path": run.report_xlsx_path,
        "report_html_path": run.report_html_path,
        "guide_count": run.guide_count,
        "warnings_json": run.warnings_json,
    }


def create_design_run(
    project_name: str,
    *,
    genome_path: str | None = None,
    annotation_path: str | None = None,
    genome_name: str | None = None,
    target: str = "",
    organism_profile: str | None = None,
    pam: str | None = None,
    design_mode: str = "knockout",
    spacer_length: int | None = None,
    max_mismatches: int | None = None,
    parameters: dict[str, Any] | None = None,
    report_paths: dict[str, str] | None = None,
    warnings: list[str] | None = None,
    status: str = "completed",
    guide_count: int = 0,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Record a design run for audit, comparison, and reproducibility."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        project_id = _ensure_project_id(sess, project_name)
        genome_id = _resolve_genome_id(sess, genome_name)
        reports = report_paths or {}
        run = DesignRun(
            project_id=project_id,
            genome_path=genome_path,
            annotation_path=annotation_path,
            genome_id=genome_id,
            target=target,
            organism_profile=organism_profile,
            pam=pam,
            design_mode=design_mode,
            spacer_length=spacer_length,
            max_mismatches=max_mismatches,
            parameters_json=json.dumps(parameters or {}),
            status=status,
            started_at=utc_now(),
            completed_at=utc_now(),
            report_csv_path=reports.get("csv"),
            report_xlsx_path=reports.get("xlsx"),
            report_html_path=reports.get("html"),
            guide_count=guide_count,
            warnings_json=json.dumps(warnings or []),
        )
        sess.add(run)
        sess.commit()
        sess.refresh(run)
        return int(run.id)
    finally:
        if close:
            sess.close()


def list_design_runs(
    project_name: str | None = None,
    limit: int = 50,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """List design runs, optionally filtered by project."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        q = sess.query(DesignRun).order_by(DesignRun.started_at.desc())
        if project_name:
            proj = sess.query(Project).filter_by(name=project_name).first()
            if not proj:
                return []
            q = q.filter_by(project_id=proj.id)
        runs = q.limit(limit).all()
        return [_design_run_to_dict(r) for r in runs]
    finally:
        if close:
            sess.close()


def save_guides_from_result(
    result: DesignResult,
    project_name: str,
    replace_existing: bool = False,
    *,
    design_run_meta: dict[str, Any] | None = None,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Persist the guide results of a design run into the database.

    Returns number of guides saved.
    """
    if not result.guide_candidates:
        return 0

    sess, close = open_session(db_url=db_url, session=session)
    try:
        project_id = _ensure_project_id(sess, project_name)

        if replace_existing:
            sess.query(Guide).filter_by(project_id=project_id).delete()

        meta = design_run_meta or {}
        genome_id = _resolve_genome_id(sess, meta.get("genome_name"))
        reports = meta.get("report_paths") or {}
        run = DesignRun(
            project_id=project_id,
            genome_path=meta.get("genome_path"),
            annotation_path=meta.get("annotation_path"),
            genome_id=genome_id,
            target=str(meta.get("target", "")),
            organism_profile=meta.get("organism_profile"),
            pam=meta.get("pam"),
            design_mode=str(meta.get("design_mode", "knockout")),
            spacer_length=meta.get("spacer_length"),
            max_mismatches=meta.get("max_mismatches"),
            parameters_json=json.dumps(meta.get("parameters") or {}),
            status=str(meta.get("status", "completed")),
            started_at=utc_now(),
            completed_at=utc_now(),
            report_csv_path=reports.get("csv"),
            report_xlsx_path=reports.get("xlsx"),
            report_html_path=reports.get("html"),
            guide_count=len(result.guide_candidates),
            warnings_json=json.dumps(result.warnings),
        )
        sess.add(run)
        sess.flush()
        design_run_id = int(run.id)

        count = 0
        score_map = {s.guide_id: s for s in result.guide_scores}

        for guide in result.guide_candidates:
            sc = score_map.get(guide.guide_id)
            ot_hits = result.off_target_hits.get(guide.guide_id, [])
            ot_count = len(ot_hits)

            g = Guide(
                project_id=project_id,
                design_run_id=design_run_id,
                guide_id=guide.guide_id,
                contig=guide.contig,
                start=guide.start,
                end=guide.end,
                strand=guide.strand,
                spacer=guide.spacer,
                pam=guide.pam,
                gc_content=guide.gc_content,
                final_score=sc.final_score if sc else None,
                recommendation=sc.recommendation if sc else None,
                bgc_id=guide.bgc_id,
                bgc_context=guide.bgc_context,
                off_target_count=ot_count,
            )
            sess.add(g)
            count += 1

        sess.commit()
        return count
    finally:
        if close:
            sess.close()


def list_projects(
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    sess, close = open_session(db_url=db_url, session=session)
    try:
        projs = sess.query(Project).order_by(Project.created_at.desc()).all()
        return [_project_to_dict(sess, p, include_counts=True) for p in projs]
    finally:
        if close:
            sess.close()


def get_project_guides(
    project_name: str,
    limit: int = 100,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    sess, close = open_session(db_url=db_url, session=session)
    try:
        proj = sess.query(Project).filter_by(name=project_name).first()
        if not proj:
            return []
        guides = (
            sess.query(Guide)
            .filter_by(project_id=proj.id)
            .order_by(Guide.final_score.desc())
            .limit(limit)
            .all()
        )
        return [_guide_to_dict(g) for g in guides]
    finally:
        if close:
            sess.close()


def _guide_to_dict(g: Guide) -> dict[str, Any]:
    return {
        "id": g.id,
        "project_id": g.project_id,
        "design_run_id": g.design_run_id,
        "guide_id": g.guide_id,
        "contig": g.contig,
        "start": g.start,
        "end": g.end,
        "strand": g.strand,
        "spacer": g.spacer,
        "pam": g.pam,
        "gc_content": g.gc_content,
        "final_score": g.final_score,
        "recommendation": g.recommendation,
        "bgc_id": g.bgc_id,
        "bgc_context": g.bgc_context,
        "off_target_count": g.off_target_count,
        "created_at": g.created_at,
    }


def list_saved_guides(
    project_name: str | None = None,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """Convenience wrapper."""
    if project_name:
        return get_project_guides(project_name, session=session, db_url=db_url)
    sess, close = open_session(db_url=db_url, session=session)
    try:
        guides = sess.query(Guide).order_by(Guide.created_at.desc()).limit(200).all()
        return [_guide_to_dict(g) for g in guides]
    finally:
        if close:
            sess.close()


def save_validation_result(
    project_name: str,
    guide_id: str,
    result: str,
    details: str = "",
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Save a validation result associated with a project and guide."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        project_id = _ensure_project_id(sess, project_name)
        vr = ValidationResult(
            project_id=project_id,
            guide_id=guide_id,
            result=result,
            details=details,
        )
        sess.add(vr)
        sess.commit()
        sess.refresh(vr)
        return int(vr.id)
    finally:
        if close:
            sess.close()


def get_validation_results(
    project_name: str | None = None,
    guide_id: str | None = None,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve validation results, optionally filtered by project or guide."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        q = sess.query(ValidationResult)
        if project_name:
            proj = sess.query(Project).filter_by(name=project_name).first()
            if not proj:
                return []
            q = q.filter_by(project_id=proj.id)
        if guide_id:
            q = q.filter_by(guide_id=guide_id)
        vrs = q.order_by(ValidationResult.created_at.desc()).limit(100).all()
        return [
            {
                "id": v.id,
                "project_id": v.project_id,
                "guide_id": v.guide_id,
                "result": v.result,
                "details": v.details,
                "created_at": v.created_at,
            }
            for v in vrs
        ]
    finally:
        if close:
            sess.close()


def import_genome(
    name: str,
    genome_path: str,
    annotation_path: str | None = None,
    organism_name: str | None = None,
    *,
    db_url: str | None = None,
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
    gc = sum(c.gc_content * c.length for c in contigs.values()) / max(1, total_length)

    if organism_name:
        save_organism(organism_name, db_url=db_url)

    genome_id = save_genome(
        name=name,
        fasta_path=str(genome_p),
        contigs=len(contigs),
        total_length=total_length,
        gc=round(gc, 4),
        organism_name=organism_name,
        db_url=db_url,
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
            save_genes(genome_id, features, db_url=db_url)

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
    *,
    db_url: str | None = None,
) -> str:
    """Export saved guides for a project to CSV or Excel.

    Returns the path written.
    """
    guides = get_project_guides(project_name, limit=10000, db_url=db_url)
    if not guides:
        raise ValueError(f"No guides found for project '{project_name}'")

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(guides)

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


def save_genes(
    genome_id: int,
    features: list[GeneFeature],
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Save GeneFeature list into the genes table for a genome."""
    if not features:
        return 0
    sess, close = open_session(db_url=db_url, session=session)
    try:
        count = 0
        for f in features:
            gene = Gene(
                genome_id=genome_id,
                contig=f.contig,
                start=f.start,
                end=f.end,
                strand=f.strand,
                locus_tag=f.locus_tag,
                gene_name=f.gene_name,
                product=f.product,
                feature_type=f.feature_type,
            )
            sess.add(gene)
            count += 1
        sess.commit()
        return count
    finally:
        if close:
            sess.close()


def get_genes_for_genome(
    genome_name: str | None = None,
    genome_id: int | None = None,
    limit: int = 500,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve genes for a genome."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        if genome_id is None and genome_name:
            g = sess.query(Genome).filter_by(name=genome_name).first()
            if not g:
                return []
            genome_id = g.id
        if genome_id is None:
            return []
        genes = (
            sess.query(Gene)
            .filter_by(genome_id=genome_id)
            .order_by(Gene.contig, Gene.start)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": ge.id,
                "genome_id": ge.genome_id,
                "contig": ge.contig,
                "start": ge.start,
                "end": ge.end,
                "strand": ge.strand,
                "locus_tag": ge.locus_tag,
                "gene_name": ge.gene_name,
                "product": ge.product,
                "feature_type": ge.feature_type,
            }
            for ge in genes
        ]
    finally:
        if close:
            sess.close()


def list_genomes(
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """List all imported genomes."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        genomes = sess.query(Genome).order_by(Genome.imported_at.desc()).all()
        return [_genome_to_dict(sess, g) for g in genomes]
    finally:
        if close:
            sess.close()


def get_genome(
    name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> dict[str, Any] | None:
    """Return genome details including linked organism."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        genome = sess.query(Genome).filter_by(name=name).first()
        if not genome:
            return None
        return _genome_to_dict(sess, genome)
    finally:
        if close:
            sess.close()


def link_genome_to_organism(
    genome_name: str,
    organism_name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Associate an imported genome with an organism record."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        genome = sess.query(Genome).filter_by(name=genome_name).first()
        if not genome:
            return False
        organism_id = _resolve_organism_id(sess, organism_name)
        if organism_id is None:
            raise ValueError(f"Organism not found: {organism_name}")
        genome.organism_id = organism_id
        sess.commit()
        return True
    finally:
        if close:
            sess.close()


def list_genomes_for_organism(
    organism_name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """List genomes linked to a given organism."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        organism_id = _resolve_organism_id(sess, organism_name)
        if organism_id is None:
            return []
        genomes = sess.query(Genome).filter_by(organism_id=organism_id).order_by(Genome.imported_at.desc()).all()
        return [_genome_to_dict(sess, g) for g in genomes]
    finally:
        if close:
            sess.close()


def save_organism(
    name: str,
    species: str | None = None,
    strain: str | None = None,
    description: str | None = None,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> int:
    """Save or get an organism record."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        existing = sess.query(Organism).filter_by(name=name).first()
        if existing:
            return int(existing.id)
        org = Organism(name=name, species=species, strain=strain, description=description)
        sess.add(org)
        sess.commit()
        sess.refresh(org)
        return int(getattr(org, "id", 0))
    finally:
        if close:
            sess.close()


def update_organism(
    name: str,
    species: str | None = None,
    strain: str | None = None,
    description: str | None = None,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Update an organism by name."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        org = sess.query(Organism).filter_by(name=name).first()
        if not org:
            return False
        if species is not None:
            org.species = species
        if strain is not None:
            org.strain = strain
        if description is not None:
            org.description = description
        sess.commit()
        return True
    finally:
        if close:
            sess.close()


def list_organisms(
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """List all organisms."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        orgs = sess.query(Organism).order_by(Organism.created_at.desc()).all()
        return [_organism_to_dict(o) for o in orgs]
    finally:
        if close:
            sess.close()


def get_organism(
    name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> dict[str, Any] | None:
    """Return organism details."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        org = sess.query(Organism).filter_by(name=name).first()
        if not org:
            return None
        return _organism_to_dict(org)
    finally:
        if close:
            sess.close()


def list_projects_for_organism(
    organism_name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> list[dict[str, Any]]:
    """List projects linked to a given organism."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        organism_id = _resolve_organism_id(sess, organism_name)
        if organism_id is None:
            return []
        projs = sess.query(Project).filter_by(organism_id=organism_id).order_by(Project.created_at.desc()).all()
        return [_project_to_dict(sess, p, include_counts=True) for p in projs]
    finally:
        if close:
            sess.close()


def delete_project(
    project_name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Delete a project and its guides."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        proj = sess.query(Project).filter_by(name=project_name).first()
        if not proj:
            return False
        pid = proj.id
        sess.query(Guide).filter_by(project_id=pid).delete()
        sess.query(DesignRun).filter_by(project_id=pid).delete()
        sess.delete(proj)
        sess.commit()
        return True
    finally:
        if close:
            sess.close()


def delete_organism(
    name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Delete an organism by name."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        org = sess.query(Organism).filter_by(name=name).first()
        if not org:
            return False
        sess.delete(org)
        sess.commit()
        return True
    finally:
        if close:
            sess.close()


def delete_genome(
    name: str,
    *,
    session: Any | None = None,
    db_url: str | None = None,
) -> bool:
    """Delete a genome and its genes."""
    sess, close = open_session(db_url=db_url, session=session)
    try:
        g = sess.query(Genome).filter_by(name=name).first()
        if not g:
            return False
        gid = g.id
        sess.query(Gene).filter_by(genome_id=gid).delete()
        sess.delete(g)
        sess.commit()
        return True
    finally:
        if close:
            sess.close()
