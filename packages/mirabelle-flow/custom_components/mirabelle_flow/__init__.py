"""Mirabelle Flow — visual automation editor for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .panel import async_register_panel, async_unregister_panel
from .websocket_api import async_register_websocket_handlers

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Mirabelle Flow (YAML)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mirabelle Flow from config entry."""
    async_register_websocket_handlers(hass)
    await async_register_panel(hass)
    _LOGGER.info("Mirabelle Flow integration ready")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Mirabelle Flow."""
    async_unregister_panel(hass)
    return True
