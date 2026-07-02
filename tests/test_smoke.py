"""Smoke tests for ActinoEdit package."""

from typer.testing import CliRunner

from actinoedit import __version__
from actinoedit.cli import app
from tests.conftest import strip_ansi

runner = CliRunner()


def test_version() -> None:
    """Test that version is defined."""
    assert __version__ == "0.4.0"


def test_cli_help() -> None:
    """Test that CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "actinoedit" in result.output.lower()


def test_cli_version() -> None:
    """Test that CLI version command works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in strip_ansi(result.output)


def test_cli_design_help() -> None:
    """Test that design command help works."""
    result = runner.invoke(app, ["design", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--genome" in output or "-genome" in output
    assert "--target" in output or "-target" in output


def test_cli_target_info_help() -> None:
    """Test that target-info command help works."""
    result = runner.invoke(app, ["target-info", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--genome" in output or "-genome" in output


def test_cli_base_edit_help() -> None:
    """Test that base-edit command help works."""
    result = runner.invoke(app, ["base-edit", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "--editor" in output or "-editor" in output
