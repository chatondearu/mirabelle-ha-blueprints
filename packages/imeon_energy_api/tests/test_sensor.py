"""Smoke tests for Imeon Energy API sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.imeon_energy_api.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_creates_sensor_entities(hass: HomeAssistant) -> None:
    """Setting up the integration should register sensor entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.10",
            "username": "installer@local",
            "password": "secret",
            "scan_interval": 30,
        },
        title="Imeon Energy (192.168.1.10)",
    )
    entry.add_to_hass(hass)

    mock_coordinator = MagicMock()
    mock_coordinator.host = "192.168.1.10"
    mock_coordinator.meta = {"serial": "TEST123", "model": "Test", "sw_version": "1.0"}
    mock_coordinator.data = {"Power": 1000}
    mock_coordinator.async_config_entry_first_refresh = AsyncMock(return_value=None)
    mock_coordinator.async_add_listener = MagicMock(return_value=lambda: None)

    with patch(
        "custom_components.imeon_energy_api.ImeonEnergyCoordinator",
        return_value=mock_coordinator,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) > 0
