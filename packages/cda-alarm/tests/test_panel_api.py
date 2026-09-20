"""Tests for CDA Alarm websocket API and response runner."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_DISARM,
    SERVICE_ALARM_TRIGGER,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_ALARM_TRIGGERED
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm import websocket_api
from custom_components.cda_alarm.const import (
    CONF_ACCESS,
    CONF_CAMERAS,
    CONF_KEYPADS,
    CONF_RESPONSE,
    CONF_SENSOR_CAMERA_MAP,
    DOMAIN,
)
from custom_components.cda_alarm.keypad import discover_default_keypad_device_id
from custom_components.cda_alarm.response import (
    CdaAlarmResponseRunner,
    normalize_response,
)
from custom_components.cda_alarm.sensors import (
    keypads_from_legacy,
    merge_runtime_config,
    resolve_active_keypads,
)


def _ws_handler(handler):
    """Unwrap websocket decorators until the async implementation remains."""
    while getattr(handler, "__wrapped__", None) is not None:
        handler = handler.__wrapped__
    return handler


def _connection(*, is_admin: bool, user_id: str = "user-1") -> MagicMock:
    """Create a websocket connection with a concrete Home Assistant user."""
    connection = MagicMock()
    connection.user = MagicMock(id=user_id, is_admin=is_admin)
    return connection


def _dashboard_entry(
    hass: HomeAssistant, *, access_mode: str = "admin"
) -> MockConfigEntry:
    """Add a minimal dashboard-enabled CDA Alarm config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            "name": "CDA Alarm",
            "codes": [{"name": "Alice", "pin": "9999"}],
            "sensor_assignments": [],
            "access": {"mode": access_mode, "user_ids": []},
        },
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.asyncio
async def test_get_dashboard_denied_for_non_acl_user(hass: HomeAssistant) -> None:
    """Dashboard access rejects a non-admin outside the configured ACL."""
    entry = _dashboard_entry(hass)
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_get_dashboard)(
        hass,
        connection,
        {
            "id": 1,
            "type": "cda_alarm/get_dashboard",
            "entry_id": entry.entry_id,
        },
    )

    connection.send_error.assert_called_once_with(
        1, "unauthorized", "Dashboard access denied"
    )
    connection.send_result.assert_not_called()


@pytest.mark.asyncio
async def test_update_config_denied_for_non_admin(hass: HomeAssistant) -> None:
    """Configuration updates remain restricted to administrators."""
    entry = _dashboard_entry(hass, access_mode="everyone")
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_update_config)(
        hass,
        connection,
        {
            "id": 2,
            "type": "cda_alarm/update_config",
            "entry_id": entry.entry_id,
            "config": {},
        },
    )

    connection.send_error.assert_called_once_with(
        2, "unauthorized", "Administrator access required"
    )
    connection.send_result.assert_not_called()


@pytest.mark.asyncio
async def test_get_dashboard_ok_for_everyone(hass: HomeAssistant) -> None:
    """Everyone ACL exposes the dashboard snapshot to a non-admin."""
    entry = _dashboard_entry(hass, access_mode="everyone")
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_get_dashboard)(
        hass,
        connection,
        {
            "id": 3,
            "type": "cda_alarm/get_dashboard",
            "entry_id": entry.entry_id,
            "panel_entity_id": "alarm_control_panel.cda_alarm",
        },
    )

    connection.send_result.assert_called_once()
    assert "areas" in connection.send_result.call_args.args[1]
    connection.send_error.assert_not_called()


@pytest.mark.asyncio
async def test_get_dashboard_uses_registered_panel_entity_id(
    hass: HomeAssistant,
) -> None:
    """Dashboard reads only the panel entity registered to its config entry."""
    entry = _dashboard_entry(hass, access_mode="everyone")
    panel = er.async_get(hass).async_get_or_create(
        ALARM_DOMAIN,
        DOMAIN,
        entry.entry_id,
        suggested_object_id="entry_panel",
    )
    hass.states.async_set(panel.entity_id, "armed_away")
    hass.states.async_set("sensor.unrelated_secret", "secret-state")
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_get_dashboard)(
        hass,
        connection,
        {
            "id": 7,
            "type": "cda_alarm/get_dashboard",
            "entry_id": entry.entry_id,
        },
    )

    payload = connection.send_result.call_args.args[1]
    assert payload["panel_entity_id"] == panel.entity_id
    assert payload["state"] == "armed_away"
    assert payload["state"] != "secret-state"


def test_get_dashboard_schema_rejects_client_panel_entity_id() -> None:
    """Dashboard clients cannot select an arbitrary panel entity."""
    with pytest.raises(vol.MultipleInvalid):
        websocket_api.ws_get_dashboard._ws_schema(
            {
                "id": 7,
                "type": "cda_alarm/get_dashboard",
                "panel_entity_id": "sensor.unrelated_secret",
            }
        )


@pytest.mark.asyncio
async def test_non_admin_get_config_omits_codes(hass: HomeAssistant) -> None:
    """Dashboard-authorized users receive no alarm codes from get_config."""
    entry = _dashboard_entry(hass, access_mode="everyone")
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_get_config)(
        hass,
        connection,
        {"id": 4, "type": "cda_alarm/get_config", "entry_id": entry.entry_id},
    )

    payload = connection.send_result.call_args.args[1]
    assert "codes" not in payload
    assert payload[CONF_ACCESS] == {"mode": "everyone"}


@pytest.mark.asyncio
async def test_non_admin_get_config_denied_outside_acl(hass: HomeAssistant) -> None:
    """Configuration reads reject non-admin users outside the dashboard ACL."""
    entry = _dashboard_entry(hass)
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_get_config)(
        hass,
        connection,
        {"id": 5, "type": "cda_alarm/get_config", "entry_id": entry.entry_id},
    )

    connection.send_error.assert_called_once_with(
        5, "unauthorized", "Dashboard access denied"
    )
    connection.send_result.assert_not_called()


@pytest.mark.asyncio
async def test_admin_commands_reject_non_admin(hass: HomeAssistant) -> None:
    """Linked automation discovery remains restricted to administrators."""
    _dashboard_entry(hass, access_mode="everyone")
    connection = _connection(is_admin=False)

    await _ws_handler(websocket_api.ws_list_linked)(
        hass, connection, {"id": 6, "type": "cda_alarm/list_linked"}
    )

    connection.send_error.assert_called_once_with(
        6, "unauthorized", "Administrator access required"
    )
    connection.send_result.assert_not_called()


@pytest.mark.asyncio
async def test_websocket_get_and_update_config(hass: HomeAssistant) -> None:
    """Round-trip panel config through websocket command handlers."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            "name": "CDA Alarm",
            "codes": [],
            "sensor_assignments": [],
            "sensors_away": [],
            "sensors_home": [],
            "sensors_night": [],
            "entry_delay": 30,
            "exit_delay": 60,
            "block_arm_if_open": True,
            "frient_device_id": "",
            "keypads": [],
            "response": normalize_response(None),
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    connection = MagicMock()
    connection.user = MagicMock()
    connection.user.is_admin = True
    await _ws_handler(websocket_api.ws_get_config)(
        hass, connection, {"id": 1, "type": "cda_alarm/get_config"}
    )
    connection.send_result.assert_called_once()
    _call_id, payload = connection.send_result.call_args[0]
    assert _call_id == 1
    assert payload["entry_id"] == entry.entry_id
    assert payload[CONF_RESPONSE]["sirens"] == []

    connection.reset_mock()
    await _ws_handler(websocket_api.ws_update_config)(
        hass,
        connection,
        {
            "id": 2,
            "type": "cda_alarm/update_config",
            "entry_id": entry.entry_id,
            "config": {
                "sensor_assignments": [
                    {"entity_id": "binary_sensor.door", "modes": ["away", "home"]},
                ],
                "entry_delay": 15,
                "exit_delay": 45,
                "block_arm_if_open": False,
                "codes": [{"name": "Alice", "pin": "9999"}],
                "cameras": ["camera.hall", "light.invalid"],
                "sensor_camera_map": {
                    "binary_sensor.door": "camera.hall",
                    "binary_sensor.window": "light.invalid",
                },
                "access": {"mode": "users", "user_ids": ["user-1", ""]},
                "keypads": [
                    {
                        "device_id": "kp-1",
                        "is_default": True,
                        "feedback": True,
                        "endpoint": 44,
                    }
                ],
                "response": {
                    "sirens": ["siren.hall"],
                    "siren_duration": 10,
                    "noise_media_players": ["media_player.kitchen"],
                    "alarm_sound_content_id": "media-source://local/alarm.mp3",
                    "noise_volume": 0.8,
                    "enable_alarm_tts": True,
                    "alarm_tts_message": "Intrusion",
                    "tts_media_players": ["media_player.kitchen"],
                },
            },
        },
    )
    connection.send_result.assert_called_once()
    _call_id, payload = connection.send_result.call_args[0]
    assert payload["entry_delay"] == 15
    assert payload["sensor_assignments"][0]["entity_id"] == "binary_sensor.door"
    assert payload["keypads"][0]["device_id"] == "kp-1"
    assert payload["response"]["sirens"] == ["siren.hall"]
    refreshed = hass.config_entries.async_get_entry(entry.entry_id)
    assert refreshed is not None
    assert refreshed.options[CONF_CAMERAS] == ["camera.hall"]
    assert refreshed.options[CONF_SENSOR_CAMERA_MAP] == {
        "binary_sensor.door": "camera.hall"
    }
    assert refreshed.options[CONF_ACCESS] == {
        "mode": "users",
        "user_ids": ["user-1"],
    }

    connection.reset_mock()
    await _ws_handler(websocket_api.ws_list_linked)(
        hass, connection, {"id": 3, "type": "cda_alarm/list_linked"}
    )
    connection.send_result.assert_called_once()
    _call_id, payload = connection.send_result.call_args[0]
    assert "automations" in payload


def test_keypads_migrate_from_legacy_frient_device() -> None:
    """Legacy frient_device_id becomes a default keypad entry."""
    keypads = keypads_from_legacy(
        {
            "frient_device_id": "device-abc",
            "enable_keypad_feedback": True,
            "keypad_endpoint": 44,
        }
    )
    assert keypads == [
        {
            "device_id": "device-abc",
            "is_default": True,
            "feedback": True,
            "endpoint": 44,
        }
    ]
    merged = merge_runtime_config(
        {"frient_device_id": "device-abc", "enable_keypad_feedback": False}
    )
    assert merged[CONF_KEYPADS][0]["device_id"] == "device-abc"
    assert (
        resolve_active_keypads([], discovered_default="discovered-1")[0]["device_id"]
        == "discovered-1"
    )


def test_discover_default_keypad_device_id(hass: HomeAssistant) -> None:
    """Discovery finds Frient-like ZHA devices."""
    from homeassistant.helpers import device_registry as dr

    zha_entry = MockConfigEntry(domain="zha")
    zha_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", "aa:bb:cc:dd:ee:ff:00:11")},
        model="KEPZB-110",
        manufacturer="frient A/S",
        name="Keypad",
    )
    assert discover_default_keypad_device_id(hass) == device.id


@pytest.mark.asyncio
async def test_response_runner_start_stop(hass: HomeAssistant) -> None:
    """Response runner calls siren/media services and isolates failures."""
    calls: list[ServiceCall] = []

    async def _capture(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register("siren", "turn_on", _capture)
    hass.services.async_register("siren", "turn_off", _capture)
    hass.services.async_register("media_player", "volume_set", _capture)
    hass.services.async_register("media_player", "play_media", _capture)
    hass.services.async_register("media_player", "media_stop", _capture)

    hass.states.async_set("media_player.kitchen", "idle")
    runner = CdaAlarmResponseRunner(hass, "entry-1")
    runner.update_config(
        {
            CONF_RESPONSE: {
                "sirens": ["siren.hall"],
                "siren_duration": 5,
                "siren_tone": "alarm",
                "noise_media_players": ["media_player.kitchen"],
                "alarm_sound_content_id": "media-source://local/a.mp3",
                "noise_volume": 0.7,
                "enable_alarm_tts": False,
                "tts_media_players": [],
            }
        }
    )
    await runner.async_start()
    await hass.async_block_till_done()
    domains = {(call.domain, call.service) for call in calls}
    assert ("siren", "turn_on") in domains
    assert ("media_player", "volume_set") in domains
    assert ("media_player", "play_media") in domains

    calls.clear()
    await runner.async_stop()
    await hass.async_block_till_done()
    domains = {(call.domain, call.service) for call in calls}
    assert ("siren", "turn_off") in domains
    assert ("media_player", "media_stop") in domains


@pytest.mark.asyncio
async def test_triggered_starts_response(hass: HomeAssistant) -> None:
    """Entering triggered starts the response runner."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            "name": "CDA Alarm",
            "codes": [],
            "sensors_away": [],
            "sensors_home": [],
            "sensors_night": [],
            "entry_delay": 0,
            "exit_delay": 0,
            "block_arm_if_open": True,
            "response": {
                "sirens": ["siren.hall"],
                "noise_media_players": [],
                "tts_media_players": [],
            },
        },
    )
    entry.add_to_hass(hass)

    async def _capture(_call: ServiceCall) -> None:
        return None

    hass.services.async_register("siren", "turn_on", _capture)
    hass.services.async_register("siren", "turn_off", _capture)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = f"{ALARM_DOMAIN}.cda_alarm"

    with patch(
        "custom_components.cda_alarm.response.CdaAlarmResponseRunner.async_start",
        new_callable=AsyncMock,
    ) as start:
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_TRIGGER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == STATE_ALARM_TRIGGERED
        start.assert_awaited()

    with patch(
        "custom_components.cda_alarm.response.CdaAlarmResponseRunner.async_stop",
        new_callable=AsyncMock,
    ) as stop:
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_DISARM,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()
        stop.assert_awaited()
