"""Behavior tests for scheduled_bell_sound automation blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.blueprints.conftest import smoke_load_automation


@pytest.mark.behavior
async def test_scheduled_bell_triggers_sound_script(hass_with_entities: HomeAssistant) -> None:
    """Manual trigger should call the CDA play sound script."""
    hass = hass_with_entities
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "cda_play_sound_with_volume_control": {
                    "sequence": [{"service": "media_player.turn_on", "target": {"entity_id": "media_player.test"}}]
                }
            }
        },
    )
    script_calls = async_mock_service(hass, "script", "cda_play_sound_with_volume_control")

    automation_entity = await smoke_load_automation(hass, "scheduled_bell_sound.yaml")

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(script_calls) >= 1
