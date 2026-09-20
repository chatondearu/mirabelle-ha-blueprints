"""ACL Companion notifications for CDA Alarm state changes."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .access import normalize_access
from .const import (
    ACCESS_MODE_ADMIN,
    ACCESS_MODE_EVERYONE,
    CONF_ACCESS,
    CONF_ACCESS_MODE,
    CONF_ACCESS_STATE_NOTIFICATIONS,
    CONF_ACCESS_USER_IDS,
    DOMAIN,
)
from .sensors import merge_runtime_config

_LOGGER = logging.getLogger(__name__)

_MOBILE_APP_DOMAIN = "mobile_app"
_NOTIFY_DOMAIN = "notify"

_NOTIFY_STATES = {
    AlarmControlPanelState.ARMED_HOME,
    AlarmControlPanelState.ARMED_AWAY,
    AlarmControlPanelState.ARMED_NIGHT,
    AlarmControlPanelState.DISARMED,
    AlarmControlPanelState.TRIGGERED,
}


def _message_for_state(state: str) -> str:
    return f"CDA Alarm: {state.replace('_', ' ')}"


def _notify_service_for_mobile_entry(entry: ConfigEntry) -> str | None:
    device_name = entry.data.get("device_name") or entry.title
    if not isinstance(device_name, str) or not device_name:
        return None
    return f"mobile_app_{slugify(device_name)}"


async def async_acl_recipient_user_ids(
    hass: HomeAssistant, access: dict[str, Any]
) -> set[str]:
    users = await hass.auth.async_get_users()
    active = [user for user in users if user.is_active and not user.system_generated]
    admins = {user.id for user in active if user.is_admin}
    mode = access.get(CONF_ACCESS_MODE, ACCESS_MODE_ADMIN)
    if mode == ACCESS_MODE_ADMIN:
        return admins
    if mode == ACCESS_MODE_EVERYONE:
        return {user.id for user in active}
    listed = {
        user_id
        for user_id in (access.get(CONF_ACCESS_USER_IDS) or [])
        if isinstance(user_id, str) and user_id
    }
    return admins | listed


def resolve_mobile_notify_services(
    hass: HomeAssistant, recipient_user_ids: set[str]
) -> list[str]:
    services: list[str] = []
    seen: set[str] = set()
    for entry in hass.config_entries.async_entries(_MOBILE_APP_DOMAIN):
        user_id = entry.data.get("user_id")
        if not isinstance(user_id, str) or user_id not in recipient_user_ids:
            continue
        service = _notify_service_for_mobile_entry(entry)
        if service is None or service in seen:
            continue
        if not hass.services.has_service(_NOTIFY_DOMAIN, service):
            continue
        seen.add(service)
        services.append(service)
    return services


def build_notify_payload(state: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": "CDA Alarm",
        "message": _message_for_state(state),
    }
    if state == AlarmControlPanelState.TRIGGERED:
        payload["data"] = {
            "ttl": 0,
            "priority": "high",
            "channel": "alarm_stream",
            "push": {
                "sound": {
                    "name": "default",
                    "critical": 1,
                    "volume": 1.0,
                }
            },
        }
    return payload


async def async_send_state_notifications(
    hass: HomeAssistant,
    access: dict[str, Any],
    state: str,
) -> None:
    if not access.get(CONF_ACCESS_STATE_NOTIFICATIONS, True):
        return
    try:
        panel_state = AlarmControlPanelState(state)
    except ValueError:
        return
    if panel_state not in _NOTIFY_STATES:
        return

    try:
        recipients = await async_acl_recipient_user_ids(hass, access)
        services = resolve_mobile_notify_services(hass, recipients)
        payload = build_notify_payload(state)
        for service in services:
            try:
                await hass.services.async_call(
                    _NOTIFY_DOMAIN,
                    service,
                    payload,
                    blocking=True,
                )
            except Exception:
                _LOGGER.debug(
                    "Unable to notify %s.%s for CDA Alarm state",
                    _NOTIFY_DOMAIN,
                    service,
                    exc_info=True,
                )
    except Exception:
        _LOGGER.debug("Unable to send CDA Alarm state notifications", exc_info=True)


def async_setup_state_notifier(
    hass: HomeAssistant,
    entry: ConfigEntry,
    panel_entity_id: str,
) -> Callable[[], None]:
    @callback
    def _async_panel_state_changed(event: Event[EventStateChangedData]) -> None:
        new_state = event.data["new_state"]
        old_state = event.data["old_state"]
        if new_state is None:
            return
        if old_state is not None and old_state.state == new_state.state:
            return

        stored = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if isinstance(stored, dict) and CONF_ACCESS in stored:
            access = normalize_access(stored.get(CONF_ACCESS))
        else:
            access = merge_runtime_config({**entry.data, **entry.options}).get(
                CONF_ACCESS, normalize_access(None)
            )

        hass.async_create_task(
            async_send_state_notifications(hass, access, new_state.state)
        )

    return async_track_state_change_event(
        hass,
        [panel_entity_id],
        _async_panel_state_changed,
    )
