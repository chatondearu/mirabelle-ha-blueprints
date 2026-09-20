"""CDA Alarm integration setup."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .keypad import async_setup_keypad_listener

PLATFORMS = [Platform.ALARM_CONTROL_PANEL]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CDA Alarm from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        **entry.data,
        **entry.options,
    }
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    panel_entity_id = er.async_get(hass).async_get_entity_id(
        ALARM_DOMAIN,
        DOMAIN,
        entry.entry_id,
    )
    if panel_entity_id is not None:
        entry.async_on_unload(
            async_setup_keypad_listener(hass, entry, panel_entity_id)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a CDA Alarm config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload CDA Alarm when config entry options change."""
    await hass.config_entries.async_reload(entry.entry_id)
