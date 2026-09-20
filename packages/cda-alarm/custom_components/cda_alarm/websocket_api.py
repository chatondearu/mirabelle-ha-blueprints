"""Websocket API for the CDA Alarm sidebar panel."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)

from .access import normalize_access, user_can_use_dashboard
from .cameras import normalize_cameras, normalize_sensor_camera_map
from .const import (
    CDA_BLUEPRINT_MARKERS,
    CONF_ACCESS,
    CONF_ACCESS_MODE,
    CONF_BLOCK_ARM_IF_OPEN,
    CONF_CAMERAS,
    CONF_CODES,
    CONF_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_KEYPADS,
    CONF_NAME,
    CONF_RESPONSE,
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSOR_CAMERA_MAP,
    DEFAULT_BLOCK_ARM_IF_OPEN,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DOMAIN,
    WS_TYPE_GET_CONFIG,
    WS_TYPE_GET_DASHBOARD,
    WS_TYPE_LIST_LINKED,
    WS_TYPE_UPDATE_CONFIG,
)
from .dashboard import build_dashboard
from .keypad import discover_default_keypad_device_id
from .response import normalize_response
from .sensors import (
    expand_assignments,
    merge_runtime_config,
    normalize_assignments,
    normalize_keypads,
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register CDA Alarm websocket commands."""
    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_update_config)
    websocket_api.async_register_command(hass, ws_list_linked)
    websocket_api.async_register_command(hass, ws_get_dashboard)


def _entries(hass: HomeAssistant) -> list[ConfigEntry]:
    return list(hass.config_entries.async_entries(DOMAIN))


def _entry_or_none(hass: HomeAssistant, entry_id: str | None) -> ConfigEntry | None:
    if entry_id:
        entry = hass.config_entries.async_get_entry(entry_id)
        return entry if entry and entry.domain == DOMAIN else None
    entries = _entries(hass)
    return entries[0] if entries else None


def _connection_user(
    connection: websocket_api.ActiveConnection,
) -> tuple[bool, str | None]:
    user = getattr(connection, "user", None)
    if user is None:
        return False, None
    return bool(getattr(user, "is_admin", False)), getattr(user, "id", None)


def _require_dashboard_acl(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    entry: ConfigEntry,
) -> bool:
    merged = merge_runtime_config({**entry.data, **entry.options})
    is_admin, user_id = _connection_user(connection)
    return user_can_use_dashboard(
        merged.get(CONF_ACCESS) or normalize_access(None),
        is_admin=is_admin,
        user_id=user_id,
    )


def _require_admin(connection: websocket_api.ActiveConnection, msg_id: int) -> bool:
    is_admin, _user_id = _connection_user(connection)
    if is_admin:
        return True
    connection.send_error(msg_id, "unauthorized", "Administrator access required")
    return False


def _panel_entity_id(hass: HomeAssistant, entry: ConfigEntry) -> str:
    return (
        er.async_get(hass).async_get_entity_id(
            "alarm_control_panel", DOMAIN, entry.entry_id
        )
        or "alarm_control_panel.cda_alarm"
    )


def _public_config(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    merged = merge_runtime_config({**entry.data, **entry.options})
    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        CONF_NAME: merged.get(CONF_NAME, entry.title),
        CONF_SENSOR_ASSIGNMENTS: merged.get(CONF_SENSOR_ASSIGNMENTS, []),
        CONF_ENTRY_DELAY: merged.get(CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY),
        CONF_EXIT_DELAY: merged.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY),
        CONF_BLOCK_ARM_IF_OPEN: merged.get(
            CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN
        ),
        CONF_CODES: merged.get(CONF_CODES, []),
        CONF_KEYPADS: merged.get(CONF_KEYPADS, []),
        CONF_RESPONSE: merged.get(CONF_RESPONSE, normalize_response(None)),
        CONF_CAMERAS: merged.get(CONF_CAMERAS, []),
        CONF_SENSOR_CAMERA_MAP: merged.get(CONF_SENSOR_CAMERA_MAP, {}),
        CONF_ACCESS: merged.get(CONF_ACCESS, normalize_access(None)),
        "discovered_default_keypad": discover_default_keypad_device_id(hass),
        "zha_devices": _zha_devices(hass),
    }


def _dashboard_safe_config(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    merged = merge_runtime_config({**entry.data, **entry.options})
    return {
        "entry_id": entry.entry_id,
        "panel_entity_id": _panel_entity_id(hass, entry),
        CONF_SENSOR_ASSIGNMENTS: merged.get(CONF_SENSOR_ASSIGNMENTS, []),
        CONF_CAMERAS: merged.get(CONF_CAMERAS, []),
        CONF_SENSOR_CAMERA_MAP: merged.get(CONF_SENSOR_CAMERA_MAP, {}),
        CONF_ACCESS: {
            CONF_ACCESS_MODE: merged[CONF_ACCESS][CONF_ACCESS_MODE],
        },
        CONF_ENTRY_DELAY: merged.get(CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY),
        CONF_EXIT_DELAY: merged.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY),
        CONF_BLOCK_ARM_IF_OPEN: merged.get(
            CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN
        ),
    }


def _zha_devices(hass: HomeAssistant) -> list[dict[str, Any]]:
    registry = dr.async_get(hass)
    devices: list[dict[str, Any]] = []
    for device in registry.devices.values():
        if not any(domain == "zha" for domain, _ in device.identifiers):
            continue
        devices.append(
            {
                "id": device.id,
                "name": device.name_by_user or device.name or device.id,
                "model": device.model,
                "manufacturer": device.manufacturer,
            }
        )
    devices.sort(key=lambda item: (item["name"] or "").lower())
    return devices


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_GET_CONFIG,
        vol.Optional("entry_id"): cv.string,
    }
)
@websocket_api.async_response
async def ws_get_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the editable CDA Alarm configuration."""
    entry = _entry_or_none(hass, msg.get("entry_id"))
    if entry is None:
        connection.send_error(msg["id"], "not_found", "No CDA Alarm config entry")
        return
    is_admin, _user_id = _connection_user(connection)
    if not is_admin and not _require_dashboard_acl(hass, connection, entry):
        connection.send_error(msg["id"], "unauthorized", "Dashboard access denied")
        return
    payload = (
        _public_config(hass, entry)
        if is_admin
        else _dashboard_safe_config(hass, entry)
    )
    connection.send_result(msg["id"], payload)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_UPDATE_CONFIG,
        vol.Optional("entry_id"): cv.string,
        vol.Required("config"): dict,
    }
)
@websocket_api.async_response
async def ws_update_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist panel edits into the config entry options."""
    if not _require_admin(connection, msg["id"]):
        return
    entry = _entry_or_none(hass, msg.get("entry_id"))
    if entry is None:
        connection.send_error(msg["id"], "not_found", "No CDA Alarm config entry")
        return

    incoming = msg["config"]
    if not isinstance(incoming, dict):
        connection.send_error(msg["id"], "invalid_format", "config must be an object")
        return

    current = {**entry.data, **entry.options}
    assignments = normalize_assignments(
        incoming.get(CONF_SENSOR_ASSIGNMENTS, current.get(CONF_SENSOR_ASSIGNMENTS))
    )
    expanded = expand_assignments(assignments)
    keypads = normalize_keypads(incoming.get(CONF_KEYPADS, current.get(CONF_KEYPADS)))
    response = normalize_response(incoming.get(CONF_RESPONSE, current.get(CONF_RESPONSE)))
    cameras = normalize_cameras(
        incoming.get(CONF_CAMERAS, current.get(CONF_CAMERAS))
    )
    sensor_camera_map = normalize_sensor_camera_map(
        incoming.get(CONF_SENSOR_CAMERA_MAP, current.get(CONF_SENSOR_CAMERA_MAP))
    )
    access = normalize_access(incoming.get(CONF_ACCESS, current.get(CONF_ACCESS)))

    def _int(key: str, default: int) -> int:
        try:
            return int(incoming.get(key, current.get(key, default)))
        except (TypeError, ValueError):
            return default

    options = {
        CONF_SENSOR_ASSIGNMENTS: assignments,
        **expanded,
        CONF_ENTRY_DELAY: _int(CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY),
        CONF_EXIT_DELAY: _int(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY),
        CONF_BLOCK_ARM_IF_OPEN: bool(
            incoming.get(
                CONF_BLOCK_ARM_IF_OPEN,
                current.get(CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN),
            )
        ),
        CONF_CODES: incoming.get(CONF_CODES, current.get(CONF_CODES, [])),
        CONF_KEYPADS: keypads,
        CONF_RESPONSE: response,
        CONF_CAMERAS: cameras,
        CONF_SENSOR_CAMERA_MAP: sensor_camera_map,
        CONF_ACCESS: access,
    }
    if not isinstance(options[CONF_CODES], list):
        connection.send_error(msg["id"], "invalid_format", "codes must be a list")
        return

    hass.config_entries.async_update_entry(entry, options=options)
    await hass.config_entries.async_reload(entry.entry_id)
    refreshed = hass.config_entries.async_get_entry(entry.entry_id)
    if refreshed is None:
        connection.send_error(msg["id"], "not_found", "Entry disappeared after reload")
        return
    connection.send_result(msg["id"], _public_config(hass, refreshed))


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_LIST_LINKED,
        vol.Optional("entry_id"): cv.string,
        vol.Optional("panel_entity_id"): cv.string,
    }
)
@websocket_api.async_response
async def ws_list_linked(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List automations that reference CDA Alarm or known CDA blueprints."""
    if not _require_admin(connection, msg["id"]):
        return
    entry = _entry_or_none(hass, msg.get("entry_id"))
    panel_entity = msg.get("panel_entity_id") or "alarm_control_panel.cda_alarm"
    if entry is not None:
        # Prefer the actual entity id for this entry when available.
        entity_id = er.async_get(hass).async_get_entity_id(
            "alarm_control_panel", DOMAIN, entry.entry_id
        )
        if entity_id:
            panel_entity = entity_id

    linked: list[dict[str, Any]] = []
    for state in hass.states.async_all("automation"):
        entity_id = state.entity_id
        attrs = state.attributes or {}
        blob = " ".join(
            [
                entity_id,
                str(attrs.get("friendly_name") or ""),
                str(attrs.get("id") or ""),
                # Some installs expose blueprint path in attributes.
                str(attrs.get("source") or ""),
            ]
        ).lower()
        config_blob = ""
        try:
            # Best-effort: inspect restored automation config when present.
            from homeassistant.components.automation import DOMAIN as AUTO_DOMAIN

            component = hass.data.get(AUTO_DOMAIN)
            if component is not None:
                entity = component.get_entity(entity_id) if hasattr(component, "get_entity") else None
                raw = getattr(entity, "_config", None) or getattr(entity, "raw_config", None)
                if raw is not None:
                    config_blob = str(raw).lower()
        except Exception:
            _LOGGER.debug("Unable to inspect automation %s", entity_id, exc_info=True)

        haystack = f"{blob} {config_blob}"
        matches_panel = panel_entity.lower() in haystack
        matches_blueprint = any(marker in haystack for marker in CDA_BLUEPRINT_MARKERS)
        if matches_panel or matches_blueprint:
            linked.append(
                {
                    "entity_id": entity_id,
                    "name": attrs.get("friendly_name") or entity_id,
                    "state": state.state,
                    "automation_id": attrs.get("id"),
                    "matches_panel": matches_panel,
                    "matches_blueprint": matches_blueprint,
                }
            )

    linked.sort(key=lambda item: (item["name"] or "").lower())
    connection.send_result(
        msg["id"],
        {
            "panel_entity_id": panel_entity,
            "automations": linked,
            "notes": [
                "Phone and Telegram alerts remain on [CDA] Alarm Response until "
                "moved into this panel.",
                "Clear sirens/noise on Alarm Response if Response tab is configured, "
                "to avoid double sound.",
            ],
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_GET_DASHBOARD,
        vol.Optional("entry_id"): cv.string,
    }
)
@websocket_api.async_response
async def ws_get_dashboard(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return a dashboard snapshot when the configured ACL permits it."""
    entry = _entry_or_none(hass, msg.get("entry_id"))
    if entry is None:
        connection.send_error(msg["id"], "not_found", "No CDA Alarm config entry")
        return
    if not _require_dashboard_acl(hass, connection, entry):
        connection.send_error(msg["id"], "unauthorized", "Dashboard access denied")
        return

    panel_entity_id = _panel_entity_id(hass, entry)
    payload = build_dashboard(hass, entry, panel_entity_id)
    payload["can_configure"] = _connection_user(connection)[0]
    connection.send_result(msg["id"], payload)
