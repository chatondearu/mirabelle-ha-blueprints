"""Behavior tests for create_schedule script blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.blueprints.conftest import smoke_load_script


@pytest.mark.behavior
async def test_create_schedule_sets_datetime(hass_with_entities: HomeAssistant) -> None:
    """Script should call input_datetime.set_datetime for the schedule helper."""
    hass = hass_with_entities
    set_datetime = async_mock_service(hass, "input_datetime", "set_datetime")

    entity_id = await smoke_load_script(hass, "create_schedule.yaml")

    await hass.services.async_call(
        "script",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(set_datetime) >= 1
