#!/usr/bin/env python3
"""Validate blueprint YAML files under blueprints/."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINTS_DIR = REPO_ROOT / "blueprints"

# Third-party blueprints in this repo (no [CDA] prefix required).
THIRD_PARTY_BLUEPRINTS = {
    "automations/frient_keypad_with_alarmo.yaml",
}

EXPECTED_BLUEPRINTS = [
    "automations/alarm-response.yaml",
    "automations/cover_control.yaml",
    "automations/cover_cover.yaml",
    "automations/cover_solar_thermal_optimization.yaml",
    "automations/cover_state_tracker.yaml",
    "automations/frient_keypad_with_alarmo.yaml",
    "automations/hvac-season-manager.yaml",
    "automations/living-area-adaptive-lighting.yaml",
    "automations/presence_based_lighting.yaml",
    "automations/reversible-split-thermostat.yaml",
    "automations/scheduled_bell_sound.yaml",
    "scripts/create-living-area-lighting-helpers.yaml",
    "scripts/create_schedule.yaml",
    "scripts/play_sound_with_volume_control.yaml",
    "scripts/set_cover_position.yaml",
]


def _sanitize_yaml(content: str) -> str:
    content = re.sub(r"!input\s+[^\n]+", '"__INPUT_PLACEHOLDER__"', content)
    content = re.sub(r"!include[^\n]*", '"__INCLUDE_PLACEHOLDER__"', content)
    content = re.sub(r"!secret\s+[^\n]+", '"__SECRET_PLACEHOLDER__"', content)
    return content


def validate_file(blueprint_file: Path) -> list[str]:
    errors: list[str] = []
    rel = blueprint_file.relative_to(BLUEPRINTS_DIR).as_posix()

    try:
        raw = blueprint_file.read_text(encoding="utf-8")
        data = yaml.safe_load(_sanitize_yaml(raw))
    except yaml.YAMLError as exc:
        return [f"{rel}: YAML syntax error — {exc}"]
    except OSError as exc:
        return [f"{rel}: cannot read file — {exc}"]

    if data is None:
        return [f"{rel}: empty or invalid YAML"]

    blueprint = data.get("blueprint")
    if not isinstance(blueprint, dict):
        return [f"{rel}: missing blueprint section"]

    name = blueprint.get("name")
    domain = blueprint.get("domain")
    if not name:
        errors.append(f"{rel}: missing blueprint.name")
    if domain not in ("automation", "script"):
        errors.append(f"{rel}: blueprint.domain must be automation or script (got {domain!r})")

    if rel not in THIRD_PARTY_BLUEPRINTS and name and "[CDA]" not in str(name):
        errors.append(f"{rel}: blueprint.name must include [CDA] prefix")

    ha_block = blueprint.get("homeassistant")
    if rel not in THIRD_PARTY_BLUEPRINTS:
        if not isinstance(ha_block, dict) or not ha_block.get("min_version"):
            errors.append(f"{rel}: missing blueprint.homeassistant.min_version")

    return errors


def main() -> int:
    errors: list[str] = []
    found: set[str] = set()

    for blueprint_file in sorted(BLUEPRINTS_DIR.rglob("*.yaml")):
        rel = blueprint_file.relative_to(BLUEPRINTS_DIR).as_posix()
        found.add(rel)
        errors.extend(validate_file(blueprint_file))

    missing = set(EXPECTED_BLUEPRINTS) - found
    extra = found - set(EXPECTED_BLUEPRINTS)

    for path in sorted(missing):
        errors.append(f"expected blueprint missing: {path}")
    for path in sorted(extra):
        errors.append(f"unexpected blueprint file (update EXPECTED_BLUEPRINTS): {path}")

    if errors:
        print("Blueprint validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"All {len(EXPECTED_BLUEPRINTS)} blueprints are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
