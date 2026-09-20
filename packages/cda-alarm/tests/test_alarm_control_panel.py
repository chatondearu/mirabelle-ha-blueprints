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
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import DOMAIN


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
