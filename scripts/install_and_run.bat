@echo off
setlocal

echo ========================================
echo  ActinoEdit Installer
echo  CRISPR Design Toolkit
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/3] Installing ActinoEdit...
pip install --upgrade pip
pip install -e ".[dev]"

echo [3/3] Starting ActinoEdit...
echo.
echo ========================================
echo  ActinoEdit is running!
echo  Open browser: http://localhost:8080
echo  Press Ctrl+C to stop
echo ========================================
echo.

python -c "from actinoedit.web.app import create_app; from nicegui import ui; create_app(); ui.run(host='127.0.0.1', port=8080, reload=False, show=True)"

pause
