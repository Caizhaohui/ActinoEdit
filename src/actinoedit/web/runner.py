"""Pipeline runner for the web UI.

Wraps run_design_pipeline for async execution in NiceGUI.
"""

from __future__ import annotations

from actinoedit.core.pipeline import DesignInput, DesignResult, run_design_pipeline
from actinoedit.core.profiles import list_profiles
from actinoedit.web.state import WebState


def build_design_input(state: WebState) -> DesignInput:
    """Build DesignInput from current web state.

    Args:
        state: Current WebState.

    Returns:
        DesignInput object.

    Raises:
        ValueError: If required fields are missing.
    """
    if not state.genome_path:
        raise ValueError("Genome FASTA file is required")
    if not state.annotation_path:
        raise ValueError("Annotation file is required")
    if not state.target:
        raise ValueError("Target is required")

    return DesignInput(
        genome_path=state.genome_path,
        annotation_path=state.annotation_path,
        target=state.target,
        pam=state.pam,
        spacer_length=state.spacer_length,
        max_mismatches=state.max_mismatches,
        organism_profile=state.profile_name if state.profile_name else None,
        bgc_path=state.bgc_path or None,
    )


def run_design(state: WebState) -> DesignResult:
    """Run the design pipeline with current state.

    Args:
        state: Current WebState.

    Returns:
        DesignResult object.
    """
    input_params = build_design_input(state)

    def progress_callback(message: str) -> None:
        state.add_progress(message)

    return run_design_pipeline(input_params, progress_callback)


def get_profile_names() -> list[str]:
    """Get list of available profile names.

    Returns:
        List of profile name strings.
    """
    return list_profiles()
