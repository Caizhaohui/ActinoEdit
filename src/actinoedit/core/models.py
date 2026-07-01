"""Core data models for ActinoEdit."""

from __future__ import annotations

from dataclasses import dataclass, field

from actinoedit.core.sequence import (
    calculate_gc_content,
    validate_dna_sequence,
)


@dataclass
class Contig:
    """Represents a DNA contig/chromosome.

    Attributes:
        name: Contig name/identifier.
        sequence: DNA sequence (will be normalized to uppercase).
        length: Sequence length (calculated).
        gc_content: GC content as fraction (calculated).
    """

    name: str
    sequence: str
    length: int = field(init=False)
    gc_content: float = field(init=False)

    def __post_init__(self) -> None:
        """Calculate derived fields and validate."""
        # Normalize sequence to uppercase
        self.sequence = self.sequence.upper()
        self.length = len(self.sequence)
        if self.length > 0:
            self.gc_content = calculate_gc_content(self.sequence)
        else:
            self.gc_content = 0.0

    def validate(self) -> tuple[bool, str | None]:
        """Validate the contig.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.name:
            return False, "Contig name is empty"
        if not self.sequence:
            return False, "Sequence is empty"
        return validate_dna_sequence(self.sequence)

    def get_subsequence(self, start_1based: int, end_1based: int) -> str:
        """Extract a subsequence using 1-based inclusive coordinates.

        Args:
            start_1based: Start position (1-based inclusive).
            end_1based: End position (1-based inclusive).

        Returns:
            Subsequence string.

        Raises:
            IndexError: If coordinates are out of range.
        """
        if start_1based < 1 or end_1based > self.length:
            raise IndexError(
                f"Coordinates ({start_1based}, {end_1based}) out of range for "
                f"contig '{self.name}' with length {self.length}"
            )
        if start_1based > end_1based:
            raise ValueError(
                f"Start ({start_1based}) must be <= end ({end_1based})"
            )
        start_0based, end_halfopen = self.to_slice(start_1based, end_1based)
        return self.sequence[start_0based:end_halfopen]

    def to_slice(self, start_1based: int, end_1based: int) -> tuple[int, int]:
        """Convert 1-based inclusive coordinates to 0-based half-open slice.

        Args:
            start_1based: Start position (1-based inclusive).
            end_1based: End position (1-based inclusive).

        Returns:
            Tuple of (start_0based, end_halfopen).
        """
        return (start_1based - 1, end_1based)

    @staticmethod
    def from_slice(start_0based: int, end_halfopen: int) -> tuple[int, int]:
        """Convert 0-based half-open slice to 1-based inclusive coordinates.

        Args:
            start_0based: Start position (0-based).
            end_halfopen: End position (half-open, exclusive).

        Returns:
            Tuple of (start_1based, end_1based).
        """
        return (start_0based + 1, end_halfopen)


@dataclass
class GeneFeature:
    """Represents a gene or other genomic feature.

    Attributes:
        contig: Contig name.
        start: Start position (1-based inclusive).
        end: End position (1-based inclusive).
        strand: Strand ('+' or '-').
        locus_tag: Locus tag identifier.
        gene_name: Gene name.
        product: Gene product description.
        feature_type: Feature type (gene, CDS, rRNA, tRNA, etc.).
    """

    contig: str
    start: int  # 1-based inclusive
    end: int  # 1-based inclusive
    strand: str  # '+' or '-'
    locus_tag: str | None = None
    gene_name: str | None = None
    product: str | None = None
    feature_type: str = "gene"

    def __post_init__(self) -> None:
        """Validate coordinates."""
        if self.start < 1:
            raise ValueError(f"Start position must be >= 1, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"End ({self.end}) must be >= start ({self.start})")
        if self.strand not in ("+", "-", "."):
            raise ValueError(f"Strand must be '+', '-', or '.', got '{self.strand}'")

    def validate(self) -> tuple[bool, str | None]:
        """Validate the feature.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.contig:
            return False, "Contig name is empty"
        if self.start < 1:
            return False, f"Start position must be >= 1, got {self.start}"
        if self.end < self.start:
            return False, f"End ({self.end}) must be >= start ({self.start})"
        if self.strand not in ("+", "-", "."):
            return False, f"Strand must be '+', '-', or '.', got '{self.strand}'"
        return True, None

    def to_slice(self) -> tuple[int, int]:
        """Convert to 0-based half-open slice.

        Returns:
            Tuple of (start_0based, end_halfopen).
        """
        return (self.start - 1, self.end)

    @property
    def length(self) -> int:
        """Return feature length.

        Returns:
            Length in bases.
        """
        return self.end - self.start + 1

    @property
    def display_name(self) -> str:
        """Return a display name for the feature.

        Returns:
            Gene name, locus tag, or 'unknown'.
        """
        return self.gene_name or self.locus_tag or "unknown"

    def overlaps(self, other: GeneFeature) -> bool:
        """Check if this feature overlaps with another.

        Args:
            other: Another GeneFeature.

        Returns:
            True if features overlap.
        """
        if self.contig != other.contig:
            return False
        return self.start <= other.end and self.end >= other.start

    def contains(self, start: int, end: int) -> bool:
        """Check if this feature contains a coordinate range.

        Args:
            start: Start position (1-based inclusive).
            end: End position (1-based inclusive).

        Returns:
            True if the range is contained within this feature.
        """
        return self.start <= start and self.end >= end


@dataclass
class TargetRegion:
    """Represents a target region for guide RNA design.

    Attributes:
        contig: Contig name.
        start: Start position (1-based inclusive).
        end: End position (1-based inclusive).
        strand: Strand ('+', '-', or '.' for both).
        label: Optional label for the target.
    """

    contig: str
    start: int  # 1-based inclusive
    end: int  # 1-based inclusive
    strand: str  # '+', '-', or '.'
    label: str | None = None

    def __post_init__(self) -> None:
        """Validate coordinates."""
        if self.start < 1:
            raise ValueError(f"Start position must be >= 1, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"End ({self.end}) must be >= start ({self.start})")
        if self.strand not in ("+", "-", "."):
            raise ValueError(f"Strand must be '+', '-', or '.', got '{self.strand}'")

    def validate(self) -> tuple[bool, str | None]:
        """Validate the target region.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.contig:
            return False, "Contig name is empty"
        if self.start < 1:
            return False, f"Start position must be >= 1, got {self.start}"
        if self.end < self.start:
            return False, f"End ({self.end}) must be >= start ({self.start})"
        if self.strand not in ("+", "-", "."):
            return False, f"Strand must be '+', '-', or '.', got '{self.strand}'"
        return True, None

    def to_slice(self) -> tuple[int, int]:
        """Convert to 0-based half-open slice.

        Returns:
            Tuple of (start_0based, end_halfopen).
        """
        return (self.start - 1, self.end)

    @property
    def length(self) -> int:
        """Return region length.

        Returns:
            Length in bases.
        """
        return self.end - self.start + 1

    @property
    def display_label(self) -> str:
        """Return a display label for the target.

        Returns:
            Label or coordinate string.
        """
        return self.label or f"{self.contig}:{self.start}-{self.end}"

    def with_flank(self, upstream: int = 0, downstream: int = 0) -> TargetRegion:
        """Create a new TargetRegion with flanking regions.

        Args:
            upstream: Bases to extend upstream (5' direction).
            downstream: Bases to extend downstream (3' direction).

        Returns:
            New TargetRegion with flanks.
        """
        new_start = max(1, self.start - upstream)
        new_end = self.end + downstream
        return TargetRegion(
            contig=self.contig,
            start=new_start,
            end=new_end,
            strand=self.strand,
            label=self.label,
        )


@dataclass
class BGCRegion:
    """Represents a Biosynthetic Gene Cluster (BGC) region.

    Used for actinomycete-specific annotation of guides inside or near
    secondary metabolite clusters (e.g. from antiSMASH).

    Attributes:
        contig: Contig name.
        start: Start position (1-based inclusive).
        end: End position (1-based inclusive).
        bgc_id: Identifier for the cluster (e.g. 'BGC00001').
        bgc_type: Type of cluster (e.g. 'NRPS', 'PKS', 'terpene').
        product: Predicted product or description.
    """

    contig: str
    start: int  # 1-based inclusive
    end: int  # 1-based inclusive
    bgc_id: str
    bgc_type: str | None = None
    product: str | None = None

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError(f"Start position must be >= 1, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"End ({self.end}) must be >= start ({self.start})")

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def contains(self, pos: int) -> bool:
        """Check if a 1-based position is inside the BGC."""
        return self.start <= pos <= self.end

    def distance_to(self, pos: int) -> int:
        """Return distance from pos to closest edge of BGC (0 if inside)."""
        if self.contains(pos):
            return 0
        if pos < self.start:
            return self.start - pos
        return pos - self.end


@dataclass
class GuideCandidate:
    """Represents a candidate guide RNA.

    Attributes:
        guide_id: Unique identifier for the guide.
        contig: Contig name.
        spacer: Spacer sequence.
        pam: PAM sequence.
        start: Spacer start position (1-based inclusive).
        end: Spacer end position (1-based inclusive).
        strand: Strand ('+' or '-').
        pam_start: PAM start position (1-based inclusive).
        pam_end: PAM end position (1-based inclusive).
        cut_site: Expected cut site position (1-based).
        gc_content: GC content of spacer.
        target_label: Optional label for the target region.
        bgc_id: BGC the guide is in (if annotated).
        bgc_type: Type of the BGC.
        bgc_context: Human readable context e.g. 'inside:NRPS' or 'nearest:PKS (+3.2kb)'.
    """

    guide_id: str
    contig: str
    spacer: str
    pam: str
    start: int  # 1-based inclusive
    end: int  # 1-based inclusive
    strand: str  # '+' or '-'
    pam_start: int  # 1-based inclusive
    pam_end: int  # 1-based inclusive
    cut_site: int  # 1-based
    gc_content: float
    target_label: str | None = None
    bgc_id: str | None = None
    bgc_type: str | None = None
    bgc_context: str | None = None

    def __post_init__(self) -> None:
        """Validate and calculate derived fields."""
        if not self.guide_id:
            raise ValueError("Guide ID cannot be empty")
        if self.start < 1:
            raise ValueError(f"Start position must be >= 1, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"End ({self.end}) must be >= start ({self.start})")
        if self.strand not in ("+", "-"):
            raise ValueError(f"Strand must be '+' or '-', got '{self.strand}'")
        # Calculate GC content if not provided
        if self.gc_content == 0.0 and self.spacer:
            self.gc_content = calculate_gc_content(self.spacer)

    def validate(self) -> tuple[bool, str | None]:
        """Validate the guide candidate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.guide_id:
            return False, "Guide ID cannot be empty"
        if not self.contig:
            return False, "Contig name is empty"
        if not self.spacer:
            return False, "Spacer sequence is empty"
        if self.start < 1:
            return False, f"Start position must be >= 1, got {self.start}"
        if self.end < self.start:
            return False, f"End ({self.end}) must be >= start ({self.start})"
        if self.strand not in ("+", "-"):
            return False, f"Strand must be '+' or '-', got '{self.strand}'"
        return True, None

    def to_slice(self) -> tuple[int, int]:
        """Convert spacer coordinates to 0-based half-open slice.

        Returns:
            Tuple of (start_0based, end_halfopen).
        """
        return (self.start - 1, self.end)

    @property
    def spacer_length(self) -> int:
        """Return spacer length.

        Returns:
            Length in bases.
        """
        return len(self.spacer)

    @property
    def display_id(self) -> str:
        """Return a display ID for the guide.

        Returns:
            Guide ID with coordinates.
        """
        return f"{self.guide_id} ({self.contig}:{self.start}-{self.end})"


@dataclass
class OffTargetHit:
    """Represents an off-target hit for a guide RNA.

    Attributes:
        guide_id: Guide RNA identifier.
        contig: Contig name.
        start: Hit start position (1-based inclusive).
        end: Hit end position (1-based inclusive).
        strand: Strand ('+' or '-').
        sequence: Hit sequence.
        mismatch_count: Number of mismatches.
        mismatch_positions: List of mismatch positions (0-based from spacer start).
        nearby_gene: Optional nearby gene name.
    """

    guide_id: str
    contig: str
    start: int  # 1-based inclusive
    end: int  # 1-based inclusive
    strand: str
    sequence: str
    mismatch_count: int
    mismatch_positions: list[int] = field(default_factory=list)
    nearby_gene: str | None = None

    def __post_init__(self) -> None:
        """Validate the off-target hit."""
        if self.start < 1:
            raise ValueError(f"Start position must be >= 1, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"End ({self.end}) must be >= start ({self.start})")
        if self.strand not in ("+", "-"):
            raise ValueError(f"Strand must be '+' or '-', got '{self.strand}'")
        if self.mismatch_count < 0:
            raise ValueError(f"Mismatch count must be >= 0, got {self.mismatch_count}")

    def validate(self) -> tuple[bool, str | None]:
        """Validate the off-target hit.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.guide_id:
            return False, "Guide ID cannot be empty"
        if not self.contig:
            return False, "Contig name is empty"
        if self.start < 1:
            return False, f"Start position must be >= 1, got {self.start}"
        if self.end < self.start:
            return False, f"End ({self.end}) must be >= start ({self.start})"
        if self.strand not in ("+", "-"):
            return False, f"Strand must be '+' or '-', got '{self.strand}'"
        if self.mismatch_count < 0:
            return False, f"Mismatch count must be >= 0, got {self.mismatch_count}"
        if self.mismatch_count != len(self.mismatch_positions):
            return False, (
                f"Mismatch count ({self.mismatch_count}) does not match "
                f"positions list length ({len(self.mismatch_positions)})"
            )
        return True, None

    def to_slice(self) -> tuple[int, int]:
        """Convert hit coordinates to 0-based half-open slice.

        Returns:
            Tuple of (start_0based, end_halfopen).
        """
        return (self.start - 1, self.end)

    @property
    def is_on_target(self) -> bool:
        """Check if this is an on-target hit (exact match).

        Returns:
            True if mismatch_count is 0.
        """
        return self.mismatch_count == 0


@dataclass
class GuideScore:
    """Represents scoring for a guide RNA.

    Attributes:
        guide_id: Guide RNA identifier.
        specificity_score: Specificity score (0-1, higher is better).
        gc_score: GC content score (0-1, higher is better).
        position_score: Position score (0-1, higher is better).
        homopolymer_penalty: Homopolymer penalty (0-1, lower is better).
        final_score: Final combined score (0-1, higher is better).
        recommendation: Recommendation category.
    """

    guide_id: str
    specificity_score: float = 0.0
    gc_score: float = 0.0
    position_score: float = 0.0
    homopolymer_penalty: float = 0.0
    final_score: float = 0.0
    recommendation: str = "caution"  # excellent, good, caution, avoid

    def __post_init__(self) -> None:
        """Validate scores."""
        for score_name in [
            "specificity_score",
            "gc_score",
            "position_score",
            "homopolymer_penalty",
            "final_score",
        ]:
            score = getattr(self, score_name)
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"{score_name} must be between 0 and 1, got {score}"
                )
        if self.recommendation not in ("excellent", "good", "caution", "avoid"):
            raise ValueError(
                f"Recommendation must be 'excellent', 'good', 'caution', or 'avoid', "
                f"got '{self.recommendation}'"
            )

    def validate(self) -> tuple[bool, str | None]:
        """Validate the guide score.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.guide_id:
            return False, "Guide ID cannot be empty"
        for score_name in [
            "specificity_score",
            "gc_score",
            "position_score",
            "homopolymer_penalty",
            "final_score",
        ]:
            score = getattr(self, score_name)
            if not 0.0 <= score <= 1.0:
                return False, f"{score_name} must be between 0 and 1, got {score}"
        if self.recommendation not in ("excellent", "good", "caution", "avoid"):
            return False, (
                f"Recommendation must be 'excellent', 'good', 'caution', or 'avoid', "
                f"got '{self.recommendation}'"
            )
        return True, None

    @property
    def recommendation_label(self) -> str:
        """Return a formatted recommendation label.

        Returns:
            Recommendation with emoji.
        """
        labels = {
            "excellent": "⭐ Excellent",
            "good": "✅ Good",
            "caution": "⚠️ Caution",
            "avoid": "❌ Avoid",
        }
        return labels.get(self.recommendation, self.recommendation)


@dataclass
class OrganismProfile:
    """Represents an organism-specific configuration profile.

    Attributes:
        name: Profile identifier.
        display_name: Human-readable display name.
        default_pam: Default PAM pattern.
        spacer_length: Default spacer length.
        max_mismatches: Maximum mismatches for off-target search.
        recommended_gc_min: Minimum recommended GC content.
        recommended_gc_max: Maximum recommended GC content.
        high_gc_warning_threshold: GC threshold for high GC warning.
        prefer_cds_first_third_for_knockout: Prefer guides in first third of CDS.
        enable_bgc_annotation: Enable BGC annotation.
        offtarget_strictness: Off-target search strictness (low, medium, high).
    """

    name: str
    display_name: str
    default_pam: str = "NGG"
    spacer_length: int = 20
    max_mismatches: int = 3
    recommended_gc_min: float = 40.0
    recommended_gc_max: float = 80.0
    high_gc_warning_threshold: float = 75.0
    prefer_cds_first_third_for_knockout: bool = True
    enable_bgc_annotation: bool = False
    offtarget_strictness: str = "medium"  # low, medium, high

    def __post_init__(self) -> None:
        """Validate the profile."""
        if not self.name:
            raise ValueError("Profile name cannot be empty")
        if not self.display_name:
            raise ValueError("Display name cannot be empty")
        if self.spacer_length < 1:
            raise ValueError(f"Spacer length must be >= 1, got {self.spacer_length}")
        if self.max_mismatches < 0:
            raise ValueError(f"Max mismatches must be >= 0, got {self.max_mismatches}")
        if self.recommended_gc_min < 0 or self.recommended_gc_min > 100:
            raise ValueError(
                f"Recommended GC min must be 0-100, got {self.recommended_gc_min}"
            )
        if self.recommended_gc_max < 0 or self.recommended_gc_max > 100:
            raise ValueError(
                f"Recommended GC max must be 0-100, got {self.recommended_gc_max}"
            )
        if self.recommended_gc_min > self.recommended_gc_max:
            raise ValueError(
                f"GC min ({self.recommended_gc_min}) must be <= GC max ({self.recommended_gc_max})"
            )
        if self.offtarget_strictness not in ("low", "medium", "high"):
            raise ValueError(
                f"Off-target strictness must be 'low', 'medium', or 'high', "
                f"got '{self.offtarget_strictness}'"
            )

    def validate(self) -> tuple[bool, str | None]:
        """Validate the profile.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.name:
            return False, "Profile name cannot be empty"
        if not self.display_name:
            return False, "Display name cannot be empty"
        if self.spacer_length < 1:
            return False, f"Spacer length must be >= 1, got {self.spacer_length}"
        if self.max_mismatches < 0:
            return False, f"Max mismatches must be >= 0, got {self.max_mismatches}"
        if self.recommended_gc_min > self.recommended_gc_max:
            return False, (
                f"GC min ({self.recommended_gc_min}) must be <= "
                f"GC max ({self.recommended_gc_max})"
            )
        if self.offtarget_strictness not in ("low", "medium", "high"):
            return False, (
                f"Off-target strictness must be 'low', 'medium', or 'high', "
                f"got '{self.offtarget_strictness}'"
            )
        return True, None

    def is_gc_in_range(self, gc_content: float) -> bool:
        """Check if GC content is within recommended range.

        Args:
            gc_content: GC content as fraction (0-1).

        Returns:
            True if within range.
        """
        gc_percent = gc_content * 100
        return self.recommended_gc_min <= gc_percent <= self.recommended_gc_max

    def is_high_gc(self, gc_content: float) -> bool:
        """Check if GC content is above high GC warning threshold.

        Args:
            gc_content: GC content as fraction (0-1).

        Returns:
            True if above threshold.
        """
        gc_percent = gc_content * 100
        return gc_percent > self.high_gc_warning_threshold

    @classmethod
    def from_dict(cls, data: dict) -> OrganismProfile:
        """Create an OrganismProfile from a dictionary.

        Args:
            data: Dictionary with profile data.

        Returns:
            OrganismProfile instance.
        """
        return cls(
            name=data.get("name", "custom"),
            display_name=data.get("display_name", "Custom"),
            default_pam=data.get("default_pam", "NGG"),
            spacer_length=data.get("spacer_length", 20),
            max_mismatches=data.get("max_mismatches", 3),
            recommended_gc_min=data.get("recommended_gc_min", 40.0),
            recommended_gc_max=data.get("recommended_gc_max", 80.0),
            high_gc_warning_threshold=data.get("high_gc_warning_threshold", 75.0),
            prefer_cds_first_third_for_knockout=data.get(
                "prefer_cds_first_third_for_knockout", True
            ),
            enable_bgc_annotation=data.get("enable_bgc_annotation", False),
            offtarget_strictness=data.get("offtarget_strictness", "medium"),
        )
