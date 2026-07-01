"""Tests for core data models."""

import pytest

from actinoedit.core.models import (
    Contig,
    GeneFeature,
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    OrganismProfile,
    TargetRegion,
)


class TestContig:
    """Tests for Contig model."""

    def test_contig_creation(self) -> None:
        """Test basic Contig creation."""
        contig = Contig(name="contig1", sequence="ATCGATCG")
        assert contig.name == "contig1"
        assert contig.sequence == "ATCGATCG"
        assert contig.length == 8

    def test_contig_gc_content(self) -> None:
        """Test GC content calculation."""
        contig = Contig(name="contig1", sequence="ATCGATCG")
        # 4 G/C out of 8 bases = 0.5
        assert contig.gc_content == 0.5

    def test_contig_gc_content_lowercase(self) -> None:
        """Test GC content with lowercase sequence."""
        contig = Contig(name="contig1", sequence="atcgatcg")
        assert contig.sequence == "ATCGATCG"
        assert contig.gc_content == 0.5

    def test_contig_empty_sequence(self) -> None:
        """Test Contig with empty sequence."""
        contig = Contig(name="contig1", sequence="")
        assert contig.length == 0
        assert contig.gc_content == 0.0

    def test_to_slice(self) -> None:
        """Test coordinate conversion to 0-based half-open."""
        contig = Contig(name="contig1", sequence="ATCGATCG")
        start, end = contig.to_slice(1, 4)
        assert start == 0
        assert end == 4

    def test_from_slice(self) -> None:
        """Test coordinate conversion from 0-based half-open."""
        start, end = Contig.from_slice(0, 4)
        assert start == 1
        assert end == 4

    def test_validate_valid(self) -> None:
        """Test validation of valid contig."""
        contig = Contig(name="contig1", sequence="ATCG")
        is_valid, error = contig.validate()
        assert is_valid is True
        assert error is None

    def test_validate_empty_name(self) -> None:
        """Test validation of empty name."""
        contig = Contig(name="", sequence="ATCG")
        is_valid, error = contig.validate()
        assert is_valid is False
        assert "name" in error.lower()

    def test_validate_empty_sequence(self) -> None:
        """Test validation of empty sequence."""
        contig = Contig(name="contig1", sequence="")
        is_valid, error = contig.validate()
        assert is_valid is False
        assert "empty" in error.lower()

    def test_get_subsequence(self) -> None:
        """Test subsequence extraction."""
        contig = Contig(name="contig1", sequence="ATCGATCG")
        subseq = contig.get_subsequence(2, 5)
        assert subseq == "TCGA"

    def test_get_subsequence_out_of_range(self) -> None:
        """Test subsequence with out of range coordinates."""
        contig = Contig(name="contig1", sequence="ATCG")
        with pytest.raises(IndexError, match="out of range"):
            contig.get_subsequence(1, 10)

    def test_get_subsequence_invalid_range(self) -> None:
        """Test subsequence with invalid range."""
        contig = Contig(name="contig1", sequence="ATCG")
        with pytest.raises(ValueError, match="must be <= end"):
            contig.get_subsequence(5, 2)


class TestGeneFeature:
    """Tests for GeneFeature model."""

    def test_gene_feature_creation(self) -> None:
        """Test basic GeneFeature creation."""
        gene = GeneFeature(
            contig="contig1",
            start=100,
            end=200,
            strand="+",
            locus_tag="SCO0001",
            gene_name="geneA",
        )
        assert gene.contig == "contig1"
        assert gene.start == 100
        assert gene.end == 200
        assert gene.strand == "+"
        assert gene.locus_tag == "SCO0001"
        assert gene.gene_name == "geneA"

    def test_gene_feature_length(self) -> None:
        """Test GeneFeature length calculation."""
        gene = GeneFeature(contig="contig1", start=100, end=200, strand="+")
        assert gene.length == 101

    def test_gene_feature_to_slice(self) -> None:
        """Test coordinate conversion."""
        gene = GeneFeature(contig="contig1", start=100, end=200, strand="+")
        start, end = gene.to_slice()
        assert start == 99
        assert end == 200

    def test_gene_feature_display_name(self) -> None:
        """Test display name property."""
        gene1 = GeneFeature(
            contig="contig1", start=100, end=200, strand="+",
            gene_name="geneA", locus_tag="SCO0001"
        )
        assert gene1.display_name == "geneA"

        gene2 = GeneFeature(
            contig="contig1", start=100, end=200, strand="+",
            locus_tag="SCO0001"
        )
        assert gene2.display_name == "SCO0001"

        gene3 = GeneFeature(contig="contig1", start=100, end=200, strand="+")
        assert gene3.display_name == "unknown"

    def test_gene_feature_overlaps(self) -> None:
        """Test overlap detection."""
        gene1 = GeneFeature(contig="contig1", start=100, end=200, strand="+")
        gene2 = GeneFeature(contig="contig1", start=150, end=250, strand="+")
        gene3 = GeneFeature(contig="contig1", start=300, end=400, strand="+")
        gene4 = GeneFeature(contig="contig2", start=100, end=200, strand="+")

        assert gene1.overlaps(gene2) is True
        assert gene1.overlaps(gene3) is False
        assert gene1.overlaps(gene4) is False

    def test_gene_feature_contains(self) -> None:
        """Test containment check."""
        gene = GeneFeature(contig="contig1", start=100, end=200, strand="+")
        assert gene.contains(120, 180) is True
        assert gene.contains(50, 250) is False
        assert gene.contains(50, 150) is False

    def test_gene_feature_invalid_start(self) -> None:
        """Test invalid start position."""
        with pytest.raises(ValueError, match="Start position must be >= 1"):
            GeneFeature(contig="contig1", start=0, end=200, strand="+")

    def test_gene_feature_invalid_end(self) -> None:
        """Test invalid end position."""
        with pytest.raises(ValueError, match="End .* must be >= start"):
            GeneFeature(contig="contig1", start=200, end=100, strand="+")

    def test_gene_feature_invalid_strand(self) -> None:
        """Test invalid strand."""
        with pytest.raises(ValueError, match="Strand must be"):
            GeneFeature(contig="contig1", start=100, end=200, strand="*")

    def test_gene_feature_validate(self) -> None:
        """Test validation."""
        gene = GeneFeature(contig="contig1", start=100, end=200, strand="+")
        is_valid, error = gene.validate()
        assert is_valid is True
        assert error is None


class TestTargetRegion:
    """Tests for TargetRegion model."""

    def test_target_region_creation(self) -> None:
        """Test basic TargetRegion creation."""
        target = TargetRegion(
            contig="contig1",
            start=100,
            end=500,
            strand="+",
            label="geneA",
        )
        assert target.contig == "contig1"
        assert target.start == 100
        assert target.end == 500
        assert target.label == "geneA"

    def test_target_region_length(self) -> None:
        """Test TargetRegion length calculation."""
        target = TargetRegion(contig="contig1", start=100, end=500, strand="+")
        assert target.length == 401

    def test_target_region_display_label(self) -> None:
        """Test display label property."""
        target1 = TargetRegion(
            contig="contig1", start=100, end=500, strand="+", label="geneA"
        )
        assert target1.display_label == "geneA"

        target2 = TargetRegion(contig="contig1", start=100, end=500, strand="+")
        assert target2.display_label == "contig1:100-500"

    def test_target_region_with_flank(self) -> None:
        """Test flank extension."""
        target = TargetRegion(
            contig="contig1", start=100, end=200, strand="+", label="geneA"
        )
        extended = target.with_flank(upstream=50, downstream=30)
        assert extended.start == 50
        assert extended.end == 230
        assert extended.label == "geneA"

    def test_target_region_with_flank_at_start(self) -> None:
        """Test flank extension at contig start."""
        target = TargetRegion(contig="contig1", start=10, end=20, strand="+")
        extended = target.with_flank(upstream=50, downstream=0)
        assert extended.start == 1  # Capped at 1

    def test_target_region_invalid_start(self) -> None:
        """Test invalid start position."""
        with pytest.raises(ValueError, match="Start position must be >= 1"):
            TargetRegion(contig="contig1", start=0, end=200, strand="+")

    def test_target_region_invalid_end(self) -> None:
        """Test invalid end position."""
        with pytest.raises(ValueError, match="End .* must be >= start"):
            TargetRegion(contig="contig1", start=200, end=100, strand="+")


class TestGuideCandidate:
    """Tests for GuideCandidate model."""

    def test_guide_candidate_creation(self) -> None:
        """Test basic GuideCandidate creation."""
        guide = GuideCandidate(
            guide_id="guide_001",
            contig="contig1",
            spacer="ATCGATCGATCGATCGATCG",
            pam="NGG",
            start=100,
            end=119,
            strand="+",
            pam_start=120,
            pam_end=122,
            cut_site=117,
            gc_content=0.5,
        )
        assert guide.guide_id == "guide_001"
        assert guide.spacer == "ATCGATCGATCGATCGATCG"
        assert guide.pam == "NGG"

    def test_guide_candidate_gc_auto_calc(self) -> None:
        """Test automatic GC content calculation."""
        guide = GuideCandidate(
            guide_id="guide_001",
            contig="contig1",
            spacer="GCGCGCGCGCGCGCGCGCGC",
            pam="NGG",
            start=100,
            end=119,
            strand="+",
            pam_start=120,
            pam_end=122,
            cut_site=117,
            gc_content=0.0,  # Will be auto-calculated
        )
        assert guide.gc_content == 1.0

    def test_guide_candidate_spacer_length(self) -> None:
        """Test spacer length property."""
        guide = GuideCandidate(
            guide_id="guide_001",
            contig="contig1",
            spacer="ATCGATCGATCGATCGATCG",
            pam="NGG",
            start=100,
            end=119,
            strand="+",
            pam_start=120,
            pam_end=122,
            cut_site=117,
            gc_content=0.5,
        )
        assert guide.spacer_length == 20

    def test_guide_candidate_display_id(self) -> None:
        """Test display ID property."""
        guide = GuideCandidate(
            guide_id="guide_001",
            contig="contig1",
            spacer="ATCGATCGATCGATCGATCG",
            pam="NGG",
            start=100,
            end=119,
            strand="+",
            pam_start=120,
            pam_end=122,
            cut_site=117,
            gc_content=0.5,
        )
        assert guide.display_id == "guide_001 (contig1:100-119)"

    def test_guide_candidate_invalid_id(self) -> None:
        """Test invalid guide ID."""
        with pytest.raises(ValueError, match="Guide ID cannot be empty"):
            GuideCandidate(
                guide_id="",
                contig="contig1",
                spacer="ATCG",
                pam="NGG",
                start=100,
                end=119,
                strand="+",
                pam_start=120,
                pam_end=122,
                cut_site=117,
                gc_content=0.5,
            )

    def test_guide_candidate_invalid_strand(self) -> None:
        """Test invalid strand."""
        with pytest.raises(ValueError, match="Strand must be"):
            GuideCandidate(
                guide_id="guide_001",
                contig="contig1",
                spacer="ATCG",
                pam="NGG",
                start=100,
                end=119,
                strand="*",
                pam_start=120,
                pam_end=122,
                cut_site=117,
                gc_content=0.5,
            )


class TestOffTargetHit:
    """Tests for OffTargetHit model."""

    def test_offtarget_hit_creation(self) -> None:
        """Test basic OffTargetHit creation."""
        hit = OffTargetHit(
            guide_id="guide_001",
            contig="contig2",
            start=50,
            end=69,
            strand="-",
            sequence="ATCGATCGATCGATCGATCG",
            mismatch_count=1,
            mismatch_positions=[5],
        )
        assert hit.guide_id == "guide_001"
        assert hit.mismatch_count == 1

    def test_offtarget_hit_is_on_target(self) -> None:
        """Test on-target detection."""
        hit_on = OffTargetHit(
            guide_id="guide_001",
            contig="contig1",
            start=100,
            end=119,
            strand="+",
            sequence="ATCGATCGATCGATCGATCG",
            mismatch_count=0,
        )
        assert hit_on.is_on_target is True

        hit_off = OffTargetHit(
            guide_id="guide_001",
            contig="contig2",
            start=50,
            end=69,
            strand="-",
            sequence="ATCGATCGATCGATCGATCG",
            mismatch_count=1,
            mismatch_positions=[5],
        )
        assert hit_off.is_on_target is False

    def test_offtarget_hit_invalid_mismatch_count(self) -> None:
        """Test invalid mismatch count."""
        with pytest.raises(ValueError, match="Mismatch count must be >= 0"):
            OffTargetHit(
                guide_id="guide_001",
                contig="contig2",
                start=50,
                end=69,
                strand="-",
                sequence="ATCG",
                mismatch_count=-1,
            )


class TestGuideScore:
    """Tests for GuideScore model."""

    def test_guide_score_creation(self) -> None:
        """Test basic GuideScore creation."""
        score = GuideScore(
            guide_id="guide_001",
            specificity_score=0.8,
            gc_score=0.9,
            position_score=0.7,
            homopolymer_penalty=0.1,
            final_score=0.8,
            recommendation="good",
        )
        assert score.guide_id == "guide_001"
        assert score.final_score == 0.8
        assert score.recommendation == "good"

    def test_guide_score_recommendation_label(self) -> None:
        """Test recommendation label property."""
        score = GuideScore(
            guide_id="guide_001",
            recommendation="excellent",
        )
        assert "Excellent" in score.recommendation_label

    def test_guide_score_invalid_score(self) -> None:
        """Test invalid score value."""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            GuideScore(
                guide_id="guide_001",
                specificity_score=1.5,
            )

    def test_guide_score_invalid_recommendation(self) -> None:
        """Test invalid recommendation."""
        with pytest.raises(ValueError, match="Recommendation must be"):
            GuideScore(
                guide_id="guide_001",
                recommendation="invalid",
            )


class TestOrganismProfile:
    """Tests for OrganismProfile model."""

    def test_organism_profile_creation(self) -> None:
        """Test basic OrganismProfile creation."""
        profile = OrganismProfile(
            name="streptomyces",
            display_name="Streptomyces / Actinomycete",
            default_pam="NGG",
            spacer_length=20,
        )
        assert profile.name == "streptomyces"
        assert profile.default_pam == "NGG"
        assert profile.spacer_length == 20

    def test_organism_profile_defaults(self) -> None:
        """Test OrganismProfile default values."""
        profile = OrganismProfile(name="test", display_name="Test")
        assert profile.max_mismatches == 3
        assert profile.recommended_gc_min == 40.0
        assert profile.recommended_gc_max == 80.0
        assert profile.offtarget_strictness == "medium"

    def test_organism_profile_is_gc_in_range(self) -> None:
        """Test GC range check."""
        profile = OrganismProfile(
            name="test",
            display_name="Test",
            recommended_gc_min=40.0,
            recommended_gc_max=80.0,
        )
        assert profile.is_gc_in_range(0.5) is True  # 50%
        assert profile.is_gc_in_range(0.3) is False  # 30%
        assert profile.is_gc_in_range(0.9) is False  # 90%

    def test_organism_profile_is_high_gc(self) -> None:
        """Test high GC check."""
        profile = OrganismProfile(
            name="test",
            display_name="Test",
            high_gc_warning_threshold=75.0,
        )
        assert profile.is_high_gc(0.8) is True  # 80%
        assert profile.is_high_gc(0.5) is False  # 50%

    def test_organism_profile_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "name": "custom",
            "display_name": "Custom Organism",
            "default_pam": "NGG",
            "spacer_length": 20,
            "max_mismatches": 3,
        }
        profile = OrganismProfile.from_dict(data)
        assert profile.name == "custom"
        assert profile.display_name == "Custom Organism"

    def test_organism_profile_invalid_gc_range(self) -> None:
        """Test invalid GC range."""
        with pytest.raises(ValueError, match="GC min .* must be <= GC max"):
            OrganismProfile(
                name="test",
                display_name="Test",
                recommended_gc_min=80.0,
                recommended_gc_max=40.0,
            )

    def test_organism_profile_invalid_strictness(self) -> None:
        """Test invalid strictness."""
        with pytest.raises(ValueError, match="Off-target strictness must be"):
            OrganismProfile(
                name="test",
                display_name="Test",
                offtarget_strictness="invalid",
            )
