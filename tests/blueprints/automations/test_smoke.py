"""Smoke tests: all automation blueprints load via use_blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from tests.blueprints.conftest import (
    setup_frient_device,
    smoke_load_automation,
)
from tests.fixtures.blueprint_inputs import (
    AUTOMATION_INPUTS,
    AUTOMATION_INPUTS_HEAVY,
    frient_keypad_inputs,
)
from tests.helpers.blueprint_loader import async_load_automation_blueprint


# cover_solar_thermal_optimization and living-area-adaptive-lighting are in test_smoke_heavy.py
SMOKE_AUTOMATIONS = sorted(
    k for k in AUTOMATION_INPUTS.keys() if k not in AUTOMATION_INPUTS_HEAVY
)


@pytest.mark.smoke
@pytest.mark.parametrize("filename", SMOKE_AUTOMATIONS)
async def test_automation_blueprint_loads(
    hass_with_entities: HomeAssistant,
    filename: str,
) -> None:
    """Each CDA automation blueprint must load without error."""
    entity_id = await smoke_load_automation(hass_with_entities, filename)
    assert hass_with_entities.states.get(entity_id) is not None


@pytest.mark.smoke
async def test_frient_keypad_blueprint_loads(hass_with_entities: HomeAssistant) -> None:
    """Third-party Frient keypad blueprint loads with a mock ZHA device."""
    device_id = await setup_frient_device(hass_with_entities)
    inputs = frient_keypad_inputs(device_id)
    entity_id = await async_load_automation_blueprint(
        hass_with_entities,
        "frient_keypad_with_alarmo.yaml",
        inputs,
        automation_id="frient_test",
    )
    assert hass_with_entities.states.get(entity_id) is not None
