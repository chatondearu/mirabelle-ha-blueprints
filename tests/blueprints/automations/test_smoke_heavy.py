"""Smoke tests for blueprints that register recurring time listeners."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from tests.blueprints.conftest import smoke_load_automation

HEAVY_AUTOMATIONS = (
    "cover_solar_thermal_optimization.yaml",
    "living-area-adaptive-lighting.yaml",
)


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Allow pattern time listeners registered by large automations."""
    return True


@pytest.mark.smoke
@pytest.mark.parametrize("filename", HEAVY_AUTOMATIONS)
async def test_heavy_automation_blueprint_loads(
    hass_with_entities: HomeAssistant,
    filename: str,
) -> None:
    """Large automations should load (may leave expected time listeners)."""
    entity_id = await smoke_load_automation(hass_with_entities, filename)
    assert hass_with_entities.states.get(entity_id) is not None
