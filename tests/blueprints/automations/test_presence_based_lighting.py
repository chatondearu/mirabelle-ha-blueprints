"""Behavior tests for presence_based_lighting blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.blueprints.conftest import smoke_load_automation
from tests.helpers.entities import seed_entities


@pytest.mark.behavior
async def test_presence_on_turns_light_on(hass_with_entities: HomeAssistant) -> None:
    """Presence detected should turn the configured light on."""
    hass = hass_with_entities
    turn_on = async_mock_service(hass, "light", "turn_on")
    turn_off = async_mock_service(hass, "light", "turn_off")

    await smoke_load_automation(hass, "presence_based_lighting.yaml")

    seed_entities(hass, {"binary_sensor.test_motion": ("on", {})})
    await hass.async_block_till_done()

    assert len(turn_on) == 1
    called_entity = turn_on[0].data.get("entity_id")
    if isinstance(called_entity, list):
        assert "light.test" in called_entity
    else:
        assert called_entity in (None, "light.test")
    assert len(turn_off) == 0


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Presence blueprint registers a for-delay timer on load."""
    return True
