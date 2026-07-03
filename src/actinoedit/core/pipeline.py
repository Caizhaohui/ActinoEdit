"""Unified design pipeline for ActinoEdit.

This module orchestrates CRISPR guide RNA design.
Both CLI and Web UI should call this pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from actinoedit import __version__
from actinoedit.core.bgc import annotate_bgc_context
from actinoedit.core.crispri import annotate_crispri_guides
from actinoedit.core.design_types import DesignInput, DesignResult
from actinoedit.core.input_summary import summarize_design_inputs
from actinoedit.core.models import GeneFeature
from actinoedit.core.offtarget import search_offtargets
from actinoedit.core.offtarget_index import get_or_build_index
from actinoedit.core.profiles import get_profile_or_default
from actinoedit.core.resolve import resolve_design_params
from actinoedit.core.scanner import ScannerConfig, scan_guides
from actinoedit.core.scoring import ScoringWeights, score_guide
from actinoedit.core.target import resolve_target
from actinoedit.io.fasta import parse_fasta
from actinoedit.io.gbk import parse_gbk
from actinoedit.io.gff import parse_gff

# Re-export types for backward compatibility
__all__ = [
    "DesignInput",
    "DesignResult",
    "run_design_pipeline",
]


def run_design_pipeline(
    input_params: DesignInput,
    progress_callback: Callable[[str], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> DesignResult:
    """Run the guide RNA design pipeline."""
    result = DesignResult(version=__version__)
    warnings: list[str] = []

    _validate_inputs(input_params)

    resolved = resolve_design_params(input_params)
    profile = get_profile_or_default(input_params.organism_profile)
    result.resolved_params = resolved.as_dict()
    result.profile_name = resolved.profile_name
    result.input_file_summary = summarize_design_inputs(
        resolved.genome_path,
        resolved.annotation_path,
        bgc_path=resolved.bgc_path,
    )

    _report_progress(progress_callback, "Loading genome...")
    contigs = parse_fasta(resolved.genome_path)
    _report_progress(progress_callback, f"  Loaded {len(contigs)} contigs")

    _report_progress(progress_callback, "Loading annotation...")
    features = _load_annotation(resolved.annotation_path)
    _report_progress(progress_callback, f"  Loaded {len(features)} features")

    _report_progress(progress_callback, f"Resolving target: {resolved.target}")
    try:
        target_region = resolve_target(features, resolved.target)
        result.target_region = target_region
        _report_progress(progress_callback, f"  Target: {target_region.display_label}")
    except ValueError as e:
        result.warnings.append(f"Target resolution failed: {e}")
        return result

    config = ScannerConfig(
        pam_pattern=resolved.pam,
        spacer_length=resolved.spacer_length,
    )

    _report_progress(progress_callback, "Scanning for guide candidates...")
    contig = contigs.get(target_region.contig)
    if contig is None:
        result.warnings.append(f"Contig '{target_region.contig}' not found in genome")
        return result

    guides = scan_guides(contig, target_region, config)
    result.guide_candidates = guides
    _report_progress(progress_callback, f"  Found {len(guides)} candidates")

    if not guides:
        result.warnings.append("No guide candidates found")
        return result

    _report_progress(progress_callback, "Building genome off-target index...")
    genome_index = get_or_build_index(contigs)
    _report_progress(progress_callback, "Searching for off-target sites...")
    for i, guide in enumerate(guides):
        if should_cancel and should_cancel():
            result.cancelled = True
            result.warnings.append("Design cancelled during off-target search")
            result.warnings.extend(warnings)
            return result

        hits = search_offtargets(
            guide,
            contigs,
            max_mismatches=resolved.max_mismatches,
            ignore_on_target=True,
            genome_index=genome_index,
        )
        result.off_target_hits[guide.guide_id] = hits

        if (i + 1) % 10 == 0:
            _report_progress(progress_callback, f"  Processed {i + 1}/{len(guides)} guides")

    _report_progress(progress_callback, "  Off-target search complete")

    _report_progress(progress_callback, "Scoring guides...")
    weights = ScoringWeights()
    weights.normalize()

    for guide in guides:
        hits = result.off_target_hits.get(guide.guide_id, [])
        score = score_guide(
            guide,
            hits,
            profile,
            weights,
            design_mode=resolved.design_mode,
        )
        result.guide_scores.append(score)

    _report_progress(progress_callback, "  Scoring complete")

    for guide in guides:
        if profile.is_high_gc(guide.gc_content):
            warnings.append(f"Guide {guide.guide_id}: High GC content ({guide.gc_content:.1%})")

    if resolved.bgc_path or profile.enable_bgc_annotation:
        _report_progress(progress_callback, "Annotating BGC context...")
        annotated, bgc_regions, bgc_warnings = annotate_bgc_context(
            result.guide_candidates,
            resolved.bgc_path,
            profile_enable_bgc=profile.enable_bgc_annotation,
        )
        result.guide_candidates = annotated
        result.bgc_regions = bgc_regions
        warnings.extend(bgc_warnings)
        if bgc_regions:
            _report_progress(
                progress_callback,
                f"  Annotated with {len(bgc_regions)} BGC regions",
            )

    if resolved.design_mode == "crispri" and result.target_region:
        _report_progress(progress_callback, "Annotating CRISPRi context...")
        annotate_crispri_guides(result.guide_candidates, result.target_region)
        _report_progress(progress_callback, "  CRISPRi annotation complete")

    result.warnings = warnings
    return result


def _validate_inputs(input_params: DesignInput) -> None:
    """Validate design input parameters."""
    genome_path = Path(input_params.genome_path)
    if not genome_path.exists():
        raise FileNotFoundError(f"Genome file not found: {input_params.genome_path}")

    annotation_path = Path(input_params.annotation_path)
    if not annotation_path.exists():
        raise FileNotFoundError(f"Annotation file not found: {input_params.annotation_path}")

    if not input_params.target:
        raise ValueError("Target must be specified")

    if input_params.spacer_length < 1:
        raise ValueError(f"Spacer length must be >= 1, got {input_params.spacer_length}")

    if input_params.max_mismatches < 0:
        raise ValueError(f"Max mismatches must be >= 0, got {input_params.max_mismatches}")


def _load_annotation(annotation_path: str) -> list[GeneFeature]:
    """Load annotation from GFF or GBK file."""
    path = Path(annotation_path)
    suffix = path.suffix.lower()

    if suffix in (".gff", ".gff3"):
        return parse_gff(path)
    if suffix in (".gbk", ".gb", ".genbank"):
        return parse_gbk(path)
    raise ValueError(f"Unsupported annotation format: {suffix}")


def _report_progress(
    callback: Callable[[str], None] | None,
    message: str,
) -> None:
    """Report progress to callback."""
    if callback is not None:
        callback(message)
