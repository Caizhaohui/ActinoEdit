"""Tests for web UI error paths and task lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from actinoedit.web import db_service
from actinoedit.web.runner import (
    build_design_input,
    cancel_design,
    run_design_background,
)
from actinoedit.web.state import WebState


def test_db_unavailable_message() -> None:
    msg = db_service.db_unavailable_message()
    assert "db init" in msg.lower()


def test_build_design_input_missing_annotation() -> None:
    state = WebState()
    state.genome_path = "genome.fasta"
    state.target = "geneA"
    with pytest.raises(ValueError, match="Annotation file is required"):
        build_design_input(state)


def test_cancel_design_sets_status() -> None:
    state = WebState()
    state.is_running = True
    state.task_status = "running"
    cancel_design(state)
    assert state.cancel_requested is True
    assert state.task_status == "cancelling"


def test_temp_upload_cleanup(tmp_path) -> None:
    state = WebState()
    old = tmp_path / "old.fasta"
    new = tmp_path / "new.fasta"
    old.write_text(">x\nA\n")
    new.write_text(">y\nC\n")
    state.temp_upload_paths = [str(old)]
    state.register_temp_upload(str(new))
    assert not old.exists()
    assert new.exists()
    state.cleanup_temp_uploads()
    assert not new.exists()
    assert state.temp_upload_paths == []


def test_show_no_guides_message() -> None:
    from actinoedit.core.pipeline import DesignResult

    state = WebState()
    state.task_status = "completed"
    state.result = DesignResult(guide_candidates=[])
    assert state.show_no_guides_message is True


def test_background_design_completes(demo_paths: tuple[Path, Path]) -> None:
    genome, gff = demo_paths
    state = WebState()
    state.genome_path = str(genome)
    state.annotation_path = str(gff)
    state.target = "geneA"
    state.profile_name = "streptomyces"

    done: list[bool] = []

    def on_complete(result, error) -> None:  # type: ignore[no-untyped-def]
        done.append(error is None and result is not None)

    thread = run_design_background(state, on_complete=on_complete, timeout_s=120)
    thread.join(timeout=120)
    assert done == [True]
    assert state.task_status == "completed"
    assert state.has_guides


@pytest.fixture
def demo_paths() -> tuple[Path, Path]:
    examples = Path(__file__).parent.parent / "examples"
    return examples / "demo_genome.fasta", examples / "demo_annotation.gff"
