"""Tests for web module."""

from __future__ import annotations

import pytest

from actinoedit.core.models import GuideCandidate, GuideScore, OffTargetHit
from actinoedit.core.pipeline import DesignResult
from actinoedit.web.state import WebState


class TestWebState:
    """Tests for WebState dataclass."""

    def test_default_state(self) -> None:
        """Test default state creation."""
        state = WebState()
        assert state.genome_path == ""
        assert state.annotation_path == ""
        assert state.pam == "NGG"
        assert state.spacer_length == 20
        assert state.max_mismatches == 3
        assert state.profile_name == "streptomyces"
        assert state.result is None
        assert state.is_running is False

    def test_reset(self) -> None:
        """Test state reset."""
        state = WebState()
        state.result = DesignResult()
        state.is_running = True
        state.error_message = "test error"
        state.progress_messages = ["msg1"]

        state.reset()

        assert state.result is None
        assert state.is_running is False
        assert state.error_message == ""
        assert state.progress_messages == []

    def test_add_progress(self) -> None:
        """Test adding progress messages."""
        state = WebState()
        state.add_progress("Step 1")
        state.add_progress("Step 2")
        assert state.progress_messages == ["Step 1", "Step 2"]

    def test_has_result_false(self) -> None:
        """Test has_result when no result."""
        state = WebState()
        assert state.has_result is False

    def test_has_result_true(self) -> None:
        """Test has_result when result exists."""
        state = WebState()
        state.result = DesignResult()
        assert state.has_result is True

    def test_guide_count_no_result(self) -> None:
        """Test guide_count with no result."""
        state = WebState()
        assert state.guide_count == 0

    def test_guide_count_with_result(self) -> None:
        """Test guide_count with result."""
        state = WebState()
        guide = GuideCandidate(
            guide_id="test_001",
            contig="contig1",
            spacer="ATCGATCGATCGATCGATCG",
            pam="NGG",
            start=100,
            end=123,
            strand="+",
            pam_start=124,
            pam_end=126,
            cut_site=123,
            gc_content=0.5,
        )
        state.result = DesignResult(guide_candidates=[guide])
        assert state.guide_count == 1

    def test_filtered_guides_no_filters(self) -> None:
        """Test filtered_guides with no filters applied."""
        state = WebState()
        guide = GuideCandidate(
            guide_id="test_001",
            contig="contig1",
            spacer="ATCGATCGATCGATCGATCG",
            pam="NGG",
            start=100,
            end=123,
            strand="+",
            pam_start=124,
            pam_end=126,
            cut_site=123,
            gc_content=0.5,
        )
        score = GuideScore(
            guide_id="test_001",
            specificity_score=0.9,
            gc_score=0.8,
            position_score=0.7,
            homopolymer_penalty=0.0,
            final_score=0.85,
            recommendation="good",
        )
        state.result = DesignResult(
            guide_candidates=[guide],
            guide_scores=[score],
            off_target_hits={"test_001": []},
        )

        filtered = state.filtered_guides
        assert len(filtered) == 1
        assert filtered[0][0].guide_id == "test_001"
        assert filtered[0][1] is not None
        assert filtered[0][2] == 0  # off-target count

    def test_filtered_guides_by_recommendation(self) -> None:
        """Test filtering by recommendation."""
        state = WebState()
        state.filter_recommendation = "excellent"

        guide1 = GuideCandidate(
            guide_id="test_001", contig="c1", spacer="A" * 20, pam="NGG",
            start=100, end=123, strand="+", pam_start=124, pam_end=126, cut_site=123, gc_content=0.0,
        )
        guide2 = GuideCandidate(
            guide_id="test_002", contig="c1", spacer="G" * 20, pam="NGG",
            start=200, end=223, strand="+", pam_start=224, pam_end=226, cut_site=223, gc_content=1.0,
        )
        score1 = GuideScore(
            guide_id="test_001", specificity_score=0.9, gc_score=0.8,
            position_score=0.7, homopolymer_penalty=0.0, final_score=0.85, recommendation="good",
        )
        score2 = GuideScore(
            guide_id="test_002", specificity_score=0.95, gc_score=0.9,
            position_score=0.8, homopolymer_penalty=0.0, final_score=0.92, recommendation="excellent",
        )

        state.result = DesignResult(
            guide_candidates=[guide1, guide2],
            guide_scores=[score1, score2],
            off_target_hits={"test_001": [], "test_002": []},
        )

        filtered = state.filtered_guides
        assert len(filtered) == 1
        assert filtered[0][0].guide_id == "test_002"

    def test_filtered_guides_by_offtargets(self) -> None:
        """Test filtering by off-target count."""
        state = WebState()
        state.filter_max_offtargets = 0

        guide = GuideCandidate(
            guide_id="test_001", contig="c1", spacer="A" * 20, pam="NGG",
            start=100, end=123, strand="+", pam_start=124, pam_end=126, cut_site=123, gc_content=0.0,
        )
        ot_hit = OffTargetHit(
            guide_id="test_001", contig="c2", start=50, end=73, strand="+",
            sequence="A" * 20, mismatch_count=1, mismatch_positions=[5],
        )

        state.result = DesignResult(
            guide_candidates=[guide],
            guide_scores=[],
            off_target_hits={"test_001": [ot_hit]},
        )

        filtered = state.filtered_guides
        assert len(filtered) == 0  # filtered out due to off-target


class TestWebModuleImports:
    """Test that all web modules can be imported."""

    def test_import_state(self) -> None:
        """Test importing state module."""
        from actinoedit.web.state import WebState
        assert WebState is not None

    def test_import_runner(self) -> None:
        """Test importing runner module."""
        from actinoedit.web.runner import (
            build_design_input,
            get_profile_names,
            run_design,
        )
        assert callable(build_design_input)
        assert callable(run_design)
        assert callable(get_profile_names)

    def test_import_components(self) -> None:
        """Test importing components module."""
        from actinoedit.web.components import create_footer, create_header
        assert callable(create_header)
        assert callable(create_footer)

    def test_import_pages(self) -> None:
        """Test importing pages module."""
        from actinoedit.web.pages import create_demo_page, create_main_page
        assert callable(create_main_page)
        assert callable(create_demo_page)

    def test_import_app(self) -> None:
        """Test importing app module."""
        from actinoedit.web.app import create_app, main
        assert callable(main)
        assert callable(create_app)


class TestRunnerFunctions:
    """Test runner utility functions."""

    def test_get_profile_names(self) -> None:
        """Test getting profile names."""
        from actinoedit.web.runner import get_profile_names
        profiles = get_profile_names()
        assert isinstance(profiles, list)
        assert "streptomyces" in profiles

    def test_build_design_input_missing_genome(self) -> None:
        """Test building DesignInput with missing genome."""
        from actinoedit.web.runner import build_design_input
        state = WebState()
        state.annotation_path = "test.gff"
        state.target = "geneA"

        with pytest.raises(ValueError, match="Genome FASTA file is required"):
            build_design_input(state)

    def test_build_design_input_missing_annotation(self) -> None:
        """Test building DesignInput with missing annotation."""
        from actinoedit.web.runner import build_design_input
        state = WebState()
        state.genome_path = "test.fasta"
        state.target = "geneA"

        with pytest.raises(ValueError, match="Annotation file is required"):
            build_design_input(state)

    def test_build_design_input_missing_target(self) -> None:
        """Test building DesignInput with missing target."""
        from actinoedit.web.runner import build_design_input
        state = WebState()
        state.genome_path = "test.fasta"
        state.annotation_path = "test.gff"

        with pytest.raises(ValueError, match="Target is required"):
            build_design_input(state)
