"""Tests for guide RNA scoring module."""

import pytest

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    OrganismProfile,
)
from actinoedit.core.scoring import (
    ScoringWeights,
    rank_guides,
    score_guide,
    score_guides,
)


@pytest.fixture
def sample_guide() -> GuideCandidate:
    """Sample guide for testing."""
    return GuideCandidate(
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


@pytest.fixture
def sample_profile() -> OrganismProfile:
    """Sample organism profile."""
    return OrganismProfile(
        name="streptomyces",
        display_name="Streptomyces",
        recommended_gc_min=40.0,
        recommended_gc_max=80.0,
    )


class TestScoringWeights:
    """Tests for ScoringWeights."""

    def test_default_weights(self) -> None:
        """Test default weights."""
        weights = ScoringWeights()
        assert weights.specificity == 0.4
        assert weights.gc == 0.2

    def test_normalize(self) -> None:
        """Test weight normalization."""
        weights = ScoringWeights(specificity=2.0, gc=2.0, position=2.0, homopolymer=2.0)
        weights.normalize()
        assert abs(weights.specificity - 0.25) < 0.01


class TestScoreGuide:
    """Tests for score_guide function."""

    def test_basic_score(self, sample_guide: GuideCandidate) -> None:
        """Test basic scoring."""
        score = score_guide(sample_guide)
        assert isinstance(score, GuideScore)
        assert 0.0 <= score.final_score <= 1.0

    def test_score_with_no_offtargets(self, sample_guide: GuideCandidate) -> None:
        """Test scoring with no off-targets."""
        score = score_guide(sample_guide, off_target_hits=[])
        assert score.specificity_score == 1.0

    def test_score_with_offtargets(self, sample_guide: GuideCandidate) -> None:
        """Test scoring with off-targets."""
        hits = [
            OffTargetHit(
                guide_id="guide_001", contig="c1", start=1, end=20,
                strand="+", sequence="A" * 20, mismatch_count=0
            ),
        ]
        score = score_guide(sample_guide, off_target_hits=hits)
        assert score.specificity_score < 1.0

    def test_score_with_profile(self, sample_guide: GuideCandidate, sample_profile: OrganismProfile) -> None:
        """Test scoring with profile."""
        score = score_guide(sample_guide, profile=sample_profile)
        assert isinstance(score, GuideScore)

    def test_recommendation(self, sample_guide: GuideCandidate) -> None:
        """Test recommendation."""
        score = score_guide(sample_guide)
        assert score.recommendation in ["excellent", "good", "caution", "avoid"]


class TestScoreGuides:
    """Tests for score_guides function."""

    def test_score_multiple(self) -> None:
        """Test scoring multiple guides."""
        guides = [
            GuideCandidate(
                guide_id=f"guide_{i:03d}",
                contig="contig1",
                spacer="ATCGATCGATCGATCGATCG",
                pam="NGG",
                start=100 + i * 30,
                end=119 + i * 30,
                strand="+",
                pam_start=120 + i * 30,
                pam_end=122 + i * 30,
                cut_site=117 + i * 30,
                gc_content=0.5,
            )
            for i in range(5)
        ]
        scores = score_guides(guides)
        assert len(scores) == 5


class TestRankGuides:
    """Tests for rank_guides function."""

    def test_ranking(self) -> None:
        """Test guide ranking."""
        guides = [
            GuideCandidate(
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
                gc_content=1.0,
            ),
            GuideCandidate(
                guide_id="guide_002",
                contig="contig1",
                spacer="ATATATATATATATATATAT",
                pam="NGG",
                start=200,
                end=219,
                strand="+",
                pam_start=220,
                pam_end=222,
                cut_site=217,
                gc_content=0.0,
            ),
        ]
        scores = score_guides(guides)
        ranked = rank_guides(guides, scores)
        assert len(ranked) == 2
        # Higher score should be first
        assert ranked[0][1].final_score >= ranked[1][1].final_score
