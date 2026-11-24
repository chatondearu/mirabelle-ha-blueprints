"""Behavior tests for reversible_split_thermostat automation blueprint."""

from __future__ import annotations

import re
from pathlib import Path
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
    OCCUPANCY,
    OCCUPANCY_GATE,
    ROOM_TEMPERATURE,
    SCRIPT_INPUTS,
)
from tests.helpers.blueprint_loader import (
    BLUEPRINTS_ROOT,
    async_load_automation_blueprint,
    async_load_script_blueprint,
)
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


def test_thermostat_default_min_run_time_and_cut_hysteresis() -> None:
    """Blueprint defaults protect the PAC: 600 s min run, 0.5 °C cut hysteresis."""
    text = (BLUEPRINTS_ROOT / "automations" / "reversible-split-thermostat.yaml").read_text(
        encoding="utf-8"
    )
    min_run = text[text.index("min_run_time:") : text.index("adaptive_boost:")]
    cut = text[text.index("cut_hysteresis:") : text.index("frost_protection_temp:")]
    assert re.search(r"default:\s*600\b", min_run)
    assert re.search(r"default:\s*0\.5\b", cut)


@pytest.mark.behavior
async def test_occupancy_off_idles_without_start(
    hass_with_entities: HomeAssistant,
) -> None:
    """Unoccupied room with the occupancy gate on must idle off, not request heat."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("heat", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("19", {}),
            ROOM_TEMPERATURE: ("15", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
            OCCUPANCY: ("off", {}),
            OCCUPANCY_GATE: ("on", {}),
        },
    )
    climate_set = async_mock_service(hass, "climate", "set_temperature")
    climate_off = async_mock_service(hass, "climate", "turn_off")

    automation_entity = await _load_split(
        hass,
        input_overrides={
            "occupancy_entity": OCCUPANCY,
            "occupancy_gate_helper": OCCUPANCY_GATE,
            "room_sensor_control": True,
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

    assert len(climate_set) == 0
    assert len(climate_off) == 1


@pytest.mark.behavior
async def test_window_open_bypasses_compressor_slot(
    hass_with_entities: HomeAssistant,
) -> None:
    """Open window must turn_off immediately, not wait on the compressor interval."""
    hass = hass_with_entities
    window = "binary_sensor.test_split_window"
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("heat", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("19", {}),
            ROOM_TEMPERATURE: ("15", {}),
            CLIMATE: (
                "heat",
                {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35},
            ),
            window: ("on", {}),
        },
    )
    climate_set = async_mock_service(hass, "climate", "set_temperature")
    climate_off = async_mock_service(hass, "climate", "turn_off")

    script_entity = await async_load_script_blueprint(
        hass,
        "pac-compressor-slot.yaml",
        {
            **SCRIPT_INPUTS["pac-compressor-slot.yaml"],
            "sibling_climates": [CLIMATE],
            "start_stagger_seconds": 0,
            "global_change_interval": 0,
        },
        script_id="pac_compressor_slot",
    )
    automation_entity = await _load_split(
        hass,
        input_overrides={
            "compressor_slot_script": script_entity,
            "windows": [window],
            "frost_protection_temp": 0,
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
async def test_season_off_bypasses_compressor_slot(
    hass_with_entities: HomeAssistant,
) -> None:
    """Global resolved mode off still turn_off directly, skipping the slot interval."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("off", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("19", {}),
            ROOM_TEMPERATURE: ("15", {}),
            CLIMATE: (
                "heat",
                {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35},
            ),
        },
    )
    climate_off = async_mock_service(hass, "climate", "turn_off")

    script_entity = await async_load_script_blueprint(
        hass,
        "pac-compressor-slot.yaml",
        {
            **SCRIPT_INPUTS["pac-compressor-slot.yaml"],
            "sibling_climates": [CLIMATE],
        },
        script_id="pac_compressor_slot",
    )
    automation_entity = await _load_split(
        hass,
        input_overrides={"compressor_slot_script": script_entity},
    )

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(climate_off) == 1


@pytest.mark.behavior
async def test_compressor_slot_used_for_conditioning_start(
    hass_with_entities: HomeAssistant,
) -> None:
    """When the slot script is set, conditioning starts go through it, not direct climate."""
    hass = hass_with_entities
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("heat", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("19", {}),
            ROOM_TEMPERATURE: ("15", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")
    datetime_calls = async_mock_service(hass, "input_datetime", "set_datetime")

    script_entity = await async_load_script_blueprint(
        hass,
        "pac-compressor-slot.yaml",
        {
            **SCRIPT_INPUTS["pac-compressor-slot.yaml"],
            "sibling_climates": [CLIMATE],
            "start_stagger_seconds": 0,
            "global_change_interval": 0,
        },
        script_id="pac_compressor_slot",
    )
    automation_entity = await _load_split(
        hass,
        input_overrides={
            "compressor_slot_script": script_entity,
            "boost_offset": 0,
            "adaptive_boost": False,
            "approach_max_delta": 0,
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
    assert len(datetime_calls) == 1


@pytest.mark.behavior
async def test_occupied_room_at_cap_does_not_start(
    hass_with_entities: HomeAssistant,
) -> None:
    """An occupied room still waits when the PAC is already at max_concurrent."""
    hass = hass_with_entities
    busy_a = "climate.slot_busy_a"
    busy_b = "climate.slot_busy_b"
    seed_entities(
        hass,
        {
            INPUT_SELECT_HVAC: ("heat", {"options": ["off", "heat", "cool"]}),
            INPUT_NUMBER_COMFORT: ("19", {}),
            ROOM_TEMPERATURE: ("15", {}),
            CLIMATE: ("off", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
            busy_a: ("heat", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
            busy_b: ("heat", {"hvac_modes": ["off", "heat", "cool"], "min_temp": 7, "max_temp": 35}),
            OCCUPANCY: ("on", {}),
            OCCUPANCY_GATE: ("on", {}),
        },
    )
    climate_calls = async_mock_service(hass, "climate", "set_temperature")

    script_entity = await async_load_script_blueprint(
        hass,
        "pac-compressor-slot.yaml",
        {
            **SCRIPT_INPUTS["pac-compressor-slot.yaml"],
            "sibling_climates": [CLIMATE, busy_a, busy_b],
            "max_concurrent": 2,
            "start_stagger_seconds": 0,
            "global_change_interval": 0,
        },
        script_id="pac_compressor_slot",
    )
    automation_entity = await _load_split(
        hass,
        input_overrides={
            "compressor_slot_script": script_entity,
            "occupancy_entity": OCCUPANCY,
            "occupancy_gate_helper": OCCUPANCY_GATE,
            "boost_offset": 0,
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

    assert len(climate_calls) == 0
