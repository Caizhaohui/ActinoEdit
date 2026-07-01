"""Tests for report generation modules."""

from pathlib import Path

import pytest

from actinoedit.core.models import (
    GuideCandidate,
    GuideScore,
    OffTargetHit,
    TargetRegion,
)
from actinoedit.reports.excel import write_excel_report
from actinoedit.reports.html import write_html_report
from actinoedit.reports.tables import guides_to_dataframe, offtargets_to_dataframe


@pytest.fixture
def sample_guides() -> list[GuideCandidate]:
    """Sample guides for testing."""
    return [
        GuideCandidate(
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
        ),
        GuideCandidate(
            guide_id="guide_002",
            contig="contig1",
            spacer="GCGCGCGCGCGCGCGCGCGC",
            pam="NGG",
            start=200,
            end=219,
            strand="-",
            pam_start=220,
            pam_end=222,
            cut_site=217,
            gc_content=1.0,
        ),
    ]


@pytest.fixture
def sample_scores() -> list[GuideScore]:
    """Sample scores for testing."""
    return [
        GuideScore(
            guide_id="guide_001",
            specificity_score=0.9,
            gc_score=0.8,
            position_score=0.7,
            homopolymer_penalty=0.1,
            final_score=0.8,
            recommendation="good",
        ),
        GuideScore(
            guide_id="guide_002",
            specificity_score=0.7,
            gc_score=0.6,
            position_score=0.5,
            homopolymer_penalty=0.2,
            final_score=0.6,
            recommendation="good",
        ),
    ]


@pytest.fixture
def sample_offtargets() -> dict[str, list[OffTargetHit]]:
    """Sample off-targets for testing."""
    return {
        "guide_001": [
            OffTargetHit(
                guide_id="guide_001",
                contig="contig2",
                start=50,
                end=69,
                strand="+",
                sequence="ATCGATCGATCGATCGATCN",
                mismatch_count=1,
                mismatch_positions=[19],
            ),
        ],
    }


class TestGuidesToDataframe:
    """Tests for guides_to_dataframe function."""

    def test_basic(self, sample_guides: list[GuideCandidate]) -> None:
        """Test basic conversion."""
        df = guides_to_dataframe(sample_guides)
        assert len(df) == 2
        assert "guide_id" in df.columns

    def test_with_scores(self, sample_guides: list, sample_scores: list) -> None:
        """Test with scores."""
        df = guides_to_dataframe(sample_guides, scores=sample_scores)
        assert "final_score" in df.columns

    def test_with_offtargets(self, sample_guides: list, sample_offtargets: dict) -> None:
        """Test with off-targets."""
        df = guides_to_dataframe(sample_guides, off_target_hits=sample_offtargets)
        assert "off_target_1mm" in df.columns


class TestOfftargetsToDataframe:
    """Tests for offtargets_to_dataframe function."""

    def test_basic(self, sample_offtargets: dict) -> None:
        """Test basic conversion."""
        df = offtargets_to_dataframe(sample_offtargets)
        assert len(df) == 1
        assert "guide_id" in df.columns


class TestWriteExcelReport:
    """Tests for write_excel_report function."""

    def test_write(self, sample_guides: list, tmp_path: Path) -> None:
        """Test writing Excel report."""
        output = tmp_path / "report.xlsx"
        write_excel_report(sample_guides, output)
        assert output.exists()

    def test_with_data(self, sample_guides: list, sample_scores: list, tmp_path: Path) -> None:
        """Test writing with all data."""
        output = tmp_path / "report.xlsx"
        write_excel_report(
            sample_guides,
            output,
            scores=sample_scores,
            parameters={"pam": "NGG", "spacer_length": "20"},
            warnings=["Test warning"],
        )
        assert output.exists()


class TestWriteHtmlReport:
    """Tests for write_html_report function."""

    def test_write(self, sample_guides: list, tmp_path: Path) -> None:
        """Test writing HTML report."""
        output = tmp_path / "report.html"
        write_html_report(sample_guides, output)
        assert output.exists()

    def test_with_data(self, sample_guides: list, sample_scores: list, tmp_path: Path) -> None:
        """Test writing with all data."""
        output = tmp_path / "report.html"
        target = TargetRegion(
            contig="contig1", start=100, end=300, strand="+", label="geneA"
        )
        write_html_report(
            sample_guides,
            output,
            target=target,
            scores=sample_scores,
            parameters={"pam": "NGG"},
            warnings=["Test warning"],
        )
        assert output.exists()
