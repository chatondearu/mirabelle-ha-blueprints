"""Sensor assignment and keypad helpers for CDA Alarm."""

from __future__ import annotations

from typing import Any

from .access import normalize_access
from .cameras import normalize_cameras, normalize_sensor_camera_map
from .const import (
    CONF_ACCESS,
    CONF_CAMERAS,
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    CONF_KEYPAD_ENDPOINT_KEY,
    CONF_KEYPAD_FEEDBACK,
    CONF_KEYPAD_IS_DEFAULT,
    CONF_KEYPAD_SYNC_ZHA_PANEL,
    CONF_KEYPADS,
    CONF_RESPONSE,
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSOR_CAMERA_MAP,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    DEFAULT_KEYPAD_ENDPOINT,
    MODE_AWAY,
    MODE_HOME,
    MODE_NIGHT,
    MODE_OPTIONS,
)
from .response import normalize_response

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
        modes = [mode for mode in item.get("modes", []) if mode in MODE_OPTIONS]
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


def keypads_from_legacy(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a keypads list from the legacy single-device fields."""
    device_id = config.get(CONF_FRIENT_DEVICE_ID) or ""
    if not isinstance(device_id, str) or not device_id:
        return []
    return [
        {
            CONF_KEYPAD_DEVICE_ID: device_id,
            CONF_KEYPAD_IS_DEFAULT: True,
            CONF_KEYPAD_FEEDBACK: bool(
                config.get(CONF_ENABLE_KEYPAD_FEEDBACK, False)
            ),
            CONF_KEYPAD_SYNC_ZHA_PANEL: False,
            CONF_KEYPAD_ENDPOINT_KEY: int(
                config.get(CONF_KEYPAD_ENDPOINT, DEFAULT_KEYPAD_ENDPOINT)
                or DEFAULT_KEYPAD_ENDPOINT
            ),
        }
    ]


def normalize_keypads(raw: Any) -> list[dict[str, Any]]:
    """Validate and normalize keypad entries."""
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        device_id = item.get(CONF_KEYPAD_DEVICE_ID) or item.get(CONF_FRIENT_DEVICE_ID)
        if not isinstance(device_id, str) or not device_id:
            continue
        try:
            endpoint = int(
                item.get(CONF_KEYPAD_ENDPOINT_KEY, DEFAULT_KEYPAD_ENDPOINT)
                or DEFAULT_KEYPAD_ENDPOINT
            )
        except (TypeError, ValueError):
            endpoint = DEFAULT_KEYPAD_ENDPOINT
        normalized.append(
            {
                CONF_KEYPAD_DEVICE_ID: device_id,
                CONF_KEYPAD_IS_DEFAULT: bool(item.get(CONF_KEYPAD_IS_DEFAULT, False)),
                CONF_KEYPAD_FEEDBACK: bool(item.get(CONF_KEYPAD_FEEDBACK, False)),
                CONF_KEYPAD_SYNC_ZHA_PANEL: bool(
                    item.get(CONF_KEYPAD_SYNC_ZHA_PANEL, False)
                ),
                CONF_KEYPAD_ENDPOINT_KEY: endpoint,
            }
        )
    if normalized and not any(k[CONF_KEYPAD_IS_DEFAULT] for k in normalized):
        normalized[0][CONF_KEYPAD_IS_DEFAULT] = True
    return normalized


def resolve_active_keypads(
    keypads: list[dict[str, Any]],
    *,
    discovered_default: str | None = None,
) -> list[dict[str, Any]]:
    """Return keypads that should listen, falling back to a discovered default."""
    if keypads:
        return keypads
    if discovered_default:
        return [
            {
                CONF_KEYPAD_DEVICE_ID: discovered_default,
                CONF_KEYPAD_IS_DEFAULT: True,
                CONF_KEYPAD_FEEDBACK: False,
                CONF_KEYPAD_SYNC_ZHA_PANEL: False,
                CONF_KEYPAD_ENDPOINT_KEY: DEFAULT_KEYPAD_ENDPOINT,
            }
        ]
    return []


def merge_runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return config with assignments, keypads, response, and expanded lists."""
    merged = dict(config)
    if CONF_SENSOR_ASSIGNMENTS in merged and merged[CONF_SENSOR_ASSIGNMENTS]:
        assignments = normalize_assignments(merged[CONF_SENSOR_ASSIGNMENTS])
    else:
        assignments = assignments_from_legacy(merged)
    expanded = expand_assignments(assignments)
    merged[CONF_SENSOR_ASSIGNMENTS] = assignments
    merged.update(expanded)

    if CONF_KEYPADS in merged and merged[CONF_KEYPADS]:
        keypads = normalize_keypads(merged[CONF_KEYPADS])
    else:
        keypads = keypads_from_legacy(merged)
    merged[CONF_KEYPADS] = keypads
    # Keep legacy fields in sync for older listeners/tests.
    default = next(
        (k for k in keypads if k.get(CONF_KEYPAD_IS_DEFAULT)),
        keypads[0] if keypads else None,
    )
    if default:
        merged[CONF_FRIENT_DEVICE_ID] = default[CONF_KEYPAD_DEVICE_ID]
        merged[CONF_ENABLE_KEYPAD_FEEDBACK] = default[CONF_KEYPAD_FEEDBACK]
        merged[CONF_KEYPAD_ENDPOINT] = default[CONF_KEYPAD_ENDPOINT_KEY]
    else:
        merged[CONF_FRIENT_DEVICE_ID] = ""
        merged[CONF_ENABLE_KEYPAD_FEEDBACK] = False
        merged[CONF_KEYPAD_ENDPOINT] = DEFAULT_KEYPAD_ENDPOINT

    merged[CONF_RESPONSE] = normalize_response(merged.get(CONF_RESPONSE))
    merged[CONF_CAMERAS] = normalize_cameras(merged.get(CONF_CAMERAS))
    merged[CONF_SENSOR_CAMERA_MAP] = normalize_sensor_camera_map(
        merged.get(CONF_SENSOR_CAMERA_MAP)
    )
    merged[CONF_ACCESS] = normalize_access(merged.get(CONF_ACCESS))
    return merged
