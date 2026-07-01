"""Build a portable Windows package for ActinoEdit.

This creates a self-contained folder with:
- Embedded Python
- All dependencies
- Launch scripts

Usage:
    python scripts/build_windows_portable.py
"""

import shutil
from pathlib import Path


def build_portable(output_dir: Path = None) -> Path:
    """Build portable package.

    Args:
        output_dir: Output directory. Defaults to dist/portable

    Returns:
        Path to the created zip file.
    """
    project_root = Path(__file__).parent.parent

    if output_dir is None:
        output_dir = project_root / "dist" / "portable"

    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    print("Building ActinoEdit portable package...")

    # 1. Copy project files
    print("  Copying project files...")
    src_dir = output_dir / "actinoedit"
    src_dir.mkdir()

    # Copy src
    shutil.copytree(project_root / "src" / "actinoedit", src_dir / "actinoedit")

    # Copy examples
    shutil.copytree(project_root / "examples", src_dir / "examples")

    # Copy essential files
    for f in ["pyproject.toml", "README.md", "LICENSE"]:
        src_file = project_root / f
        if src_file.exists():
            shutil.copy2(src_file, src_dir / f)

    # 2. Create launcher scripts
    print("  Creating launcher scripts...")

    # Windows batch launcher
    bat_content = '''@echo off
cd /d "%~dp0"
echo Starting ActinoEdit...
echo.
echo Open browser: http://localhost:8080
echo Press Ctrl+C to stop
echo.
python\\python.exe -m actinoedit.web.app --host 127.0.0.1 --port 8080
pause
'''
    (output_dir / "Launch ActinoEdit.bat").write_text(bat_content)

    # PowerShell launcher (for modern Windows)
    ps1_content = '''Set-Location $PSScriptRoot
Write-Host "Starting ActinoEdit..." -ForegroundColor Green
Write-Host ""
Write-Host "Open browser: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
.\\python\\python.exe -m actinoedit.web.app --host 127.0.0.1 --port 8080
'''
    (output_dir / "Launch ActinoEdit.ps1").write_text(ps1_content)

    # 3. Create requirements file
    requirements = '''biopython>=1.80
pandas>=2.0
openpyxl>=3.1
typer>=0.9
rich>=13.0
jinja2>=3.1
pyyaml>=6.0
nicegui>=1.4
'''
    (src_dir / "requirements.txt").write_text(requirements)

    # 4. Create setup script for first run
    setup_content = '''@echo off
cd /d "%~dp0"
echo Installing ActinoEdit dependencies...
python\\python.exe -m pip install --upgrade pip
python\\python.exe -m pip install -r actinoedit\\requirements.txt
python\\python.exe -m pip install -e actinoedit
echo.
echo Installation complete!
echo Run "Launch ActinoEdit.bat" to start.
pause
'''
    (output_dir / "First Time Setup.bat").write_text(setup_content)

    print(f"  Package created: {output_dir}")
    print()
    print("To create a distributable zip:")
    print(f"  1. Download Python embeddable package to {output_dir / 'python'}")
    print(f"  2. Zip the {output_dir} folder")

    return output_dir


if __name__ == "__main__":
    build_portable()
