"""Tests for ACL Companion state notifications."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import DOMAIN
from custom_components.cda_alarm.notifications import (
    build_notify_payload,
    resolve_mobile_notify_services,
)


def test_build_notify_payload_critical_only_for_triggered() -> None:
    normal = build_notify_payload(STATE_ALARM_DISARMED)
    assert normal["message"] == "CDA Alarm: disarmed"
    assert "data" not in normal
    critical = build_notify_payload(STATE_ALARM_TRIGGERED)
    assert critical["message"] == "CDA Alarm: triggered"
    assert critical["data"]["priority"] == "high"


@pytest.mark.asyncio
async def test_resolve_mobile_notify_services_filters_by_user(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain="mobile_app",
        title="Pixel 7",
        data={"user_id": "user-a", "device_name": "Pixel 7"},
    )
    entry.add_to_hass(hass)
    other = MockConfigEntry(
        domain="mobile_app",
        title="Pixel 6",
        data={"user_id": "user-b", "device_name": "Pixel 6"},
    )
    other.add_to_hass(hass)

    async def _capture(_call: ServiceCall) -> None:
        return None

    hass.services.async_register("notify", "mobile_app_pixel_7", _capture)
    hass.services.async_register("notify", "mobile_app_pixel_6", _capture)
    assert resolve_mobile_notify_services(hass, {"user-a"}) == ["mobile_app_pixel_7"]


@pytest.mark.asyncio
async def test_state_notifications_for_acl_users(hass: HomeAssistant) -> None:
    calls: list[ServiceCall] = []

    async def _capture(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register("notify", "mobile_app_pixel_7", _capture)
    mobile = MockConfigEntry(
        domain="mobile_app",
        title="Pixel 7",
        data={"user_id": "user-acl", "device_name": "Pixel 7"},
    )
    mobile.add_to_hass(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            "name": "CDA Alarm",
            "codes": [{"name": "alice", "pin": "1234"}],
            "sensors_away": [],
            "sensors_home": [],
            "sensors_night": [],
            "entry_delay": 0,
            "exit_delay": 0,
            "block_arm_if_open": True,
            "access": {
                "mode": "users",
                "user_ids": ["user-acl"],
                "state_notifications": True,
            },
        },
    )
    entry.add_to_hass(hass)
    admin = SimpleNamespace(id="admin-1", is_admin=True, is_active=True, system_generated=False)
    acl_user = SimpleNamespace(id="user-acl", is_admin=False, is_active=True, system_generated=False)
    with patch.object(hass.auth, "async_get_users", new=AsyncMock(return_value=[admin, acl_user])):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entity_id = er.async_get(hass).async_get_entity_id("alarm_control_panel", DOMAIN, entry.entry_id)
        assert entity_id is not None
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_away",
            {ATTR_ENTITY_ID: entity_id, "code": "1234"},
            blocking=True,
        )
        await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY
    assert len(calls) == 1
    assert calls[0].data["message"] == "CDA Alarm: armed away"


@pytest.mark.asyncio
async def test_state_notifications_skip_arming_and_respect_disable(hass: HomeAssistant) -> None:
    calls: list[ServiceCall] = []

    async def _capture(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register("notify", "mobile_app_pixel_7", _capture)
    mobile = MockConfigEntry(
        domain="mobile_app",
        title="Pixel 7",
        data={"user_id": "admin-1", "device_name": "Pixel 7"},
    )
    mobile.add_to_hass(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CDA Alarm",
        data={
            "name": "CDA Alarm",
            "codes": [{"name": "alice", "pin": "1234"}],
            "sensors_away": [],
            "sensors_home": [],
            "sensors_night": [],
            "entry_delay": 0,
            "exit_delay": 5,
            "block_arm_if_open": True,
            "access": {"mode": "admin", "user_ids": [], "state_notifications": False},
        },
    )
    entry.add_to_hass(hass)
    admin = SimpleNamespace(id="admin-1", is_admin=True, is_active=True, system_generated=False)
    with patch.object(hass.auth, "async_get_users", new=AsyncMock(return_value=[admin])):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entity_id = er.async_get(hass).async_get_entity_id("alarm_control_panel", DOMAIN, entry.entry_id)
        assert entity_id is not None
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_away",
            {ATTR_ENTITY_ID: entity_id, "code": "1234"},
            blocking=True,
        )
        await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMING
    assert calls == []
