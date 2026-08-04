"""Behavior tests for reversible_split_thermostat automation blueprint."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.fixtures.blueprint_inputs import (
    AUTOMATION_INPUTS,
    CLIMATE,
    INPUT_NUMBER_COMFORT,
    INPUT_NUMBER_ECO,
    INPUT_SELECT_HVAC,
    ROOM_TEMPERATURE,
)
from tests.helpers.blueprint_loader import async_load_automation_blueprint
from tests.helpers.entities import seed_entities


async def _load_split(
    hass: HomeAssistant,
    *,
    extra_entities: dict[str, tuple[str, dict[str, Any] | None]] | None = None,
    input_overrides: dict[str, Any] | None = None,
) -> str:
    """Load the split thermostat blueprint with optional overrides."""
    if extra_entities:
        seed_entities(hass, extra_entities)
    inputs = {
        **AUTOMATION_INPUTS["reversible-split-thermostat.yaml"],
        **(input_overrides or {}),
    }
    return await async_load_automation_blueprint(
        hass,
        "reversible-split-thermostat.yaml",
        inputs,
        automation_id="test_reversible_split",
    )


@pytest.mark.behavior
async def test_approach_max_delta_caps_cool_drive_when_room_is_far(
    hass_with_entities: HomeAssistant,
) -> None:
    """Far from target in cool, setpoint stays within delta of room but not below target."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("cool", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("24", {}),
            INPUT_NUMBER_ECO: ("24.5", {}),
            ROOM_TEMPERATURE: ("27", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "boost_offset": 1,
            "approach_max_delta": 2,
            "adaptive_boost": False,
        },
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_calls) == 1
    assert climate_calls[0].data["hvac_mode"] == "cool"
    # raw drive 23, capped to max(23, 25)=25 then min(25, target 24)=24
    assert climate_calls[0].data["temperature"] == 24


@pytest.mark.behavior
async def test_approach_max_delta_disabled_uses_full_boost(
    hass_with_entities: HomeAssistant,
) -> None:
    """With approach_max_delta 0, boost is not capped by room temperature."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("cool", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("24", {}),
            ROOM_TEMPERATURE: ("27", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "boost_offset": 1,
            "approach_max_delta": 0,
            "adaptive_boost": False,
        },
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_calls) == 1
    assert climate_calls[0].data["temperature"] == 23


@pytest.mark.behavior
async def test_approach_max_delta_floors_heat_drive_at_target(
    hass_with_entities: HomeAssistant,
) -> None:
    """In heat, cap cannot drive below the logical target."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("heat", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("19", {}),
            INPUT_NUMBER_ECO: ("17", {}),
            ROOM_TEMPERATURE: ("15", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "boost_offset": 2,
            "approach_max_delta": 2,
            "adaptive_boost": False,
        },
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_calls) == 1
    assert climate_calls[0].data["hvac_mode"] == "heat"
    # raw drive 21, capped to min(21, 17)=17 then max(17, target 19)=19
    assert climate_calls[0].data["temperature"] == 19


@pytest.mark.behavior
async def test_approach_max_delta_allows_boost_when_room_is_near_target(
    hass_with_entities: HomeAssistant,
) -> None:
    """When room is within delta of target, boost applies unchanged."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("cool", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("24", {}),
            ROOM_TEMPERATURE: ("24.5", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "boost_offset": 1,
            "approach_max_delta": 2,
            "adaptive_boost": False,
        },
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_calls) == 1
    assert climate_calls[0].data["temperature"] == 23


@pytest.mark.behavior
async def test_cool_idles_when_room_at_or_below_target(
    hass_with_entities: HomeAssistant,
) -> None:
    """With room sensor control, cool mode turns off once the room reached target."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("cool", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("26", {}),
            INPUT_NUMBER_ECO: ("28", {}),
            ROOM_TEMPERATURE: ("26.0", {}),
            CLIMATE: (
                "cool",
                {
                    "hvac_modes": ["off", "heat", "cool"],
                    "min_temp": 16,
                    "max_temp": 30,
                    "temperature": 20,
                },
            ),
        },
    )
    climate_set = async_mock_service(hass, "climate", "set_temperature")
    climate_off = async_mock_service(hass, "climate", "turn_off")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "boost_offset": 1,
            "approach_max_delta": 1,
            "adaptive_boost": True,
            "room_sensor_control": True,
        },
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_set) == 0
    assert len(climate_off) == 1


@pytest.mark.behavior
async def test_cool_drives_when_room_above_target_plus_hysteresis(
    hass_with_entities: HomeAssistant,
) -> None:
    """Cool mode must keep driving when the room is clearly above target."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("cool", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("26", {}),
            ROOM_TEMPERATURE: ("26.8", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 16, "max_temp": 30}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "boost_offset": 1,
            "approach_max_delta": 1,
            "adaptive_boost": False,
            "cut_hysteresis": 0.3,
            "room_sensor_control": True,
        },
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_calls) == 1
    assert climate_calls[0].data["hvac_mode"] == "cool"
    # raw drive 25, approach max(25, 25.8)=25.8, min with target 26 → 25.8
    assert climate_calls[0].data["temperature"] == 25.8
