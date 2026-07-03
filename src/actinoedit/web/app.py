"""NiceGUI local web application for ActinoEdit.

This module provides the main entry point for the ActinoEdit web UI.
It uses NiceGUI to create a local web interface for CRISPR guide RNA design.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nicegui import ui

from actinoedit.web.demo import load_demo_state, run_demo_acceptance
from actinoedit.web.pages import (
    create_demo_page,
    create_genomes_page,
    create_main_page,
    create_organisms_page,
    create_projects_page,
)
from actinoedit.web.state import WebState

DEFAULT_WEB_HOST = "127.0.0.1"


def create_app(*, demo_mode: bool = False, auto_run_design: bool = False) -> WebState:
    """Create and configure the NiceGUI application.

    Args:
        demo_mode: Pre-load demo data and open the demo page at ``/``.
        auto_run_design: In demo mode, run design automatically on page load.

    Returns:
        Shared application state.
    """
    state = WebState()
    if demo_mode:
        load_demo_state(state)

    @ui.page("/")
    def index() -> None:
        if demo_mode:
            create_demo_page(state, demo_banner=True, auto_run=auto_run_design)
        else:
            create_main_page(state)

    @ui.page("/demo")
    def demo() -> None:
        create_demo_page(state)

    @ui.page("/projects")
    def projects() -> None:
        create_projects_page(state)

    @ui.page("/organisms")
    def organisms() -> None:
        create_organisms_page(state)

    @ui.page("/genomes")
    def genomes() -> None:
        create_genomes_page(state)

    return state


def _run_acceptance_check(output_dir: str | None, db_url: str | None) -> int:
    """Headless v0.4 acceptance check (for CI and launcher verification)."""
    try:
        summary = run_demo_acceptance(output_dir=output_dir, db_url=db_url)
    except Exception as exc:
        print(f"ActinoEdit demo acceptance FAILED: {exc}", file=sys.stderr)
        return 1

    print("ActinoEdit demo acceptance OK")
    print(f"  guides designed: {summary['guides']}")
    print(f"  reports: {len(summary['reports'])} files")
    print(f"  db project: {summary['db_project']}")
    print(f"  export: {summary['export']}")
    return 0


def main() -> None:
    """Start the ActinoEdit web application.

    Entry point for ``actinoedit-web``.

    v0.4 one-click demo::

        actinoedit-web --demo

    Headless acceptance (CI / clean install)::

        actinoedit-web --acceptance-check
    """
    parser = argparse.ArgumentParser(description="ActinoEdit Web Application")
    parser.add_argument(
        "--host",
        default=DEFAULT_WEB_HOST,
        help=f"Host to bind (default: {DEFAULT_WEB_HOST})",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--show", action="store_true", help="Open browser automatically")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="One-click demo: load Streptomyces example data and open the design UI",
    )
    parser.add_argument(
        "--run-design",
        action="store_true",
        help="With --demo, automatically run design when the page loads",
    )
    parser.add_argument(
        "--acceptance-check",
        action="store_true",
        help="Headless v0.4 check: demo design, reports, DB save, export; then exit",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for --acceptance-check (default: results/demo_acceptance)",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="Database URL for --acceptance-check (default: temp SQLite in output dir)",
    )
    args = parser.parse_args()

    if args.acceptance_check:
        db_url = args.db_url
        if db_url is None and args.output_dir:
            db_path = Path(args.output_dir) / "acceptance.db"
            db_url = f"sqlite:///{db_path}"
        raise SystemExit(_run_acceptance_check(args.output_dir, db_url))

    host = args.host
    show_browser = args.show or args.demo

    create_app(demo_mode=args.demo, auto_run_design=args.run_design)
    ui.run(
        title="ActinoEdit - CRISPR Design Toolkit",
        host=host,
        port=args.port,
        reload=False,
        show=show_browser,
    )


if __name__ == "__main__":
    main()
