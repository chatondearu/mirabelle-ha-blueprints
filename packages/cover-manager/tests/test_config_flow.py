"""Tests for Cover Manager config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cover_manager.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_invalid_switch(hass: HomeAssistant) -> None:
    """Unknown switch entity should show invalid_switch_entity error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Living Room",
            "switch_entity": "switch.nonexistent",
            "travel_time": 30,
            "initial_position": 0,
            "pulse_gap": 0.8,
            "acceleration_duration": 0,
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_switch_entity"


@pytest.mark.asyncio
async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Valid switch entity should create a config entry."""
    hass.states.async_set("switch.test_cover", "off", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Living Room",
            "switch_entity": "switch.test_cover",
            "travel_time": 30,
            "initial_position": 0,
            "pulse_gap": 0.8,
            "acceleration_duration": 0,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room"
    assert result["data"]["switch_entity"] == "switch.test_cover"

