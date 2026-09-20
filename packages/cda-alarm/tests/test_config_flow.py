"""Tests for CDA Alarm config and options flows."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import (
    CONF_BLOCK_ARM_IF_OPEN,
    CONF_CODES,
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    CONF_KEYPADS,
    CONF_NAME,
    CONF_RESPONSE,
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    DEFAULT_BLOCK_ARM_IF_OPEN,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DEFAULT_KEYPAD_ENDPOINT,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """Create an entry with safe defaults from the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result["type"] == "form"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: "CDA Alarm"},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "CDA Alarm"
    assert result["data"][CONF_NAME] == "CDA Alarm"
    assert result["data"][CONF_SENSOR_ASSIGNMENTS] == []
    assert result["data"][CONF_SENSORS_AWAY] == []
    assert result["data"][CONF_KEYPADS] == []
    assert CONF_RESPONSE in result["data"]


@pytest.mark.asyncio
async def test_options_flow_redirects_to_sidebar(hass: HomeAssistant) -> None:
    """Options flow is a thin redirect that preserves current options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            CONF_NAME: "CDA Alarm",
            CONF_CODES: [{"name": "Alice", "pin": "1234"}],
            CONF_SENSOR_ASSIGNMENTS: [
                {"entity_id": "binary_sensor.door", "modes": ["away"]},
            ],
            CONF_SENSORS_AWAY: ["binary_sensor.door"],
            CONF_SENSORS_HOME: [],
            CONF_SENSORS_NIGHT: [],
            CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
            CONF_EXIT_DELAY: DEFAULT_EXIT_DELAY,
            CONF_BLOCK_ARM_IF_OPEN: DEFAULT_BLOCK_ARM_IF_OPEN,
            CONF_FRIENT_DEVICE_ID: "legacy-device",
            CONF_ENABLE_KEYPAD_FEEDBACK: False,
            CONF_KEYPAD_ENDPOINT: DEFAULT_KEYPAD_ENDPOINT,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert "panel_path" in result.get("description_placeholders", {})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {},
    )
    assert result["type"] == "create_entry"
    assert entry.options[CONF_SENSOR_ASSIGNMENTS][0]["entity_id"] == "binary_sensor.door"
    assert entry.options[CONF_CODES][0]["pin"] == "1234"
    assert entry.options[CONF_KEYPADS][0]["device_id"] == "legacy-device"


def test_manifest_declares_config_flow() -> None:
    """Integration manifest must advertise UI config flow to Home Assistant."""
    manifest_path = (
        Path(__file__).resolve().parent.parent
        / "custom_components"
        / "cda_alarm"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("config_flow") is True
    assert manifest.get("version") == "0.5.0"
