"""Tests for CDA Alarm panel entity."""

from __future__ import annotations

import asyncio
import logging

import pytest
from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_DISARM,
    SERVICE_ALARM_TRIGGER,
)
from homeassistant.const import (
    ATTR_CODE,
    ATTR_ENTITY_ID,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.cda_alarm.const import (
    ATTR_ARM_FAILURE,
    ATTR_ARM_MODE,
    DOMAIN,
    EVENT_ARM_FAILED,
    REASON_OPEN_SENSORS,
)


async def _setup_panel(hass: HomeAssistant, **overrides) -> str:
    data = {
        "name": "CDA Alarm",
        "codes": [{"name": "alice", "pin": "1234"}],
        "sensors_away": ["binary_sensor.front_door"],
        "sensors_home": [],
        "sensors_night": [],
        "entry_delay": 0,
        "exit_delay": 0,
        "block_arm_if_open": True,
        **overrides,
    }
    entry = MockConfigEntry(domain=DOMAIN, data=data, title="CDA Alarm")
    entry.add_to_hass(hass)
    if hass.states.get("binary_sensor.front_door") is None:
        hass.states.async_set("binary_sensor.front_door", "off", {})
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


@pytest.mark.asyncio
async def test_arm_away_and_trigger(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY

    hass.states.async_set("binary_sensor.front_door", "on", {})
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED
    assert "binary_sensor.front_door" in (state.attributes.get("open_sensors") or {})


@pytest.mark.asyncio
async def test_block_arm_when_sensor_open(hass: HomeAssistant) -> None:
    hass.states.async_set("binary_sensor.front_door", "on", {})
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_arm_away_after_exit_delay(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass, exit_delay=0.01)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMING

    await asyncio.sleep(0.02)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_block_arm_when_sensor_opens_during_exit_delay(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    entity_id = await _setup_panel(hass, exit_delay=0.01)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMING

    hass.states.async_set("binary_sensor.front_door", "on", {})
    await hass.async_block_till_done()
    with caplog.at_level(logging.WARNING):
        await asyncio.sleep(0.02)
        await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED
    assert "Refusing to arm CDA Alarm because sensors are open" in caplog.text


@pytest.mark.asyncio
async def test_entry_delay_triggers_alarm(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass, entry_delay=0.01)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )

    hass.states.async_set("binary_sensor.front_door", "on", {})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY

    await asyncio.sleep(0.02)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_TRIGGERED


@pytest.mark.asyncio
async def test_disarm_with_code(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_TRIGGER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_reject_bad_code(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "0000"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_arm_and_disarm_with_rfid_badge(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(
        hass,
        codes=[{"name": "bob", "rfid": "AA:BB:CC:DD"}],
    )
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "AA:BB:CC:DD"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "AA:BB:CC:DD"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED


@pytest.mark.asyncio
async def test_arm_with_nfc_tag_id(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(
        hass,
        codes=[{"name": "carol", "nfc_tag_id": "home-tag-1"}],
    )
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "home-tag-1"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_armed_state_survives_reload(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_AWAY
    assert state.attributes[ATTR_ARM_MODE] == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_restored_panel_reevaluates_sensors(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY

    # The door opens while the integration is down, so the restored panel must
    # notice it instead of waiting for a fresh state change event.
    hass.states.async_set("binary_sensor.front_door", "on", {})
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_TRIGGERED
    assert "binary_sensor.front_door" in state.attributes["open_sensors"]


@pytest.mark.asyncio
async def test_triggered_state_survives_reload(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_TRIGGER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_TRIGGERED

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_ALARM_TRIGGERED


@pytest.mark.asyncio
async def test_arm_failure_after_exit_delay_is_observable(
    hass: HomeAssistant,
) -> None:
    entity_id = await _setup_panel(hass, exit_delay=0.01)
    events = async_capture_events(hass, EVENT_ARM_FAILED)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMING

    hass.states.async_set("binary_sensor.front_door", "on", {})
    await hass.async_block_till_done()
    await asyncio.sleep(0.02)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_DISARMED
    assert state.attributes[ATTR_ARM_FAILURE]["reason"] == REASON_OPEN_SENSORS
    assert len(events) == 1
    assert events[0].data[ATTR_ENTITY_ID] == entity_id
    assert events[0].data["reason"] == REASON_OPEN_SENSORS
    assert events[0].data["mode"] == STATE_ALARM_ARMED_AWAY
    assert "binary_sensor.front_door" in events[0].data["open_sensors"]


@pytest.mark.asyncio
async def test_arm_failure_is_cleared_on_next_arm(hass: HomeAssistant) -> None:
    hass.states.async_set("binary_sensor.front_door", "on", {})
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).attributes[ATTR_ARM_FAILURE] is not None

    hass.states.async_set("binary_sensor.front_door", "off", {})
    await hass.async_block_till_done()
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_AWAY
    assert state.attributes[ATTR_ARM_FAILURE] is None


@pytest.mark.asyncio
async def test_delayed_arm_success_clears_failure_from_later_attempt(
    hass: HomeAssistant,
) -> None:
    entity_id = await _setup_panel(hass, exit_delay=0.02)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMING

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "0000"},
        blocking=True,
    )
    assert hass.states.get(entity_id).attributes[ATTR_ARM_FAILURE] is not None

    await asyncio.sleep(0.03)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ALARM_ARMED_AWAY
    assert state.attributes[ATTR_ARM_FAILURE] is None
