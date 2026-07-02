#!/usr/bin/env bash
# ActinoEdit v0.4 one-click demo launcher (Linux/macOS)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "========================================"
echo " ActinoEdit Demo Launcher (v0.4)"
echo " CRISPR Design Toolkit"
echo "========================================"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3.10+ and retry."
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  echo "ERROR: Python 3.10+ is required. Found: $(python3 --version 2>&1)"
  exit 1
fi

VENV="$ROOT/.venv"
if [[ ! -d "$VENV" ]]; then
  echo "[1/3] Creating virtual environment..."
  python3 -m venv "$VENV"
else
  echo "[1/3] Using existing virtual environment: $VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[2/3] Installing ActinoEdit..."
python -m pip install --upgrade pip -q
python -m pip install -e . -q

echo "[3/3] Running headless acceptance check..."
python -m actinoedit.web.app --acceptance-check --output-dir "$ROOT/results/demo_acceptance"

echo ""
echo "========================================"
echo " Demo acceptance passed."
echo " Starting Web UI with demo data..."
echo " Open: http://127.0.0.1:8080"
echo " Press Ctrl+C to stop"
echo "========================================"
echo ""

exec actinoedit-web --demo --host 127.0.0.1 --port 8080 --show
