"""Tests for Cover Manager setup and unload."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cover_manager.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """Integration should set up cover platform and unload cleanly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Cover",
            "switch_entity": "switch.test_cover",
            "travel_time": 30,
            "initial_position": 0,
            "pulse_gap": 0.8,
            "acceleration_duration": 0,
        },
        title="Test Cover",
    )
    entry.add_to_hass(hass)
    hass.states.async_set("switch.test_cover", "off", {})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
