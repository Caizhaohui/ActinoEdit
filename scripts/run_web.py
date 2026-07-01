#!/usr/bin/env python3
"""Script to run ActinoEdit web application."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from actinoedit.web.app import main

    if __name__ == "__main__":
        main()
except ImportError:
    print("Error: NiceGUI is not installed.")
    print("Install with: pip install nicegui")
    sys.exit(1)
