"""Sensor assignment helpers for CDA Alarm."""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    MODE_AWAY,
    MODE_HOME,
    MODE_NIGHT,
    MODE_OPTIONS,
)

_MODE_TO_CONF = {
    MODE_AWAY: CONF_SENSORS_AWAY,
    MODE_HOME: CONF_SENSORS_HOME,
    MODE_NIGHT: CONF_SENSORS_NIGHT,
}


def assignments_from_legacy(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Build assignments from the legacy per-mode sensor lists."""
    modes_by_entity: dict[str, list[str]] = {}
    for mode, conf_key in _MODE_TO_CONF.items():
        for entity_id in config.get(conf_key, []) or []:
            modes_by_entity.setdefault(entity_id, [])
            if mode not in modes_by_entity[entity_id]:
                modes_by_entity[entity_id].append(mode)
    return [
        {"entity_id": entity_id, "modes": modes}
        for entity_id, modes in modes_by_entity.items()
    ]


def normalize_assignments(raw: Any) -> list[dict[str, Any]]:
    """Validate and normalize sensor assignments."""
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        entity_id = item.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id:
            continue
        modes = [
            mode
            for mode in item.get("modes", [])
            if mode in MODE_OPTIONS
        ]
        # Preserve order away → home → night
        modes = [mode for mode in MODE_OPTIONS if mode in modes]
        if not modes:
            continue
        normalized.append({"entity_id": entity_id, "modes": modes})
    return normalized


def expand_assignments(
    assignments: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Expand assignments into legacy per-mode entity lists."""
    result = {
        CONF_SENSORS_AWAY: [],
        CONF_SENSORS_HOME: [],
        CONF_SENSORS_NIGHT: [],
    }
    for item in assignments:
        entity_id = item["entity_id"]
        for mode in item.get("modes", []):
            conf_key = _MODE_TO_CONF.get(mode)
            if conf_key and entity_id not in result[conf_key]:
                result[conf_key].append(entity_id)
    return result


def merge_runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return config with both assignments and expanded per-mode lists."""
    merged = dict(config)
    if CONF_SENSOR_ASSIGNMENTS in merged and merged[CONF_SENSOR_ASSIGNMENTS]:
        assignments = normalize_assignments(merged[CONF_SENSOR_ASSIGNMENTS])
    else:
        assignments = assignments_from_legacy(merged)
    expanded = expand_assignments(assignments)
    merged[CONF_SENSOR_ASSIGNMENTS] = assignments
    merged.update(expanded)
    return merged
