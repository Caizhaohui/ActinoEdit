"""Build ActinoEdit as a standalone desktop application using PyInstaller."""

import subprocess
import sys
from pathlib import Path


def build() -> None:
    """Build the standalone application."""
    project_root = Path(__file__).parent.parent

    # Entry point script
    entry_script = project_root / "scripts" / "run_desktop.py"

    # NiceGUI static files
    import nicegui
    nicegui_path = Path(nicegui.__file__).parent

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ActinoEdit",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--windowed",  # No console window on Windows
        # Add NiceGUI data files + ActinoEdit resources (examples, profiles)
        "--add-data", f"{nicegui_path}:nicegui",
        "--add-data", f"{project_root / 'examples'}:examples",
        # Hidden imports
        "--hidden-import", "nicegui",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "fastapi",
        "--hidden-import", "starlette",
        "--hidden-import", "jinja2",
        # Entry script
        str(entry_script),
    ]

    print("Building ActinoEdit standalone application...")
    print(f"Project root: {project_root}")
    print(f"NiceGUI path: {nicegui_path}")
    print()

    subprocess.run(cmd, cwd=str(project_root), check=True)

    # Output location
    dist_dir = project_root / "dist"
    if sys.platform == "win32":
        exe_path = dist_dir / "ActinoEdit.exe"
    else:
        exe_path = dist_dir / "ActinoEdit"

    print()
    print(f"Build complete! Executable: {exe_path}")
    print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    build()
