"""Pipeline runner for the web UI.

Wraps run_design_pipeline for async execution in NiceGUI.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from actinoedit.core.design_types import DesignInput
from actinoedit.core.pipeline import DesignResult, run_design_pipeline
from actinoedit.core.profiles import list_profiles
from actinoedit.web.state import WebState

DEFAULT_TASK_TIMEOUT_S = 600.0


def build_design_input(state: WebState) -> DesignInput:
    """Build DesignInput from current web state."""
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
        design_mode=state.design_mode,
    )


def run_design(state: WebState) -> DesignResult:
    """Run the design pipeline with current state (blocking)."""
    input_params = build_design_input(state)

    def progress_callback(message: str) -> None:
        state.add_progress(message)

    def should_cancel() -> bool:
        return state.cancel_requested

    return run_design_pipeline(
        input_params,
        progress_callback,
        should_cancel=should_cancel,
    )


def _finalize_task_status(state: WebState, result: DesignResult | None) -> None:
    """Set terminal task status after the worker thread exits."""
    if state.task_status == "timeout":
        return

    if state.cancel_requested or (result is not None and result.cancelled):
        state.task_status = "cancelled"
        state.status_message = "Design cancelled."
        return

    if result is None:
        state.task_status = "failed"
        if not state.status_message:
            state.status_message = "Design did not complete."
        return

    if not result.guide_candidates:
        state.task_status = "completed"
        state.status_message = "Design finished with no guide candidates."
    else:
        state.task_status = "completed"
        state.status_message = f"Design complete: {len(result.guide_candidates)} guides."


def run_design_background(
    state: WebState,
    *,
    on_complete: Callable[[DesignResult | None, str | None], None] | None = None,
    timeout_s: float = DEFAULT_TASK_TIMEOUT_S,
) -> threading.Thread:
    """Run design in a background thread with optional timeout and cancel."""
    state.reset()
    state.is_running = True
    state.task_status = "running"
    state.status_message = "Design running in background..."

    def _worker() -> None:
        result: DesignResult | None = None
        error: str | None = None
        try:
            result = run_design(state)
            state.result = result
        except FileNotFoundError as exc:
            error = str(exc)
            state.error_message = error
            state.task_status = "failed"
            state.status_message = error
        except ValueError as exc:
            error = str(exc)
            state.error_message = error
            state.task_status = "failed"
            state.status_message = error
        except Exception as exc:
            error = f"Unexpected error: {exc}"
            state.error_message = error
            state.task_status = "failed"
            state.status_message = error
        finally:
            if state.task_status not in ("failed", "timeout"):
                _finalize_task_status(state, result)
            state.is_running = False
            if on_complete is not None:
                on_complete(result, error)

    thread = threading.Thread(target=_worker, daemon=True, name="actinoedit-design")
    thread.start()

    def _watch_timeout() -> None:
        thread.join(timeout=timeout_s)
        if thread.is_alive():
            state.cancel_requested = True
            state.is_running = False
            state.task_status = "timeout"
            state.status_message = f"Design timed out after {int(timeout_s)}s."
            state.error_message = state.status_message
            if on_complete is not None:
                on_complete(None, state.error_message)

    threading.Thread(target=_watch_timeout, daemon=True, name="actinoedit-design-timeout").start()
    return thread


def cancel_design(state: WebState) -> None:
    """Request cancellation of a running background design."""
    state.request_cancel()


def get_profile_names() -> list[str]:
    """Get list of available profile names."""
    return list_profiles()


def build_design_run_meta(state: WebState, result: DesignResult) -> dict:
    """Build DB audit metadata from web state and design result."""
    return {
        "genome_path": state.genome_path,
        "annotation_path": state.annotation_path,
        "target": state.target,
        "organism_profile": result.profile_name or state.profile_name,
        "pam": result.resolved_params.get("pam", state.pam),
        "design_mode": state.design_mode,
        "spacer_length": result.resolved_params.get("spacer_length", state.spacer_length),
        "max_mismatches": result.resolved_params.get("max_mismatches", state.max_mismatches),
        "parameters": {
            "source": "web",
            "version": result.version,
            "resolved_params": result.resolved_params,
            "input_file_summary": result.input_file_summary,
        },
        "report_paths": result.report_paths,
        "status": "cancelled" if result.cancelled else "completed",
    }


def autosave_design_reports(state: WebState, result: DesignResult) -> list[str]:
    """Write standard reports and attach paths to the design result."""
    from actinoedit.reports import write_design_reports

    auto_dir = Path(state.report_output_dir)
    auto_prefix = str(auto_dir / "last_design")
    report_paths = write_design_reports(
        result.guide_candidates,
        result.guide_scores,
        result.off_target_hits,
        result.target_region,
        result.warnings,
        auto_prefix,
        {
            "source": "web-auto",
            "version": result.version or "",
            "profile": result.profile_name or state.profile_name,
        },
    )
    result.set_report_paths_from_files(report_paths)
    return report_paths
