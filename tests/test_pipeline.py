"""Tests for design pipeline."""

from pathlib import Path

import pytest

from actinoedit.core.pipeline import (
    DesignInput,
    DesignResult,
    run_design_pipeline,
)


@pytest.fixture
def demo_files(tmp_path: Path) -> tuple[Path, Path]:
    """Create demo files for testing."""
    # Create FASTA file with enough sequence for scanning
    fasta_content = """>contig1 Demo genome
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
AGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
CGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
GGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
TGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
AGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
CGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
"""
    fasta_file = tmp_path / "genome.fasta"
    fasta_file.write_text(fasta_content)

    # Create GFF file
    gff_content = """##gff-version 3
contig1\tProdigal\tgene\t10\t200\t.\t+\t0\tID=geneA;locus_tag=SCO0001;gene=geneA;product=Hypothetical protein
contig1\tProdigal\tgene\t250\t400\t.\t-\t0\tID=geneB;locus_tag=SCO0002;gene=geneB;product=Transcriptional regulator
"""
    gff_file = tmp_path / "annotation.gff"
    gff_file.write_text(gff_content)

    return fasta_file, gff_file


class TestDesignInput:
    """Tests for DesignInput."""

    def test_default_values(self) -> None:
        """Test default values."""
        inp = DesignInput(
            genome_path="genome.fasta",
            annotation_path="annotation.gff",
            target="SCO0001",
        )
        assert inp.pam == "NGG"
        assert inp.spacer_length == 20
        assert inp.max_mismatches == 3


class TestDesignResult:
    """Tests for DesignResult."""

    def test_default_values(self) -> None:
        """Test default values."""
        result = DesignResult()
        assert result.target_region is None
        assert len(result.guide_candidates) == 0
        assert len(result.warnings) == 0


class TestRunDesignPipeline:
    """Tests for run_design_pipeline function."""

    def test_basic_pipeline(self, demo_files: tuple[Path, Path]) -> None:
        """Test basic pipeline execution."""
        fasta_file, gff_file = demo_files

        inp = DesignInput(
            genome_path=str(fasta_file),
            annotation_path=str(gff_file),
            target="SCO0001",
            pam="NGG",
            spacer_length=20,
        )

        result = run_design_pipeline(inp)
        assert isinstance(result, DesignResult)
        assert result.target_region is not None

    def test_pipeline_with_profile(self, demo_files: tuple[Path, Path]) -> None:
        """Test pipeline with organism profile."""
        fasta_file, gff_file = demo_files

        inp = DesignInput(
            genome_path=str(fasta_file),
            annotation_path=str(gff_file),
            target="SCO0001",
            organism_profile="streptomyces",
        )

        result = run_design_pipeline(inp)
        assert isinstance(result, DesignResult)

    def test_pipeline_invalid_target(self, demo_files: tuple[Path, Path]) -> None:
        """Test pipeline with invalid target."""
        fasta_file, gff_file = demo_files

        inp = DesignInput(
            genome_path=str(fasta_file),
            annotation_path=str(gff_file),
            target="nonexistent",
        )

        result = run_design_pipeline(inp)
        assert len(result.warnings) > 0

    def test_pipeline_missing_genome(self, demo_files: tuple[Path, Path]) -> None:
        """Test pipeline with missing genome."""
        _, gff_file = demo_files

        inp = DesignInput(
            genome_path="nonexistent.fasta",
            annotation_path=str(gff_file),
            target="SCO0001",
        )

        with pytest.raises(FileNotFoundError):
            run_design_pipeline(inp)

    def test_pipeline_progress_callback(self, demo_files: tuple[Path, Path]) -> None:
        """Test pipeline with progress callback."""
        fasta_file, gff_file = demo_files
        messages = []

        inp = DesignInput(
            genome_path=str(fasta_file),
            annotation_path=str(gff_file),
            target="SCO0001",
        )

        run_design_pipeline(inp, progress_callback=lambda m: messages.append(m))
        assert len(messages) > 0
