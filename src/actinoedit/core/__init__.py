"""Core CRISPR design algorithms."""

from actinoedit.core.models import (
    Contig,
    GeneFeature,
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    OrganismProfile,
    TargetRegion,
)
from actinoedit.core.offtarget import (
    count_offtargets_by_mismatch,
    filter_offtargets,
    get_offtarget_summary,
    search_offtargets,
)
from actinoedit.core.pam import (
    compile_pam,
    find_pam_matches,
    get_default_pam,
    get_nuclease_info,
    get_pam_regex,
    is_pam_match,
    list_nucleases,
)
from actinoedit.core.profiles import (
    get_profile_or_default,
    list_profiles,
    load_all_profiles,
    load_profile,
)
from actinoedit.core.scanner import (
    ScannerConfig,
    filter_guides_by_gc,
    scan_entire_contig,
    scan_guides,
    sort_guides_by_gc,
)
from actinoedit.core.scoring import (
    ScoringWeights,
    rank_guides,
    score_guide,
    score_guides,
)
from actinoedit.core.sequence import (
    AMBIGUOUS_BASES,
    COMPLEMENT_TABLE,
    VALID_DNA_CHARS,
    calculate_gc_content,
    complement,
    count_homopolymer_runs,
    generate_stable_id,
    has_homopolymer_run,
    normalize_sequence,
    reverse_complement,
    validate_dna_sequence,
)
from actinoedit.core.target import (
    get_target_info,
    list_targets,
    resolve_target,
)

__all__ = [
    # Models
    "Contig",
    "GeneFeature",
    "GuideCandidate",
    "GuideScore",
    "OffTargetHit",
    "OrganismProfile",
    "TargetRegion",
    # Off-target search
    "count_offtargets_by_mismatch",
    "filter_offtargets",
    "get_offtarget_summary",
    "search_offtargets",
    # PAM matching
    "compile_pam",
    "find_pam_matches",
    "get_default_pam",
    "get_nuclease_info",
    "get_pam_regex",
    "is_pam_match",
    "list_nucleases",
    # Profiles
    "get_profile_or_default",
    "list_profiles",
    "load_all_profiles",
    "load_profile",
    # Scanner
    "ScannerConfig",
    "filter_guides_by_gc",
    "scan_entire_contig",
    "scan_guides",
    "sort_guides_by_gc",
    # Scoring
    "ScoringWeights",
    "rank_guides",
    "score_guide",
    "score_guides",
    # Sequence utilities
    "AMBIGUOUS_BASES",
    "COMPLEMENT_TABLE",
    "VALID_DNA_CHARS",
    "calculate_gc_content",
    "complement",
    "count_homopolymer_runs",
    "generate_stable_id",
    "has_homopolymer_run",
    "normalize_sequence",
    "reverse_complement",
    "validate_dna_sequence",
    # Target selection
    "get_target_info",
    "list_targets",
    "resolve_target",
]
