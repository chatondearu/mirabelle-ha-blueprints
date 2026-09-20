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
    CONF_NAME,
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
    assert result["data"] == {
        CONF_NAME: "CDA Alarm",
        CONF_CODES: [],
        CONF_SENSORS_AWAY: [],
        CONF_SENSORS_HOME: [],
        CONF_SENSORS_NIGHT: [],
        CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
        CONF_EXIT_DELAY: DEFAULT_EXIT_DELAY,
        CONF_BLOCK_ARM_IF_OPEN: DEFAULT_BLOCK_ARM_IF_OPEN,
        CONF_FRIENT_DEVICE_ID: "",
        CONF_ENABLE_KEYPAD_FEEDBACK: False,
        CONF_KEYPAD_ENDPOINT: DEFAULT_KEYPAD_ENDPOINT,
    }


@pytest.mark.asyncio
async def test_options_flow_updates_settings(hass: HomeAssistant) -> None:
    """Save sensors, delays, codes, and Frient keypad settings."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            CONF_NAME: "CDA Alarm",
            CONF_CODES: [],
            CONF_SENSORS_AWAY: [],
            CONF_SENSORS_HOME: [],
            CONF_SENSORS_NIGHT: [],
            CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
            CONF_EXIT_DELAY: DEFAULT_EXIT_DELAY,
            CONF_BLOCK_ARM_IF_OPEN: DEFAULT_BLOCK_ARM_IF_OPEN,
            CONF_FRIENT_DEVICE_ID: "",
            CONF_ENABLE_KEYPAD_FEEDBACK: False,
            CONF_KEYPAD_ENDPOINT: DEFAULT_KEYPAD_ENDPOINT,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SENSORS_AWAY: ["binary_sensor.front_door"],
            CONF_SENSORS_HOME: ["binary_sensor.garage"],
            CONF_SENSORS_NIGHT: [],
            CONF_ENTRY_DELAY: 45,
            CONF_EXIT_DELAY: 90,
            CONF_BLOCK_ARM_IF_OPEN: False,
            CONF_FRIENT_DEVICE_ID: "frient-device-id",
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
            "codes_json": (
                '[{"name":"Alice","pin":"1234","rfid":"tag-1",'
                '"nfc_tag_id":"nfc-1"}]'
            ),
        },
    )

    assert result["type"] == "create_entry"
    assert entry.options[CONF_ENTRY_DELAY] == 45
    assert entry.options[CONF_SENSORS_AWAY] == ["binary_sensor.front_door"]
    assert entry.options[CONF_CODES] == [
        {
            "name": "Alice",
            "pin": "1234",
            "rfid": "tag-1",
            "nfc_tag_id": "nfc-1",
        }
    ]
    assert entry.options[CONF_FRIENT_DEVICE_ID] == "frient-device-id"


@pytest.mark.asyncio
async def test_options_flow_rejects_invalid_codes_json(
    hass: HomeAssistant,
) -> None:
    """Keep the options form open when codes JSON is invalid."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={CONF_NAME: "CDA Alarm"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SENSORS_AWAY: [],
            CONF_SENSORS_HOME: [],
            CONF_SENSORS_NIGHT: [],
            CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
            CONF_EXIT_DELAY: DEFAULT_EXIT_DELAY,
            CONF_BLOCK_ARM_IF_OPEN: DEFAULT_BLOCK_ARM_IF_OPEN,
            CONF_FRIENT_DEVICE_ID: "",
            CONF_ENABLE_KEYPAD_FEEDBACK: False,
            CONF_KEYPAD_ENDPOINT: DEFAULT_KEYPAD_ENDPOINT,
            "codes_json": '{"name":"Alice"}',
        },
    )

    assert result["type"] == "form"
    assert result["errors"] == {"codes_json": "invalid_codes"}


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
