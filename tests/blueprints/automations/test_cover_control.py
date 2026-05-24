"""Behavior tests for cover_control automation blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.blueprints.conftest import smoke_load_automation
from tests.fixtures.blueprint_inputs import SWITCH


@pytest.mark.behavior
async def test_cover_control_triggers_script(hass_with_entities: HomeAssistant) -> None:
    """Manual trigger should call the set_cover_position script service."""
    hass = hass_with_entities
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(
        hass,
        "script",
        {
            "script": [
                {
                    "alias": "set_cover_position",
                    "sequence": [
                        {
                            "service": "switch.turn_off",
                            "target": {"entity_id": SWITCH},
                        }
                    ],
                }
            ]
        },
    )
    await hass.async_block_till_done()
    script_calls = async_mock_service(hass, "script", "set_cover_position")

    automation_entity = await smoke_load_automation(hass, "cover_control.yaml")

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": automation_entity, "skip_condition": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(script_calls) >= 1
