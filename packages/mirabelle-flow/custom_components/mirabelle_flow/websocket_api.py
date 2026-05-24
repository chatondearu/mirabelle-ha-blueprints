"""WebSocket API for Mirabelle Flow layout persistence."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import storage

from .const import DOMAIN, STORAGE_KEY

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websocket_handlers(hass: HomeAssistant) -> None:
    """Register custom websocket commands."""
    websocket_api.async_register_command(hass, ws_layout_get)
    websocket_api.async_register_command(hass, ws_layout_save)


async def _get_store(hass: HomeAssistant) -> storage.Store[dict[str, Any]]:
    """Return layout storage."""
    return storage.Store(hass, 1, STORAGE_KEY)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "mirabelle_flow/layout/get",
        vol.Required("key"): str,
    }
)
@websocket_api.async_response
async def ws_layout_get(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return saved node layout for a document key."""
    store = await _get_store(hass)
    data = await store.async_load() or {}
    key = msg["key"]
    entry = data.get(key, {})
    connection.send_result(msg["id"], {"layout": entry.get("layout", {})})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "mirabelle_flow/layout/save",
        vol.Required("key"): str,
        vol.Required("layout"): dict,
    }
)
@websocket_api.async_response
async def ws_layout_save(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist node layout for a document key."""
    store = await _get_store(hass)
    data = await store.async_load() or {}
    key = msg["key"]
    data[key] = {"layout": msg["layout"]}
    await store.async_save(data)
    connection.send_result(msg["id"], {"success": True})
