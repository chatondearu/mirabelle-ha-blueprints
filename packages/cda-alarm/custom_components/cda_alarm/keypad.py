"""Frient keypad input listener for CDA Alarm."""

from __future__ import annotations

from collections.abc import Callable, Mapping
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

from .codes import match_code
from .const import CONF_CODES, CONF_FRIENT_DEVICE_ID

_ARM_MODE_SERVICES = {
    0: SERVICE_ALARM_DISARM,
    1: SERVICE_ALARM_ARM_HOME,
    2: SERVICE_ALARM_ARM_NIGHT,
    3: SERVICE_ALARM_ARM_AWAY,
}


def async_setup_keypad_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
    panel_entity_id: str,
) -> Callable[[], None]:
    """Listen for arm commands from the configured Frient keypad."""
    config = {**entry.data, **entry.options}
    device_id = config.get(CONF_FRIENT_DEVICE_ID)
    codes = config.get(CONF_CODES, [])

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
            hass.services.async_call(
                ALARM_DOMAIN,
                service,
                {ATTR_ENTITY_ID: panel_entity_id, ATTR_CODE: code},
                blocking=True,
            )
        )

    return hass.bus.async_listen("zha_event", _async_handle_zha_event)
