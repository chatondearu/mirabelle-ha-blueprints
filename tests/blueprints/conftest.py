"""Blueprint test fixtures."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from tests.helpers.entities import seed_entities
from tests.fixtures.blueprint_inputs import (
    AUTOMATION_INPUTS,
    SCRIPT_INPUTS,
    frient_keypad_inputs,
)
from tests.helpers.blueprint_loader import (
    async_load_automation_blueprint,
    async_load_script_blueprint,
)


@pytest.fixture
def common_entities() -> dict[str, tuple[str, dict[str, Any] | None]]:
    """Default entity states for blueprint smoke tests."""
    return {
        "media_player.test": ("idle", {"volume_level": 0.5, "supported_features": 0}),
        "light.test": ("off", {}),
        "binary_sensor.test_motion": ("off", {}),
        "switch.test_cover": ("off", {}),
        "input_text.test_cover_position": ("50", {}),
        "input_text.test_cover_direction": ("idle", {}),
        "cover.test": ("closed", {"current_position": 0}),
        "person.test": ("home", {}),
        "alarm_control_panel.test": ("disarmed", {}),
        "alarm_control_panel.test_mirror": ("disarmed", {}),
        "input_datetime.test_schedule": ("2025-01-01", {}),
        "sun.sun": ("above_horizon", {"elevation": 45}),
        "climate.test_split": (
            "off",
            {
                "hvac_modes": ["off", "heat", "cool"],
                "min_temp": 7,
                "max_temp": 35,
                "current_temperature": 20,
            },
        ),
        "sensor.test_room_temperature": ("20", {}),
        "input_number.test_comfort": ("20", {}),
        "input_number.test_eco": ("18", {}),
        "input_select.test_season_mode": (
            "auto",
            {"options": ["off", "heat", "cool", "auto"]},
        ),
        "input_select.test_hvac_active": (
            "heat",
            {"options": ["off", "heat", "cool"]},
        ),
    }


@pytest.fixture
async def hass_with_entities(hass: HomeAssistant, common_entities):  # noqa: ANN001
    """Home Assistant with seeded test entities."""
    seed_entities(hass, common_entities)
    await hass.async_block_till_done()
    return hass


async def setup_frient_device(hass: HomeAssistant) -> str:
    """Register a mock ZHA device for the Frient keypad blueprint."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    config_entry = MockConfigEntry(domain="zha", title="ZHA", data={})
    config_entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("zha", "test_frient_keypad")},
    )
    return device.id


async def smoke_load_automation(hass: HomeAssistant, filename: str) -> str:
    """Load automation blueprint with default test inputs."""
    inputs = AUTOMATION_INPUTS[filename]
    return await async_load_automation_blueprint(hass, filename, inputs)


async def smoke_load_script(hass: HomeAssistant, filename: str) -> str:
    """Load script blueprint with default test inputs."""
    inputs = SCRIPT_INPUTS[filename]
    return await async_load_script_blueprint(hass, filename, inputs)
