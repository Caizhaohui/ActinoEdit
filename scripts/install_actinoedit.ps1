# ActinoEdit Windows Portable Installer
# Run this script in PowerShell to create a portable ActinoEdit package

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$BaseDir = "$env:USERPROFILE\Desktop\ActinoEdit-Portable"
$PythonVersion = "3.12.4"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ActinoEdit Portable Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create directory
if (Test-Path $BaseDir) {
    Write-Host "[INFO] Removing existing installation..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $BaseDir
}
New-Item -ItemType Directory -Path $BaseDir | Out-Null
Set-Location $BaseDir

# Step 1: Download Python
Write-Host "[1/5] Downloading Python $PythonVersion..." -ForegroundColor Green
$pythonZip = "$BaseDir\python.zip"
Invoke-WebRequest -Uri $PythonUrl -OutFile $pythonZip
Expand-Archive -Path $pythonZip -DestinationPath "$BaseDir\python"
Remove-Item $pythonZip

# Step 2: Configure Python
Write-Host "[2/5] Configuring Python..." -ForegroundColor Green
$pthFile = "$BaseDir\python\python312._pth"
(Get-Content $pthFile) -replace '#import site', 'import site' | Set-Content $pthFile

# Step 3: Install pip
Write-Host "[3/5] Installing pip..." -ForegroundColor Green
$getPip = "$BaseDir\python\get-pip.py"
Invoke-WebRequest -Uri $GetPipUrl -OutFile $getPip
& "$BaseDir\python\python.exe" $getPip --no-warn-script-location
Remove-Item $getPip

# Step 4: Install ActinoEdit
Write-Host "[4/5] Installing ActinoEdit (this may take a few minutes)..." -ForegroundColor Green
& "$BaseDir\python\python.exe" -m pip install actinoedit --no-warn-script-location

# Step 5: Create launcher
Write-Host "[5/5] Creating launcher..." -ForegroundColor Green

$batContent = @"
@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo  ActinoEdit - CRISPR Design Toolkit
echo ========================================
echo.
echo Starting server...
echo.
echo Open your browser and go to:
echo   http://localhost:8080
echo.
echo Press Ctrl+C to stop the server
echo.
python\python.exe -m actinoedit.web.app --host 127.0.0.1 --port 8080
pause
"@

$batContent | Out-File -Encoding ascii "$BaseDir\Start ActinoEdit.bat"

# Create README
$readmeContent = @"
ActinoEdit - CRISPR Design Toolkit for Actinomycetes
=====================================================

Quick Start:
1. Double-click "Start ActinoEdit.bat"
2. Open browser: http://localhost:8080
3. Use Demo page to try with example data

Features:
- Custom microbial genome support
- Organism-specific sgRNA design profiles
- High GC content optimization for actinomycetes
- CSV, Excel, and HTML report generation

For more information: https://github.com/actinoedit/actinoedit
"@

$readmeContent | Out-File -Encoding ascii "$BaseDir\README.txt"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "ActinoEdit installed to: $BaseDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start:" -ForegroundColor Yellow
Write-Host "  1. Go to: $BaseDir" -ForegroundColor White
Write-Host "  2. Double-click: Start ActinoEdit.bat" -ForegroundColor White
Write-Host "  3. Open browser: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
