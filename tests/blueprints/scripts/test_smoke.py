"""Smoke tests: all script blueprints load via use_blueprint."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from tests.blueprints.conftest import smoke_load_script
from tests.fixtures.blueprint_inputs import SCRIPT_INPUTS


@pytest.mark.smoke
@pytest.mark.parametrize("filename", sorted(SCRIPT_INPUTS.keys()))
async def test_script_blueprint_loads(
    hass_with_entities: HomeAssistant,
    filename: str,
) -> None:
    """Each CDA script blueprint must load without error."""
    entity_id = await smoke_load_script(hass_with_entities, filename)
    assert hass_with_entities.states.get(entity_id) is not None
