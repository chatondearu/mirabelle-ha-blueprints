"""Frient keypad input listener for CDA Alarm."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_CODE, ATTR_ENTITY_ID
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .codes import match_code
from .const import (
    CONF_CODES,
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    DEFAULT_KEYPAD_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

_ZHA_DOMAIN = "zha"
_ZHA_FEEDBACK_SERVICE = "issue_zigbee_cluster_command"

_ARM_MODE_SERVICES = {
    0: SERVICE_ALARM_DISARM,
    1: SERVICE_ALARM_ARM_HOME,
    2: SERVICE_ALARM_ARM_NIGHT,
    3: SERVICE_ALARM_ARM_AWAY,
}
_ARM_MODE_PANEL_STATUS = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
}


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
    """Listen for arm commands from the configured Frient keypad."""
    config = {**entry.data, **entry.options}
    device_id = config.get(CONF_FRIENT_DEVICE_ID)
    codes = config.get(CONF_CODES, [])
    feedback_enabled = config.get(CONF_ENABLE_KEYPAD_FEEDBACK, False)
    keypad_endpoint = config.get(CONF_KEYPAD_ENDPOINT, DEFAULT_KEYPAD_ENDPOINT)

    @callback
    def _async_handle_zha_event(event: Event[dict[str, Any]]) -> None:
        if (
            not device_id
            or event.data.get("device_id") != device_id
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

        code = params.get("code", args.get("code"))
        if code is not None:
            code = str(code)
        if any(item.get("pin") for item in codes) and match_code(codes, pin=code) is None:
            return

        hass.async_create_task(
            _async_execute_keypad_action(
                hass,
                service,
                panel_entity_id,
                code,
                device_id,
                feedback_enabled,
                keypad_endpoint,
                _ARM_MODE_PANEL_STATUS[arm_mode],
            ),
        )

    return hass.bus.async_listen("zha_event", _async_handle_zha_event)


async def _async_execute_keypad_action(
    hass: HomeAssistant,
    service: str,
    panel_entity_id: str,
    code: str | None,
    device_id: str,
    feedback_enabled: bool,
    keypad_endpoint: int,
    panel_status: int,
) -> None:
    """Execute the panel action before sending optional keypad feedback."""
    await hass.services.async_call(
        ALARM_DOMAIN,
        service,
        {ATTR_ENTITY_ID: panel_entity_id, ATTR_CODE: code},
        blocking=True,
    )
    if feedback_enabled:
        await _async_push_keypad_feedback(
            hass,
            device_id,
            keypad_endpoint,
            panel_status,
        )
