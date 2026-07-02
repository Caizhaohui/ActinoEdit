"""Integration tests for the design command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from actinoedit.cli import app

runner = CliRunner()


@pytest.fixture
def demo_files(tmp_path: Path) -> tuple[Path, Path]:
    """Create demo FASTA and GFF files for testing."""
    # Create FASTA file
    fasta_content = """>contig1 Demo genome
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
AGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
CGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
GGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
TGGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
"""
    fasta_file = tmp_path / "genome.fasta"
    fasta_file.write_text(fasta_content)

    # Create GFF file
    gff_content = """##gff-version 3
contig1\tProdigal\tgene\t10\t100\t.\t+\t0\tID=geneA;locus_tag=SCO0001;gene=geneA;product=Hypothetical protein
contig1\tProdigal\tgene\t150\t250\t.\t-\t0\tID=geneB;locus_tag=SCO0002;gene=geneB;product=Transcriptional regulator
"""
    gff_file = tmp_path / "annotation.gff"
    gff_file.write_text(gff_content)

    return fasta_file, gff_file


class TestDesignCommand:
    """Tests for the design command."""

    def test_design_basic(self, demo_files: tuple[Path, Path]) -> None:
        """Test basic design command."""
        fasta_file, gff_file = demo_files
        prefix = fasta_file.parent / "results" / "design"

        result = runner.invoke(app, [
            "design",
            "--genome", str(fasta_file),
            "--gff", str(gff_file),
            "--target", "SCO0001",
            "--output-prefix", str(prefix),
        ])

        assert result.exit_code == 0
        # Produces design_guides.csv
        csv_file = prefix.parent / "design_guides.csv"
        assert csv_file.exists(), f"Expected {csv_file} among {list((prefix.parent).glob('*'))}"

    def test_design_with_pam(self, demo_files: tuple[Path, Path]) -> None:
        """Test design command with custom PAM."""
        fasta_file, gff_file = demo_files
        prefix = fasta_file.parent / "results" / "guides_pam"

        result = runner.invoke(app, [
            "design",
            "--genome", str(fasta_file),
            "--gff", str(gff_file),
            "--target", "SCO0001",
            "--pam", "NGG",
            "--output-prefix", str(prefix),
        ])

        assert result.exit_code == 0

    def test_design_missing_genome(self, demo_files: tuple[Path, Path]) -> None:
        """Test design command with missing genome."""
        _, gff_file = demo_files

        result = runner.invoke(app, [
            "design",
            "--genome", "nonexistent.fasta",
            "--gff", str(gff_file),
            "--target", "SCO0001",
        ])

        assert result.exit_code == 1

    def test_design_missing_annotation(self, demo_files: tuple[Path, Path]) -> None:
        """Test design command with missing annotation."""
        fasta_file, _ = demo_files

        result = runner.invoke(app, [
            "design",
            "--genome", str(fasta_file),
            "--target", "SCO0001",
        ])

        assert result.exit_code == 1

    def test_design_invalid_target(self, demo_files: tuple[Path, Path]) -> None:
        """Test design command with invalid target."""
        fasta_file, gff_file = demo_files

        result = runner.invoke(app, [
            "design",
            "--genome", str(fasta_file),
            "--gff", str(gff_file),
            "--target", "nonexistent",
        ])

        assert result.exit_code == 1


class TestTargetInfoCommand:
    """Tests for the target-info command."""

    def test_target_info_basic(self, demo_files: tuple[Path, Path]) -> None:
        """Test basic target-info command."""
        fasta_file, gff_file = demo_files

        result = runner.invoke(app, [
            "target-info",
            "--genome", str(fasta_file),
            "--gff", str(gff_file),
            "--target", "SCO0001",
        ])

        assert result.exit_code == 0
        assert "SCO0001" in result.output


class TestHelpCommand:
    """Tests for help commands."""

    def test_main_help(self) -> None:
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "actinoedit" in result.output.lower()

    def test_design_help(self) -> None:
        """Test design help command."""
        from tests.conftest import strip_ansi

        result = runner.invoke(app, ["design", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--genome" in output or "-genome" in output
        assert "--target" in output or "-target" in output

    def test_target_info_help(self) -> None:
        """Test target-info help command."""
        from tests.conftest import strip_ansi

        result = runner.invoke(app, ["target-info", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--genome" in output or "-genome" in output

    def test_base_edit_help(self) -> None:
        """Test base-edit help command."""
        from tests.conftest import strip_ansi

        result = runner.invoke(app, ["base-edit", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--editor" in output or "-editor" in output
