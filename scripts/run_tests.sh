#!/usr/bin/env bash
# Run the same validation and pytest suite as CI (use before git push).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${SKIP_HA_TESTS:-}" == "1" ]]; then
  echo "SKIP_HA_TESTS=1 — skipping Home Assistant test suite."
  exit 0
fi

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON="$ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
  else
    echo "Error: Python not found. Create a venv: python3 -m venv .venv && .venv/bin/pip install -r requirements-test.txt"
    exit 1
  fi
fi

if ! "$PYTHON" -c "import pytest" 2>/dev/null; then
  echo "Error: test dependencies missing. Run: $PYTHON -m pip install -r requirements-test.txt"
  exit 1
fi

echo "==> yamllint blueprints/"
"$PYTHON" -m yamllint blueprints/

echo "==> validate_blueprints.py"
"$PYTHON" scripts/validate_blueprints.py

echo "==> pytest (blueprints + validation)"
"$PYTHON" -m pytest tests/ -q --tb=short

echo "==> pytest (cover-manager)"
PYTHONPATH="$ROOT/packages/cover-manager" "$PYTHON" -m pytest packages/cover-manager/tests -q --tb=short

echo "==> pytest (imeon_energy_api)"
PYTHONPATH="$ROOT/packages/imeon_energy_api" "$PYTHON" -m pytest packages/imeon_energy_api/tests -q --tb=short

echo "All tests passed."
