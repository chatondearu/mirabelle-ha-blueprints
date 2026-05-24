"""Behavior tests for set_cover_position script blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.blueprints.conftest import smoke_load_script


@pytest.mark.behavior
async def test_set_cover_position_drives_switch(hass_with_entities: HomeAssistant) -> None:
    """Script should update helper and pulse the cover switch."""
    hass = hass_with_entities
    set_value = async_mock_service(hass, "input_text", "set_value")
    switch_on = async_mock_service(hass, "switch", "turn_on")
    switch_off = async_mock_service(hass, "switch", "turn_off")

    entity_id = await smoke_load_script(hass, "set_cover_position.yaml")

    await hass.services.async_call(
        "script",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(set_value) >= 1
    assert len(switch_on) >= 1
    assert len(switch_off) >= 1
