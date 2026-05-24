"""Tests for Imeon Energy API config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.imeon_energy_api.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Valid credentials should create a config entry."""
    with (
        patch(
            "custom_components.imeon_energy_api.config_flow.validate_input",
            new=AsyncMock(return_value={"title": "Imeon Energy (192.168.1.10)"}),
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_setup",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] == FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_USERNAME: "installer@local",
                CONF_PASSWORD: "secret",
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Imeon Energy (192.168.1.10)"


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass: HomeAssistant) -> None:
    """Connection failure should surface cannot_connect error."""
    from custom_components.imeon_energy_api.config_flow import CannotConnect

    with patch(
        "custom_components.imeon_energy_api.config_flow.validate_input",
        new=AsyncMock(side_effect=CannotConnect()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.10",
                CONF_USERNAME: "installer@local",
                CONF_PASSWORD: "bad",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"
