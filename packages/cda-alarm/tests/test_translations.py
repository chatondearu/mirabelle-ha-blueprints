"""Tests for shipped CDA Alarm translations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

COMPONENT_DIR = Path(__file__).parents[1] / "custom_components" / "cda_alarm"
TRANSLATIONS_DIR = COMPONENT_DIR / "translations"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _key_paths(value: Any, prefix: str = "") -> set[str]:
    """Return the flattened key paths of a translation mapping."""
    if not isinstance(value, dict):
        return {prefix}
    return {
        path
        for key, child in value.items()
        for path in _key_paths(child, f"{prefix}.{key}" if prefix else key)
    }


@pytest.mark.parametrize("language", ["en", "fr"])
def test_translation_files_match_strings(language: str) -> None:
    strings = _load(COMPONENT_DIR / "strings.json")
    translation = _load(TRANSLATIONS_DIR / f"{language}.json")
    assert _key_paths(translation) == _key_paths(strings)


@pytest.mark.parametrize("language", ["en", "fr"])
def test_translations_have_no_empty_values(language: str) -> None:
    translation = _load(TRANSLATIONS_DIR / f"{language}.json")

    def _values(value: Any) -> list[Any]:
        if isinstance(value, dict):
            return [item for child in value.values() for item in _values(child)]
        return [value]

    assert all(isinstance(item, str) and item.strip() for item in _values(translation))
