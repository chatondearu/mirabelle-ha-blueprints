"""Tests for Cover Manager cover entity."""

from __future__ import annotations

import pytest
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cover_manager.const import DOMAIN


@pytest.mark.asyncio
async def test_cover_initial_position(hass: HomeAssistant) -> None:
    """Cover should expose configured initial position after setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Cover",
            "switch_entity": "switch.test_cover",
            "travel_time": 30,
            "initial_position": 25,
            "pulse_gap": 0.8,
            "acceleration_duration": 0,
        },
        title="Test Cover",
    )
    entry.add_to_hass(hass)
    hass.states.async_set("switch.test_cover", "off", {})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    cover_entities = [e for e in entities if e.domain == COVER_DOMAIN]
    assert len(cover_entities) == 1

    state = hass.states.get(cover_entities[0].entity_id)
    assert state is not None
    assert int(round(state.attributes.get("position", 0))) == 25
