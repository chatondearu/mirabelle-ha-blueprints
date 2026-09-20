"""Tests for CDA Alarm integration setup."""

from __future__ import annotations

import pytest
from homeassistant.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
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
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id in hass.data[DOMAIN]
    assert hass.states.get(f"{ALARM_DOMAIN}.cda_alarm") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data[DOMAIN]
