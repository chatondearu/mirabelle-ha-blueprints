"""CDA Alarm integration setup."""

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DATA_RESPONSE_RUNNER, DATA_WS_REGISTERED, DOMAIN
from .keypad import async_setup_keypad_listener
from .panel import async_setup_panel
from .response import CdaAlarmResponseRunner
from .sensors import merge_runtime_config
from .websocket_api import async_register_websockets

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.ALARM_CONTROL_PANEL]


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the CDA Alarm integration (panel + websocket)."""
    await _async_setup_shared(hass)
    return True


async def _async_setup_shared(hass: HomeAssistant) -> None:
    """Register websocket commands and the sidebar panel once."""
    hass.data.setdefault(DOMAIN, {})
    if not hass.data[DOMAIN].get(DATA_WS_REGISTERED):
        async_register_websockets(hass)
        hass.data[DOMAIN][DATA_WS_REGISTERED] = True
    try:
        await async_setup_panel(hass)
    except Exception:
        # Panel registration needs http/frontend; skip gracefully in unit tests.
        _LOGGER.debug("CDA Alarm panel registration skipped", exc_info=True)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CDA Alarm from a config entry."""
    await _async_setup_shared(hass)

    config = merge_runtime_config({**entry.data, **entry.options})
    runner = CdaAlarmResponseRunner(hass, entry.entry_id)
    runner.update_config(config)
    hass.data[DOMAIN][entry.entry_id] = {
        "config": config,
        DATA_RESPONSE_RUNNER: runner,
        # Flat keys for keypad/legacy readers that expect option fields.
        **config,
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
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if isinstance(stored, dict):
        runner = stored.get(DATA_RESPONSE_RUNNER)
        if isinstance(runner, CdaAlarmResponseRunner):
            await runner.async_stop()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload CDA Alarm when config entry options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def get_response_runner(
    hass: HomeAssistant, entry_id: str
) -> CdaAlarmResponseRunner | None:
    """Return the response runner for an entry when present."""
    stored = hass.data.get(DOMAIN, {}).get(entry_id)
    if not isinstance(stored, dict):
        return None
    runner = stored.get(DATA_RESPONSE_RUNNER)
    return runner if isinstance(runner, CdaAlarmResponseRunner) else None
