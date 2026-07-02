"""v0.4 launcher and clean-environment acceptance tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from actinoedit.resources import (
    get_demo_annotation_path,
    get_demo_genome_path,
    get_examples_dir,
    get_profiles_dir,
)
from actinoedit.web.demo import load_demo_state, run_demo_acceptance

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestBundledResources:
    """Examples and profiles resolve after install or editable checkout."""

    def test_examples_dir_exists(self) -> None:
        examples = get_examples_dir()
        assert examples.is_dir()
        assert (examples / "demo_genome.fasta").is_file()

    def test_demo_paths_exist(self) -> None:
        assert get_demo_genome_path().is_file()
        assert get_demo_annotation_path("gff").is_file()

    def test_profiles_available(self) -> None:
        profiles = get_profiles_dir()
        assert profiles.is_dir()
        assert (profiles / "streptomyces.yaml").is_file()


class TestDemoMode:
    """Demo state and headless acceptance workflow."""

    def test_load_demo_state(self) -> None:
        from actinoedit.web.state import WebState

        state = WebState()
        load_demo_state(state)
        assert state.target == "geneA"
        assert Path(state.genome_path).is_file()
        assert Path(state.annotation_path).is_file()

    def test_headless_acceptance(self, tmp_path: Path) -> None:
        summary = run_demo_acceptance(output_dir=tmp_path / "acceptance")
        assert summary["guides"] > 0
        assert Path(summary["export"]).is_file()


class TestWebCliFlags:
    """actinoedit-web exposes v0.4 demo and acceptance flags."""

    def test_help_lists_demo_and_acceptance(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "actinoedit.web.app", "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "--demo" in output
        assert "--acceptance-check" in output

    def test_acceptance_check_subprocess(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "actinoedit.web.app",
                "--acceptance-check",
                "--output-dir",
                str(tmp_path / "subproc_acceptance"),
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout
        assert "demo acceptance ok" in result.stdout.lower()


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("ACTINOEDIT_RUN_CLEAN_INSTALL") != "1",
    reason="set ACTINOEDIT_RUN_CLEAN_INSTALL=1 to run network-dependent clean install test",
)
def test_clean_venv_install_acceptance(tmp_path: Path) -> None:
    """Simulate a fresh environment: venv -> pip install -e . -> acceptance check."""
    venv_dir = tmp_path / "clean_venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    assert python.is_file(), f"venv python missing at {python}"

    install_env = os.environ.copy()
    install_env["PIP_CACHE_DIR"] = str(tmp_path / "pip_cache")
    install_env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    install_result = subprocess.run(
        [str(python), "-m", "pip", "install", "-e", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        env=install_env,
        check=False,
        timeout=600,
    )
    assert install_result.returncode == 0, (
        "clean venv pip install failed\n"
        f"python: {python}\n"
        f"stdout:\n{install_result.stdout}\n"
        f"stderr:\n{install_result.stderr}"
    )

    version_result = subprocess.run(
        [str(python), "-c", "import sys; assert sys.version_info >= (3, 10)"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert version_result.returncode == 0, version_result.stderr + version_result.stdout

    out_dir = tmp_path / "clean_acceptance"
    result = subprocess.run(
        [
            str(python),
            "-m",
            "actinoedit.web.app",
            "--acceptance-check",
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, (
        "clean venv acceptance check failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_launcher_scripts_exist() -> None:
    """One-click launcher scripts are present for Unix and Windows."""
    assert (REPO_ROOT / "scripts" / "launch_demo.sh").is_file()
    assert (REPO_ROOT / "scripts" / "launch_demo.bat").is_file()


def test_launcher_scripts_require_python_310() -> None:
    """Launchers must check for Python 3.10+ before install."""
    sh = (REPO_ROOT / "scripts" / "launch_demo.sh").read_text()
    bat = (REPO_ROOT / "scripts" / "launch_demo.bat").read_text()
    assert "3, 10" in sh or "(3, 10)" in sh
    assert "(3, 10)" in bat
