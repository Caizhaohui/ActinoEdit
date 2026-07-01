"""Unified design pipeline for ActinoEdit.

This module provides a reusable pipeline for CRISPR guide RNA design.
Both CLI and Web UI should call this pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from actinoedit.annotation.bgc import annotate_guides_with_bgc, load_bgc_regions
from actinoedit.core.models import (
    BGCRegion,
    GeneFeature,
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    TargetRegion,
)
from actinoedit.core.offtarget import search_offtargets
from actinoedit.core.profiles import get_profile_or_default
from actinoedit.core.scanner import ScannerConfig, scan_guides
from actinoedit.core.scoring import ScoringWeights, score_guide
from actinoedit.core.target import resolve_target
from actinoedit.io.fasta import parse_fasta
from actinoedit.io.gbk import parse_gbk
from actinoedit.io.gff import parse_gff


@dataclass
class DesignInput:
    """Input parameters for guide RNA design.

    Attributes:
        genome_path: Path to genome FASTA file.
        annotation_path: Path to annotation file (GFF or GBK).
        target: Target gene (locus_tag, gene name, or coordinates).
        pam: PAM pattern.
        spacer_length: Spacer length.
        max_mismatches: Maximum mismatches for off-target search.
        organism_profile: Organism profile name.
        output_prefix: Output file prefix.
        bgc_path: Optional path to BGC regions file for context annotation.
    """

    genome_path: str
    annotation_path: str
    target: str
    pam: str = "NGG"
    spacer_length: int = 20
    max_mismatches: int = 3
    organism_profile: str | None = None
    output_prefix: str = "results/guides"
    bgc_path: str | None = None  # Optional BGC regions file (BED/TSV) for actinomycete context
    design_mode: str = "knockout"  # "knockout" or "crispri"


@dataclass
class DesignResult:
    """Result of guide RNA design.

    Attributes:
        target_region: Target region.
        guide_candidates: List of guide candidates.
        off_target_hits: Dictionary mapping guide_id to off-target hits.
        guide_scores: List of guide scores.
        warnings: List of warning messages.
        output_files: List of output file paths.
        bgc_regions: Loaded BGC regions (if used).
    """

    target_region: TargetRegion | None = None
    guide_candidates: list[GuideCandidate] = field(default_factory=list)
    off_target_hits: dict[str, list[OffTargetHit]] = field(default_factory=dict)
    guide_scores: list[GuideScore] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    bgc_regions: list[BGCRegion] = field(default_factory=list)


def run_design_pipeline(
    input_params: DesignInput,
    progress_callback: Callable[[str], None] | None = None,
) -> DesignResult:
    """Run the guide RNA design pipeline.

    This is the main entry point for guide RNA design.
    Both CLI and Web UI should call this function.

    Args:
        input_params: DesignInput parameters.
        progress_callback: Optional callback for progress updates.

    Returns:
        DesignResult object.

    Raises:
        FileNotFoundError: If input files not found.
        ValueError: If parameters are invalid.
    """
    result = DesignResult()
    warnings: list[str] = []

    # Validate inputs
    _validate_inputs(input_params)

    # Load organism profile
    profile = get_profile_or_default(input_params.organism_profile)

    # Apply profile defaults if not overridden
    if input_params.pam == "NGG" and profile.default_pam != "NGG":
        input_params.pam = profile.default_pam
    if input_params.spacer_length == 20 and profile.spacer_length != 20:
        input_params.spacer_length = profile.spacer_length
    if input_params.max_mismatches == 3 and profile.max_mismatches != 3:
        input_params.max_mismatches = profile.max_mismatches

    # Step 1: Load genome
    _report_progress(progress_callback, "Loading genome...")
    contigs = parse_fasta(input_params.genome_path)
    _report_progress(progress_callback, f"  Loaded {len(contigs)} contigs")

    # Step 2: Load annotation
    _report_progress(progress_callback, "Loading annotation...")
    features = _load_annotation(input_params.annotation_path)
    _report_progress(progress_callback, f"  Loaded {len(features)} features")

    # Step 3: Resolve target
    _report_progress(progress_callback, f"Resolving target: {input_params.target}")
    try:
        target_region = resolve_target(features, input_params.target)
        result.target_region = target_region
        _report_progress(progress_callback, f"  Target: {target_region.display_label}")
    except ValueError as e:
        result.warnings.append(f"Target resolution failed: {e}")
        return result

    # Step 4: Configure scanner
    config = ScannerConfig(
        pam_pattern=input_params.pam,
        spacer_length=input_params.spacer_length,
    )

    # Step 5: Scan for guides
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

    # Step 6: Search off-targets
    _report_progress(progress_callback, "Searching for off-target sites...")
    for i, guide in enumerate(guides):
        hits = search_offtargets(
            guide, contigs,
            max_mismatches=input_params.max_mismatches,
            ignore_on_target=True,
        )
        result.off_target_hits[guide.guide_id] = hits

        if (i + 1) % 10 == 0:
            _report_progress(progress_callback, f"  Processed {i + 1}/{len(guides)} guides")

    _report_progress(progress_callback, "  Off-target search complete")

    # Step 7: Score guides
    _report_progress(progress_callback, "Scoring guides...")
    weights = ScoringWeights()
    weights.normalize()

    for guide in guides:
        hits = result.off_target_hits.get(guide.guide_id, [])
        score = score_guide(guide, hits, profile, weights, design_mode=input_params.design_mode)
        result.guide_scores.append(score)

    _report_progress(progress_callback, "  Scoring complete")

    # Check for high GC warnings
    for guide in guides:
        if profile.is_high_gc(guide.gc_content):
            warnings.append(f"Guide {guide.guide_id}: High GC content ({guide.gc_content:.1%})")

    # Step 8 (optional): BGC annotation for actinomycetes
    bgc_regions: list[BGCRegion] = []
    if input_params.bgc_path or profile.enable_bgc_annotation:
        _report_progress(progress_callback, "Annotating BGC context...")
        try:
            if input_params.bgc_path:
                bgc_regions = load_bgc_regions(input_params.bgc_path)
            # If no explicit file but profile wants it, we currently require explicit path.
            # (Future: could look for common files next to genome.)
            if bgc_regions:
                result.guide_candidates = annotate_guides_with_bgc(
                    result.guide_candidates, bgc_regions
                )
                result.bgc_regions = bgc_regions
                _report_progress(
                    progress_callback,
                    f"  Annotated with {len(bgc_regions)} BGC regions",
                )
            else:
                warnings.append("BGC annotation requested but no regions loaded")
        except Exception as e:
            warnings.append(f"BGC annotation skipped: {e}")

    result.warnings = warnings

    return result


def _validate_inputs(input_params: DesignInput) -> None:
    """Validate design input parameters.

    Args:
        input_params: DesignInput parameters.

    Raises:
        FileNotFoundError: If files not found.
        ValueError: If parameters invalid.
    """
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
    """Load annotation from GFF or GBK file.

    Args:
        annotation_path: Path to annotation file.

    Returns:
        List of GeneFeature objects.
    """
    path = Path(annotation_path)
    suffix = path.suffix.lower()

    if suffix in (".gff", ".gff3"):
        return parse_gff(path)
    elif suffix in (".gbk", ".gb", ".genbank"):
        return parse_gbk(path)
    else:
        raise ValueError(f"Unsupported annotation format: {suffix}")


def _report_progress(
    callback: Callable[[str], None] | None,
    message: str,
) -> None:
    """Report progress to callback.

    Args:
        callback: Progress callback function.
        message: Progress message.
    """
    if callback is not None:
        callback(message)
