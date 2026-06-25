"""Behavior tests for the cover_solar_thermal_optimization blueprint (v2)."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from tests.helpers.blueprint_loader import async_load_automation_blueprint
from tests.helpers.entities import seed_entities

FILENAME = "cover_solar_thermal_optimization.yaml"
BAY = "cover.bay_window"
DOOR = "cover.french_door"
BAY_CONTACT = "binary_sensor.bay_window_contact"
PERSON = "person.test"


@pytest.fixture
def expected_lingering_timers() -> bool:
    """The blueprint registers a 10-minute time_pattern listener."""
    return True


def _requested_positions(calls: list[Any]) -> dict[str, Any]:
    """Map each targeted cover to the position requested by set_cover_position."""
    positions: dict[str, Any] = {}
    for call in calls:
        entity = call.data.get("entity_id")
        targets = entity if isinstance(entity, list) else [entity]
        for target in targets:
            positions[target] = call.data.get("position")
    return positions


@pytest.mark.behavior
async def test_contact_open_moves_only_linked_cover(hass: HomeAssistant) -> None:
    """Opening a sensor repositions only the cover linked to it."""
    # Daylight + home + summer cool: the ambient target equals the current
    # position (neutral 100), so both covers are no-ops until a contact opens.
    seed_entities(
        hass,
        {
            "sun.sun": ("above_horizon", {"azimuth": 180.0, "elevation": 45}),
            PERSON: ("home", {}),
            BAY: ("open", {"current_position": 100}),
            DOOR: ("open", {"current_position": 100}),
            BAY_CONTACT: ("off", {}),
        },
    )
    await hass.async_block_till_done()

    set_position = async_mock_service(hass, "cover", "set_cover_position")

    await async_load_automation_blueprint(
        hass,
        FILENAME,
        {
            "covers": [BAY, DOOR],
            "presence_persons": [PERSON],
            "season_mode": "summer",
            "neutral_position": "100",
            "contact_open_position": "50",
            "cover_contact_links": [
                {"cover": BAY, "sensors": [BAY_CONTACT]},
            ],
        },
    )

    seed_entities(hass, {BAY_CONTACT: ("on", {})})
    await hass.async_block_till_done()

    positions = _requested_positions(set_position)
    assert positions.get(BAY) == 50
    assert DOOR not in positions


@pytest.mark.behavior
async def test_away_closes_all_covers(hass: HomeAssistant) -> None:
    """When nobody is home, every managed cover is closed."""
    seed_entities(
        hass,
        {
            "sun.sun": ("above_horizon", {"azimuth": 180.0, "elevation": 45}),
            PERSON: ("home", {}),
            BAY: ("open", {"current_position": 100}),
            DOOR: ("open", {"current_position": 100}),
        },
    )
    await hass.async_block_till_done()

    set_position = async_mock_service(hass, "cover", "set_cover_position")

    await async_load_automation_blueprint(
        hass,
        FILENAME,
        {
            "covers": [BAY, DOOR],
            "presence_persons": [PERSON],
            "close_when_away": True,
        },
    )

    seed_entities(hass, {PERSON: ("not_home", {})})
    await hass.async_block_till_done()

    positions = _requested_positions(set_position)
    assert positions.get(BAY) == 0
    assert positions.get(DOOR) == 0
