"""Behavior tests for the PAC compressor-slot script blueprint."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from tests.fixtures.blueprint_inputs import (
    INPUT_DATETIME_PAC_LAST_CHANGE,
    SCRIPT_INPUTS,
)
from tests.helpers.blueprint_loader import async_load_script_blueprint
from tests.helpers.entities import seed_entities

SLOT_CLIMATES = (
    "climate.slot_a",
    "climate.slot_b",
    "climate.slot_c",
    "climate.slot_d",
)


def _eid(call: ServiceCall) -> str:
    entity_id = call.data.get("entity_id")
    if isinstance(entity_id, list):
        return entity_id[0]
    return str(entity_id)


def _climate_attrs(temperature: Any = 21) -> dict[str, Any]:
    return {
        "hvac_modes": ["off", "heat", "cool"],
        "min_temp": 7,
        "max_temp": 35,
        "temperature": temperature,
    }


def register_hvac_io(
    hass: HomeAssistant,
) -> tuple[list[ServiceCall], list[ServiceCall], list[ServiceCall]]:
    """Register climate and datetime services that apply state (needed for cap counts)."""
    set_calls: list[ServiceCall] = []
    off_calls: list[ServiceCall] = []
    dt_calls: list[ServiceCall] = []

    async def set_temp(call: ServiceCall) -> None:
        set_calls.append(call)
        hass.states.async_set(
            _eid(call),
            call.data.get("hvac_mode", "heat"),
            _climate_attrs(call.data.get("temperature")),
        )

    async def turn_off(call: ServiceCall) -> None:
        off_calls.append(call)
        hass.states.async_set(_eid(call), "off", _climate_attrs())

    async def set_datetime(call: ServiceCall) -> None:
        dt_calls.append(call)
        ts = float(call.data.get("timestamp") or 0)
        when = dt_util.utc_from_timestamp(ts) if ts else dt_util.utcnow()
        hass.states.async_set(
            _eid(call),
            when.strftime("%Y-%m-%d %H:%M:%S"),
            {"has_date": True, "has_time": True, "timestamp": ts or when.timestamp()},
        )

    hass.services.async_register("climate", "set_temperature", set_temp)
    hass.services.async_register("climate", "turn_off", turn_off)
    hass.services.async_register("input_datetime", "set_datetime", set_datetime)
    return set_calls, off_calls, dt_calls


def _seed_slots(
    hass: HomeAssistant,
    *,
    states: dict[str, str] | None = None,
) -> None:
    entities: dict[str, tuple[str, dict[str, Any] | None]] = {
        INPUT_DATETIME_PAC_LAST_CHANGE: (
            "2020-01-01 00:00:00",
            {"has_date": True, "has_time": True, "timestamp": 0},
        )
    }
    for climate_id in SLOT_CLIMATES:
        entities[climate_id] = (states.get(climate_id, "off") if states else "off", _climate_attrs())
    seed_entities(hass, entities)


async def _load_slot(hass: HomeAssistant, **overrides: Any) -> str:
    inputs = {
        **SCRIPT_INPUTS["pac-compressor-slot.yaml"],
        "sibling_climates": list(SLOT_CLIMATES),
        **overrides,
    }
    return await async_load_script_blueprint(
        hass,
        "pac-compressor-slot.yaml",
        inputs,
        script_id="pac_compressor_slot",
    )


async def _request(
    hass: HomeAssistant,
    climate_id: str,
    request: str = "start",
    *,
    frost: bool = False,
    blocking: bool = True,
) -> None:
    await hass.services.async_call(
        "script",
        "pac_compressor_slot",
        {
            "climate_id": climate_id,
            "request": request,
            "hvac_mode": "heat",
            "temperature": 21,
            "frost": frost,
        },
        blocking=blocking,
    )


@pytest.mark.behavior
async def test_four_starts_grant_at_most_max_concurrent(
    hass_with_entities: HomeAssistant,
) -> None:
    """Queued overlapping starts must not all see an empty PAC."""
    hass = hass_with_entities
    _seed_slots(hass)
    set_calls, _, _ = register_hvac_io(hass)
    await _load_slot(hass, start_stagger_seconds=0, global_change_interval=0, max_concurrent=2)

    await asyncio.gather(*[_request(hass, climate_id) for climate_id in SLOT_CLIMATES])
    await hass.async_block_till_done()

    granted = {_eid(call) for call in set_calls}
    assert len(set_calls) == 2
    assert granted <= set(SLOT_CLIMATES)
    running = [c for c in SLOT_CLIMATES if hass.states.get(c).state in ("heat", "cool")]
    assert len(running) == 2


@pytest.mark.behavior
async def test_stagger_delays_second_granted_start(
    hass_with_entities: HomeAssistant,
) -> None:
    """Second start waits at least start_stagger_seconds after the first grant."""
    hass = hass_with_entities
    _seed_slots(hass)
    set_calls, _, dt_calls = register_hvac_io(hass)
    await _load_slot(hass, start_stagger_seconds=5, global_change_interval=0, max_concurrent=2)

    await _request(hass, SLOT_CLIMATES[0])
    first_ts = float(hass.states.get(INPUT_DATETIME_PAC_LAST_CHANGE).attributes["timestamp"])
    assert dt_calls, "granted start must stamp the last-change helper"
    assert first_ts > 0
    assert len(set_calls) == 1

    second = asyncio.create_task(_request(hass, SLOT_CLIMATES[1]))
    await hass.async_block_till_done()
    assert len(set_calls) == 1, "second start must wait on stagger before climate write"

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()
    await asyncio.wait_for(second, timeout=5)

    assert len(set_calls) == 2
    assert _eid(set_calls[1]) == SLOT_CLIMATES[1]


@pytest.mark.behavior
async def test_stop_waits_global_change_interval(
    hass_with_entities: HomeAssistant,
) -> None:
    """A stop after a start waits on the global interval before turn_off."""
    hass = hass_with_entities
    _seed_slots(hass)
    set_calls, off_calls, _ = register_hvac_io(hass)
    await _load_slot(hass, start_stagger_seconds=0, global_change_interval=5, max_concurrent=2)

    await _request(hass, SLOT_CLIMATES[0])
    assert len(set_calls) == 1

    stopping = asyncio.create_task(_request(hass, SLOT_CLIMATES[0], "stop"))
    await hass.async_block_till_done()
    assert len(off_calls) == 0

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()
    await asyncio.wait_for(stopping, timeout=5)

    assert len(off_calls) == 1
    assert _eid(off_calls[0]) == SLOT_CLIMATES[0]


@pytest.mark.behavior
async def test_already_on_setpoint_refresh_does_not_count_as_start(
    hass_with_entities: HomeAssistant,
) -> None:
    """Start A, reset helper, start A again (already_on): B must not wait on that refresh."""
    hass = hass_with_entities
    _seed_slots(hass)
    set_calls, _, dt_calls = register_hvac_io(hass)
    await _load_slot(hass, start_stagger_seconds=5, global_change_interval=5, max_concurrent=2)

    await _request(hass, SLOT_CLIMATES[0])
    assert len(set_calls) == 1
    assert len(dt_calls) == 1
    assert hass.states.get(SLOT_CLIMATES[0]).state == "heat"

    hass.states.async_set(
        INPUT_DATETIME_PAC_LAST_CHANGE,
        "2020-01-01 00:00:00",
        {"has_date": True, "has_time": True, "timestamp": 0},
    )
    dt_before = len(dt_calls)

    refresh = asyncio.create_task(_request(hass, SLOT_CLIMATES[0]))
    await hass.async_block_till_done()
    await asyncio.wait_for(refresh, timeout=5)

    assert len(set_calls) == 2, "already_on start still applies the setpoint"
    assert len(dt_calls) == dt_before, "already_on start must not stamp last_change"

    second = asyncio.create_task(_request(hass, SLOT_CLIMATES[1]))
    await hass.async_block_till_done()
    await asyncio.wait_for(second, timeout=5)

    assert len(set_calls) == 3
    assert _eid(set_calls[2]) == SLOT_CLIMATES[1]


@pytest.mark.behavior
async def test_frost_start_granted_at_cap(
    hass_with_entities: HomeAssistant,
) -> None:
    """Frost may start even when max_concurrent indoor units are already running."""
    hass = hass_with_entities
    _seed_slots(hass, states={SLOT_CLIMATES[0]: "heat", SLOT_CLIMATES[1]: "heat"})
    set_calls, _, _ = register_hvac_io(hass)
    await _load_slot(hass, start_stagger_seconds=0, global_change_interval=0, max_concurrent=2)

    await _request(hass, SLOT_CLIMATES[2], frost=True)
    await hass.async_block_till_done()

    assert len(set_calls) == 1
    assert _eid(set_calls[0]) == SLOT_CLIMATES[2]
    assert hass.states.get(SLOT_CLIMATES[2]).state == "heat"


@pytest.mark.behavior
async def test_helper_unset_skips_cap(
    hass_with_entities: HomeAssistant,
) -> None:
    """Without the last-change helper, compressor rules are skipped and starts grant."""
    hass = hass_with_entities
    _seed_slots(hass)
    set_calls, _, _ = register_hvac_io(hass)
    await _load_slot(
        hass,
        last_change_helper="",
        start_stagger_seconds=0,
        global_change_interval=0,
        max_concurrent=2,
    )

    await asyncio.gather(*[_request(hass, climate_id) for climate_id in SLOT_CLIMATES])
    await hass.async_block_till_done()

    assert len(set_calls) == 4
