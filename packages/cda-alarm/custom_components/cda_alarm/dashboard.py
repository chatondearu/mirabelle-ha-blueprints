"""Build dashboard snapshots for the CDA Alarm panel."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar, entity_registry as er

from .const import (
    ATTR_ARM_FAILURE,
    ATTR_ARM_MODE,
    ATTR_OPEN_SENSORS,
    CONF_ACCESS,
    CONF_ACCESS_MODE,
    CONF_CAMERAS,
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSOR_CAMERA_MAP,
)
from .sensors import merge_runtime_config

_PANEL_ATTRIBUTE_KEYS = (
    ATTR_OPEN_SENSORS,
    ATTR_ARM_FAILURE,
    ATTR_ARM_MODE,
    "code_format",
)
_OPEN_STATES = {"on", "open"}


def _entity_snapshot(entity_id: str, state: State | None) -> dict[str, Any]:
    """Return the dashboard-safe state of an entity."""
    return {
        "entity_id": entity_id,
        "name": state.name if state is not None else entity_id,
        "state": state.state if state is not None else STATE_UNAVAILABLE,
    }


def build_dashboard(
    hass: HomeAssistant,
    entry: ConfigEntry,
    panel_entity_id: str,
) -> dict[str, Any]:
    """Build a dashboard snapshot from the current runtime state."""
    config = merge_runtime_config({**entry.data, **entry.options})
    entity_registry = er.async_get(hass)
    area_registry = ar.async_get(hass)
    grouped: dict[str | None, dict[str, Any]] = {}

    for assignment in config[CONF_SENSOR_ASSIGNMENTS]:
        entity_id = assignment["entity_id"]
        registry_entry = entity_registry.async_get(entity_id)
        area_id = registry_entry.area_id if registry_entry is not None else None
        area = area_registry.async_get_area(area_id) if area_id else None
        group_key = area.id if area is not None else None
        group = grouped.setdefault(
            group_key,
            {
                "area_id": group_key,
                "name": area.name if area is not None else "Unassigned",
                "sensors": [],
            },
        )
        state = hass.states.get(entity_id)
        sensor = _entity_snapshot(entity_id, state)
        sensor["open"] = state is not None and state.state in _OPEN_STATES
        group["sensors"].append(sensor)

    panel_state = hass.states.get(panel_entity_id)
    panel_attributes = {
        key: panel_state.attributes.get(key)
        for key in _PANEL_ATTRIBUTE_KEYS
        if panel_state is not None and key in panel_state.attributes
    }

    highlighted_camera = None
    if panel_state is not None and panel_state.state == "triggered":
        open_sensors = panel_state.attributes.get(ATTR_OPEN_SENSORS) or {}
        if isinstance(open_sensors, dict):
            camera_map = config[CONF_SENSOR_CAMERA_MAP]
            highlighted_camera = next(
                (
                    camera_map[entity_id]
                    for entity_id in open_sensors
                    if entity_id in camera_map
                ),
                None,
            )

    cameras = [
        _entity_snapshot(entity_id, hass.states.get(entity_id))
        for entity_id in config[CONF_CAMERAS]
    ]
    areas = sorted(grouped.values(), key=lambda item: item["name"].lower())

    return {
        "entry_id": entry.entry_id,
        "panel_entity_id": panel_entity_id,
        "state": panel_state.state if panel_state is not None else None,
        "attributes": panel_attributes,
        "areas": areas,
        "cameras": cameras,
        "highlighted_camera": highlighted_camera,
        "access": {CONF_ACCESS_MODE: config[CONF_ACCESS][CONF_ACCESS_MODE]},
    }
