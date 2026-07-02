@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo  ActinoEdit Demo Launcher (v0.4)
echo  CRISPR Design Toolkit
echo ========================================
echo.

cd /d "%~dp0\.."

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10+ is required.
    python --version
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
) else (
    echo [1/3] Using existing virtual environment: .venv
)

call .venv\Scripts\activate.bat

echo [2/3] Installing ActinoEdit...
python -m pip install --upgrade pip -q
python -m pip install -e . -q

echo [3/3] Running headless acceptance check...
python -m actinoedit.web.app --acceptance-check --output-dir results\demo_acceptance
if errorlevel 1 (
    echo Acceptance check FAILED.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Demo acceptance passed.
echo  Starting Web UI with demo data...
echo  Open: http://127.0.0.1:8080
echo  Press Ctrl+C to stop
echo ========================================
echo.

actinoedit-web --demo --host 127.0.0.1 --port 8080 --show
pause
