"""Tests for sensor assignment helpers."""

from __future__ import annotations

from custom_components.cda_alarm.const import (
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    MODE_AWAY,
    MODE_HOME,
    MODE_NIGHT,
)
from custom_components.cda_alarm.sensors import (
    assignments_from_legacy,
    expand_assignments,
    merge_runtime_config,
)


def test_expand_assignments() -> None:
    """Assignments expand into the legacy per-mode lists."""
    expanded = expand_assignments(
        [
            {
                "entity_id": "binary_sensor.door",
                "modes": [MODE_AWAY, MODE_HOME, MODE_NIGHT],
            },
            {"entity_id": "binary_sensor.motion", "modes": [MODE_AWAY]},
        ]
    )
    assert expanded[CONF_SENSORS_AWAY] == [
        "binary_sensor.door",
        "binary_sensor.motion",
    ]
    assert expanded[CONF_SENSORS_HOME] == ["binary_sensor.door"]
    assert expanded[CONF_SENSORS_NIGHT] == ["binary_sensor.door"]


def test_legacy_lists_become_assignments() -> None:
    """Old per-mode lists migrate into a single assignments structure."""
    assignments = assignments_from_legacy(
        {
            CONF_SENSORS_AWAY: ["binary_sensor.door", "binary_sensor.motion"],
            CONF_SENSORS_HOME: ["binary_sensor.door"],
            CONF_SENSORS_NIGHT: [],
        }
    )
    assert assignments == [
        {
            "entity_id": "binary_sensor.door",
            "modes": [MODE_AWAY, MODE_HOME],
        },
        {"entity_id": "binary_sensor.motion", "modes": [MODE_AWAY]},
    ]


def test_merge_runtime_config_prefers_assignments() -> None:
    """Runtime config keeps assignments and refreshes derived lists."""
    merged = merge_runtime_config(
        {
            CONF_SENSOR_ASSIGNMENTS: [
                {"entity_id": "binary_sensor.door", "modes": [MODE_NIGHT]},
            ],
            CONF_SENSORS_AWAY: ["binary_sensor.stale"],
            CONF_SENSORS_HOME: [],
            CONF_SENSORS_NIGHT: [],
        }
    )
    assert merged[CONF_SENSORS_AWAY] == []
    assert merged[CONF_SENSORS_NIGHT] == ["binary_sensor.door"]
