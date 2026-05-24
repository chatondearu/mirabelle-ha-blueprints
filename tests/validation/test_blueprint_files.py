"""Regression tests for blueprint file inventory and validate_blueprints.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[2]
BLUEPRINTS_DIR = REPO_ROOT / "blueprints"

_spec = importlib.util.spec_from_file_location(
    "validate_blueprints",
    REPO_ROOT / "scripts" / "validate_blueprints.py",
)
assert _spec and _spec.loader
_validate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_validate)
EXPECTED_BLUEPRINTS = _validate.EXPECTED_BLUEPRINTS


def test_expected_blueprint_files_exist() -> None:
    """Every documented blueprint file must exist on disk."""
    for rel in EXPECTED_BLUEPRINTS:
        assert (BLUEPRINTS_DIR / rel).is_file(), f"Missing blueprint: {rel}"


def test_validate_blueprints_script_succeeds() -> None:
    """CLI validation must pass for the current tree."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_blueprints.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
