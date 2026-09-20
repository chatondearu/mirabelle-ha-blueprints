"""Behavior tests for the alarm response automation blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.fixtures.blueprint_inputs import AUTOMATION_INPUTS
from tests.helpers.blueprint_loader import async_load_automation_blueprint


@pytest.mark.behavior
async def test_alarm_trigger_uses_only_available_noise_players(
    hass_with_entities: HomeAssistant,
) -> None:
    """Alarm noise should skip unavailable players while sound and TTS continue."""
    hass = hass_with_entities
    hass.states.async_set("media_player.available", "idle")
    hass.states.async_set("media_player.unavailable", "unavailable")

    siren_calls = async_mock_service(hass, "siren", "turn_on")
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    play_calls = async_mock_service(hass, "media_player", "play_media")
    tts_calls = async_mock_service(hass, "tts", "speak")

    inputs = {
        **AUTOMATION_INPUTS["alarm-response.yaml"],
        "mobile_notify_service": "",
        "telegram_chat_id": "",
        "noise_media_players": [
            "media_player.available",
            "media_player.unavailable",
        ],
        "alarm_sound_content_id": "media-source://media_source/local/alarm.mp3",
        "noise_volume": 0.7,
        "enable_alarm_tts": True,
        "alarm_tts_message": "Alarm triggered.",
        "tts_media_players": [
            "media_player.available",
            "media_player.unavailable",
        ],
    }
    await async_load_automation_blueprint(hass, "alarm-response.yaml", inputs)

    hass.states.async_set("alarm_control_panel.test", "triggered")
    await hass.async_block_till_done()

    assert siren_calls
    assert [call.data["entity_id"] for call in volume_calls] == [
        ["media_player.available"]
    ]
    assert [call.data["entity_id"] for call in play_calls] == [
        ["media_player.available"]
    ]
    assert play_calls[0].data["media_content_id"] == inputs["alarm_sound_content_id"]
    assert play_calls[0].data["media_content_type"] == "music"
    assert len(tts_calls) == 1
    assert tts_calls[0].data["media_player_entity_id"] == [
        "media_player.available"
    ]
    assert tts_calls[0].data["message"] == "Alarm triggered."


@pytest.mark.behavior
async def test_alarm_clear_and_silence_stop_noise_and_tts_players(
    hass_with_entities: HomeAssistant,
) -> None:
    """Leaving triggered or choosing Silence should stop noise and TTS media."""
    hass = hass_with_entities
    noise_player = "media_player.noise"
    tts_player = "media_player.tts"
    hass.states.async_set(noise_player, "idle")
    hass.states.async_set(tts_player, "idle")
    media_stop_calls = async_mock_service(hass, "media_player", "media_stop")
    async_mock_service(hass, "siren", "turn_on")
    async_mock_service(hass, "siren", "turn_off")

    inputs = {
        **AUTOMATION_INPUTS["alarm-response.yaml"],
        "mobile_notify_service": "",
        "telegram_chat_id": "",
        "noise_media_players": [noise_player],
        "tts_media_players": [tts_player],
    }
    await async_load_automation_blueprint(hass, "alarm-response.yaml", inputs)

    hass.states.async_set("alarm_control_panel.test", "triggered")
    await hass.async_block_till_done()
    hass.states.async_set("alarm_control_panel.test", "armed_away")
    await hass.async_block_till_done()
    assert [call.data["entity_id"] for call in media_stop_calls] == [
        [noise_player],
        [tts_player],
    ]

    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": "CDA_ALARM_SILENCE"},
    )
    await hass.async_block_till_done()
    assert [call.data["entity_id"] for call in media_stop_calls] == [
        [noise_player],
        [tts_player],
        [noise_player],
        [tts_player],
    ]
