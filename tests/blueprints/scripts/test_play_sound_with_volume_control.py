"""Behavior tests for play_sound_with_volume_control script blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.blueprints.conftest import smoke_load_script


@pytest.mark.behavior
async def test_play_sound_calls_media_player_services(
    hass_with_entities: HomeAssistant,
) -> None:
    """Running the script should invoke media_player play and volume services."""
    hass = hass_with_entities
    turn_on = async_mock_service(hass, "media_player", "turn_on")
    play_media = async_mock_service(hass, "media_player", "play_media")
    volume_set = async_mock_service(hass, "media_player", "volume_set")

    entity_id = await smoke_load_script(hass, "play_sound_with_volume_control.yaml")

    await hass.services.async_call(
        "script",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(turn_on) >= 1
    assert len(play_media) >= 1
    assert len(volume_set) >= 1
