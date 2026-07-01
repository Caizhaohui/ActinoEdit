"""NiceGUI local web application for ActinoEdit.

This module provides the main entry point for the ActinoEdit web UI.
It uses NiceGUI to create a local web interface for CRISPR guide RNA design.
"""

from __future__ import annotations

import argparse

from nicegui import ui

from actinoedit.web.pages import (
    create_demo_page,
    create_main_page,
    create_projects_page,
)
from actinoedit.web.state import WebState


def create_app() -> None:
    """Create and configure the NiceGUI application.

    This function sets up routes and global state.
    """
    # Shared application state
    state = WebState()

    @ui.page("/")
    def index() -> None:
        """Main design page."""
        create_main_page(state)

    @ui.page("/demo")
    def demo() -> None:
        """Demo page with pre-filled data."""
        create_demo_page(state)

    @ui.page("/projects")
    def projects() -> None:
        """Browse saved projects from local DB."""
        create_projects_page(state)


def main() -> None:
    """Start the ActinoEdit web application.

    This is the entry point for the `actinoedit-web` command.
    Supports headless mode for servers without GUI.
    """
    parser = argparse.ArgumentParser(description="ActinoEdit Web Application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--show", action="store_true", help="Open browser automatically")
    args = parser.parse_args()

    create_app()
    ui.run(
        title="ActinoEdit - CRISPR Design Toolkit",
        host=args.host,
        port=args.port,
        reload=False,
        show=args.show,
    )


if __name__ == "__main__":
    main()
