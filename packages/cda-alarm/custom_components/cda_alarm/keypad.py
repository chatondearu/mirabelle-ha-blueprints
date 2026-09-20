"""Frient keypad input listener for CDA Alarm."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_CODE, ATTR_ENTITY_ID
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_KEYPAD_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT_KEY,
    CONF_KEYPAD_FEEDBACK,
    CONF_KEYPADS,
    DEFAULT_KEYPAD_ENDPOINT,
    DOMAIN,
)
from .sensors import merge_runtime_config, resolve_active_keypads

_LOGGER = logging.getLogger(__name__)

_ZHA_DOMAIN = "zha"
_ZHA_FEEDBACK_SERVICE = "issue_zigbee_cluster_command"
_CODE_FIELDS = ("code", "arm_disarm_code")
_FRIENT_MODEL_MARKERS = ("kepzb", "frient")

_ARM_MODE_SERVICES = {
    0: SERVICE_ALARM_DISARM,
    1: SERVICE_ALARM_ARM_HOME,
    2: SERVICE_ALARM_ARM_NIGHT,
    3: SERVICE_ALARM_ARM_AWAY,
}

_PANEL_STATUS_BY_STATE = {
    AlarmControlPanelState.DISARMED: 0,
    AlarmControlPanelState.ARMED_HOME: 1,
    AlarmControlPanelState.ARMED_NIGHT: 2,
    AlarmControlPanelState.ARMED_AWAY: 3,
    AlarmControlPanelState.ARMING: 4,
    AlarmControlPanelState.PENDING: 5,
    AlarmControlPanelState.TRIGGERED: 7,
}
_PANEL_STATUS_NOT_READY = 6


def _panel_status(state: str | None) -> int:
    """Map a panel state string to its IAS ACE panel status."""
    try:
        return _PANEL_STATUS_BY_STATE[AlarmControlPanelState(state)]
    except (KeyError, ValueError):
        return _PANEL_STATUS_NOT_READY


def _extract_code(params: Mapping[str, Any], args: Mapping[str, Any]) -> str | None:
    """Return the PIN or badge id carried by a ZHA arm event."""
    for field in _CODE_FIELDS:
        for source in (params, args):
            value = source.get(field)
            if value is not None and str(value) != "":
                return str(value)
    return None


def discover_default_keypad_device_id(hass: HomeAssistant) -> str | None:
    """Return the first ZHA device that looks like a Frient KEPZB keypad."""
    registry = dr.async_get(hass)
    for device in registry.devices.values():
        if device.via_device_id is None and not any(
            domain == _ZHA_DOMAIN for domain, _ in device.identifiers
        ):
            # Still allow via_device_id devices; check identifiers below.
            pass
        if not any(domain == _ZHA_DOMAIN for domain, _ in device.identifiers):
            continue
        haystack = " ".join(
            filter(
                None,
                [
                    device.model,
                    device.name,
                    device.name_by_user,
                    device.manufacturer,
                ],
            )
        ).lower()
        if any(marker in haystack for marker in _FRIENT_MODEL_MARKERS):
            return device.id
    return None


async def _async_push_keypad_feedback(
    hass: HomeAssistant,
    device_id: str,
    endpoint_id: int,
    panel_status: int,
) -> None:
    """Best-effort push the panel status to the keypad IAS ACE cluster."""
    try:
        device = dr.async_get(hass).async_get(device_id)
        if device is None:
            return
        ieee = next(
            (
                identifier
                for domain, identifier in device.identifiers
                if domain == _ZHA_DOMAIN
            ),
            None,
        )
        if ieee is None:
            return

        await hass.services.async_call(
            _ZHA_DOMAIN,
            _ZHA_FEEDBACK_SERVICE,
            {
                "ieee": ieee,
                "endpoint_id": endpoint_id,
                "cluster_id": 1281,
                "cluster_type": "out",
                "command": 4,
                "command_type": "client",
                "args": [panel_status, 0, 0, 0],
            },
            blocking=True,
        )
    except Exception:
        _LOGGER.debug("Unable to push status feedback to Frient keypad", exc_info=True)


def async_setup_keypad_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
    panel_entity_id: str,
) -> Callable[[], None]:
    """Listen for arm commands from configured (or default) Frient keypads."""
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    config = stored if isinstance(stored, dict) else merge_runtime_config(
        {**entry.data, **entry.options}
    )
    keypads = resolve_active_keypads(
        config.get(CONF_KEYPADS) or [],
        discovered_default=discover_default_keypad_device_id(hass),
    )
    keypad_by_id = {
        item[CONF_KEYPAD_DEVICE_ID]: item for item in keypads if item.get(CONF_KEYPAD_DEVICE_ID)
    }
    last_status: dict[str, int | None] = {
        device_id: None for device_id in keypad_by_id
    }

    async def _async_push_status(device_id: str, panel_status: int) -> None:
        """Push a panel status to one keypad when feedback is enabled."""
        item = keypad_by_id.get(device_id)
        if item is None or not item.get(CONF_KEYPAD_FEEDBACK):
            return
        if last_status.get(device_id) == panel_status:
            return
        last_status[device_id] = panel_status
        await _async_push_keypad_feedback(
            hass,
            device_id,
            int(item.get(CONF_KEYPAD_ENDPOINT_KEY, DEFAULT_KEYPAD_ENDPOINT)),
            panel_status,
        )

    async def _async_push_all(panel_status: int) -> None:
        for device_id in keypad_by_id:
            await _async_push_status(device_id, panel_status)

    @callback
    def _async_panel_state_changed(event: Event[EventStateChangedData]) -> None:
        new_state = event.data["new_state"]
        if new_state is None:
            return
        hass.async_create_task(_async_push_all(_panel_status(new_state.state)))

    @callback
    def _async_handle_zha_event(event: Event[dict[str, Any]]) -> None:
        device_id = event.data.get("device_id")
        if (
            not device_id
            or device_id not in keypad_by_id
            or event.data.get("command") != "arm"
        ):
            return

        params = event.data.get("params")
        if not isinstance(params, Mapping):
            params = {}
        args = event.data.get("args")
        if not isinstance(args, Mapping):
            args = {}

        try:
            arm_mode = int(params.get("arm_mode", args.get("arm_mode", -1)))
        except (TypeError, ValueError):
            return
        service = _ARM_MODE_SERVICES.get(arm_mode)
        if service is None:
            return

        code = _extract_code(params, args)

        async def _push_for_device(status: int) -> None:
            await _async_push_status(device_id, status)

        hass.async_create_task(
            _async_execute_keypad_action(
                hass,
                service,
                panel_entity_id,
                code,
                _push_for_device,
            ),
        )

    unsubscribes = [hass.bus.async_listen("zha_event", _async_handle_zha_event)]
    if any(item.get(CONF_KEYPAD_FEEDBACK) for item in keypad_by_id.values()):
        unsubscribes.append(
            async_track_state_change_event(
                hass,
                [panel_entity_id],
                _async_panel_state_changed,
            )
        )

    @callback
    def _async_unsubscribe() -> None:
        for unsubscribe in unsubscribes:
            unsubscribe()

    return _async_unsubscribe


async def _async_execute_keypad_action(
    hass: HomeAssistant,
    service: str,
    panel_entity_id: str,
    code: str | None,
    push_status: Callable[[int], Awaitable[None]],
) -> None:
    """Execute the panel action, then report the real panel state."""
    data: dict[str, Any] = {ATTR_ENTITY_ID: panel_entity_id}
    if code is not None:
        data[ATTR_CODE] = code
    await hass.services.async_call(ALARM_DOMAIN, service, data, blocking=True)
    await hass.async_block_till_done()
    panel_state = hass.states.get(panel_entity_id)
    await push_status(_panel_status(panel_state.state if panel_state else None))
