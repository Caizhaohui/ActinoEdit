"""Desktop entry point for ActinoEdit.

This script launches the NiceGUI web server and opens the browser.
Designed to be packaged with PyInstaller.
"""

import threading
import time
import webbrowser

from nicegui import ui

from actinoedit.web.pages import create_demo_page, create_main_page
from actinoedit.web.state import WebState


def create_app() -> None:
    """Create and configure the NiceGUI application."""
    state = WebState()

    @ui.page("/")
    def index() -> None:
        create_main_page(state)

    @ui.page("/demo")
    def demo() -> None:
        create_demo_page(state)


def open_browser(host: str, port: int) -> None:
    """Open browser after a short delay."""
    time.sleep(2)
    webbrowser.open(f"http://{host}:{port}")


def main() -> None:
    """Launch the application."""
    host = "127.0.0.1"
    port = 8080

    # Open browser in background thread
    threading.Thread(target=open_browser, args=(host, port), daemon=True).start()

    # Create and run app
    create_app()
    ui.run(
        title="ActinoEdit - CRISPR Design Toolkit",
        host=host,
        port=port,
        reload=False,
        show=False,
    )


if __name__ == "__main__":
    main()
