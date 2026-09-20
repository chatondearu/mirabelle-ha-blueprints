"""Tests for the Frient keypad event listener."""

from __future__ import annotations

import pytest
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_TRIGGER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import (
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    DOMAIN,
)

KEYPAD_IEEE = "00:0d:6f:00:0a:90:69:e7"
ZHA_DOMAIN = "zha"
ZHA_FEEDBACK_SERVICE = "issue_zigbee_cluster_command"


async def _setup_panel(hass: HomeAssistant, **overrides) -> str:
    data = {
        "name": "CDA Alarm",
        "codes": [{"name": "alice", "pin": "1234"}],
        "sensors_away": [],
        "sensors_home": [],
        "sensors_night": [],
        "entry_delay": 0,
        "exit_delay": 0,
        "block_arm_if_open": True,
        "frient_device_id": "device-frient-1",
        **overrides,
    }
    if data.get(CONF_ENABLE_KEYPAD_FEEDBACK):
        zha_entry = MockConfigEntry(domain=ZHA_DOMAIN)
        zha_entry.add_to_hass(hass)
        keypad_device = dr.async_get(hass).async_get_or_create(
            config_entry_id=zha_entry.entry_id,
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)},
        )
        data[CONF_FRIENT_DEVICE_ID] = keypad_device.id

    entry = MockConfigEntry(domain=DOMAIN, data=data, title="CDA Alarm")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = [
        entity
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        if entity.domain == ALARM_DOMAIN
    ]
    assert len(entities) == 1
    return entities[0].entity_id


def _fire_keypad_event(
    hass: HomeAssistant,
    *,
    arm_mode: int,
    code: str = "1234",
    device_id: str = "device-frient-1",
) -> None:
    hass.bus.async_fire(
        "zha_event",
        {
            "device_id": device_id,
            "command": "arm",
            "args": [],
            "params": {"arm_mode": arm_mode, "code": code},
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("arm_mode", "expected_state"),
    [
        (1, STATE_ALARM_ARMED_HOME),
        (2, STATE_ALARM_ARMED_NIGHT),
        (3, STATE_ALARM_ARMED_AWAY),
    ],
)
async def test_frient_event_arms_configured_mode(
    hass: HomeAssistant,
    arm_mode: int,
    expected_state: str,
) -> None:
    entity_id = await _setup_panel(hass)

    _fire_keypad_event(hass, arm_mode=arm_mode)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == expected_state


@pytest.mark.asyncio
async def test_frient_event_ignores_wrong_device(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)

    _fire_keypad_event(hass, arm_mode=3, device_id="another-device")
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_frient_event_ignores_bad_code(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)

    _fire_keypad_event(hass, arm_mode=3, code="0000")
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_frient_event_disarms_cda_panel(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_TRIGGER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_TRIGGERED

    _fire_keypad_event(hass, arm_mode=0)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_frient_event_pushes_enabled_keypad_feedback(
    hass: HomeAssistant,
) -> None:
    calls: list[ServiceCall] = []

    async def capture_feedback(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(
        ZHA_DOMAIN,
        ZHA_FEEDBACK_SERVICE,
        capture_feedback,
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
        },
    )

    _fire_keypad_event(
        hass,
        arm_mode=3,
        device_id=dr.async_get(hass).async_get_device(
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)}
        ).id,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY
    assert len(calls) == 1
    assert calls[0].data == {
        "ieee": KEYPAD_IEEE,
        "endpoint_id": 44,
        "cluster_id": 1281,
        "cluster_type": "out",
        "command": 4,
        "command_type": "client",
        "args": [3, 0, 0, 0],
    }


@pytest.mark.asyncio
async def test_frient_feedback_failure_does_not_block_arming(
    hass: HomeAssistant,
) -> None:
    attempts = 0

    async def reject_feedback(call: ServiceCall) -> None:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("ZHA rejected keypad feedback")

    hass.services.async_register(
        ZHA_DOMAIN,
        ZHA_FEEDBACK_SERVICE,
        reject_feedback,
    )
    entity_id = await _setup_panel(
        hass,
        **{
            CONF_ENABLE_KEYPAD_FEEDBACK: True,
            CONF_KEYPAD_ENDPOINT: 44,
        },
    )

    _fire_keypad_event(
        hass,
        arm_mode=1,
        device_id=dr.async_get(hass).async_get_device(
            identifiers={(ZHA_DOMAIN, KEYPAD_IEEE)}
        ).id,
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_HOME
    assert attempts == 1
