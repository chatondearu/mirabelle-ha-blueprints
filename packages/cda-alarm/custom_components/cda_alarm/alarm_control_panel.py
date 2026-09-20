"""Alarm control panel platform for CDA Alarm."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .codes import match_code
from .const import (
    ATTR_ARM_FAILURE,
    ATTR_ARM_MODE,
    ATTR_OPEN_SENSORS,
    CONF_BLOCK_ARM_IF_OPEN,
    CONF_CODES,
    CONF_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_NAME,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    DEFAULT_BLOCK_ARM_IF_OPEN,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DOMAIN,
    EVENT_ARM_FAILED,
    REASON_INVALID_CODE,
    REASON_OPEN_SENSORS,
)

_LOGGER = logging.getLogger(__name__)
_OPEN_STATES = {"on", "open"}

MODE_SENSORS = {
    AlarmControlPanelState.ARMED_AWAY: CONF_SENSORS_AWAY,
    AlarmControlPanelState.ARMED_HOME: CONF_SENSORS_HOME,
    AlarmControlPanelState.ARMED_NIGHT: CONF_SENSORS_NIGHT,
}
RESTORABLE_STATES = {
    *MODE_SENSORS,
    AlarmControlPanelState.ARMING,
    AlarmControlPanelState.PENDING,
    AlarmControlPanelState.TRIGGERED,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CDA Alarm panel entity."""
    async_add_entities([CdaAlarmControlPanel(entry, hass.data[DOMAIN][entry.entry_id])])


class CdaAlarmControlPanel(AlarmControlPanelEntity, RestoreEntity):
    """Represent a CDA Alarm control panel."""

    _attr_alarm_state = AlarmControlPanelState.DISARMED
    _attr_should_poll = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.TRIGGER
    )

    def __init__(self, entry: ConfigEntry, config: dict[str, Any]) -> None:
        """Initialize the panel."""
        self._config = config
        self._attr_name = config.get(CONF_NAME, entry.title)
        self._attr_unique_id = entry.entry_id
        self._codes = config.get(CONF_CODES, [])
        has_pin = any(code.get("pin") for code in self._codes)
        self._has_credentials = any(
            code.get("pin") or code.get("rfid") or code.get("nfc_tag_id")
            for code in self._codes
        )
        self._attr_code_arm_required = self._has_credentials
        if has_pin:
            self._attr_code_format = CodeFormat.NUMBER
        elif self._has_credentials:
            self._attr_code_format = CodeFormat.TEXT
        else:
            self._attr_code_format = None
        self._active_sensors: list[str] = []
        self._open_sensors: dict[str, str] = {}
        self._arm_mode: AlarmControlPanelState | None = None
        self._arm_failure: dict[str, Any] | None = None
        self._cancel_exit_delay: Callable[[], None] | None = None
        self._cancel_entry_delay: Callable[[], None] | None = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return panel-specific state attributes."""
        return {
            ATTR_OPEN_SENSORS: self._open_sensors,
            ATTR_ARM_MODE: self._arm_mode.value if self._arm_mode else None,
            ATTR_ARM_FAILURE: self._arm_failure,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to configured sensor changes and restore the last state."""
        await super().async_added_to_hass()
        self.async_on_remove(self._cancel_delays)
        sensors = {
            sensor
            for key in (CONF_SENSORS_AWAY, CONF_SENSORS_HOME, CONF_SENSORS_NIGHT)
            for sensor in self._config.get(key, [])
        }
        if sensors:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    sensors,
                    self._async_sensor_changed,
                )
            )
        await self._async_restore_last_state()

    async def _async_restore_last_state(self) -> None:
        """Restore the armed state across a reload or a restart."""
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            restored = AlarmControlPanelState(last_state.state)
        except ValueError:
            return
        if restored not in RESTORABLE_STATES:
            return

        arm_mode = (
            restored
            if restored in MODE_SENSORS
            else _parse_arm_mode(last_state.attributes.get(ATTR_ARM_MODE))
        )
        if arm_mode is None:
            if restored is not AlarmControlPanelState.TRIGGERED:
                # Without a known mode there is nothing meaningful to watch.
                return
        else:
            self._arm_mode = arm_mode
            self._active_sensors = list(self._config.get(MODE_SENSORS[arm_mode], []))

        self._attr_alarm_state = restored
        if restored is AlarmControlPanelState.ARMING and arm_mode is not None:
            self._schedule_exit_delay(arm_mode)
            return
        self._async_reevaluate_sensors()

    @callback
    def _async_reevaluate_sensors(self) -> None:
        """Re-check monitored sensors, e.g. after restoring an armed state."""
        if self._attr_alarm_state not in MODE_SENSORS:
            return
        open_sensors = self._get_open_sensors(self._active_sensors)
        if not open_sensors:
            return
        self._open_sensors = open_sensors
        self._start_entry_delay()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Arm the alarm in away mode."""
        self._async_arm(AlarmControlPanelState.ARMED_AWAY, code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Arm the alarm in home mode."""
        self._async_arm(AlarmControlPanelState.ARMED_HOME, code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Arm the alarm in night mode."""
        self._async_arm(AlarmControlPanelState.ARMED_NIGHT, code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarm the alarm when the code is valid."""
        if not self._is_valid_code(code):
            _LOGGER.warning("Rejected CDA Alarm disarm request with invalid code")
            return
        self._cancel_delays()
        self._active_sensors = []
        self._open_sensors = {}
        self._arm_mode = None
        self._arm_failure = None
        self._attr_alarm_state = AlarmControlPanelState.DISARMED
        self.async_write_ha_state()

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Trigger the alarm."""
        self._cancel_delays()
        self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        self.async_write_ha_state()

    @callback
    def _async_arm(
        self,
        target_state: AlarmControlPanelState,
        code: str | None,
    ) -> None:
        """Validate and begin arming for a target mode."""
        if not self._is_valid_code(code):
            _LOGGER.warning("Rejected CDA Alarm arm request with invalid code")
            self._async_report_arm_failure(REASON_INVALID_CODE, target_state)
            return

        sensors = list(self._config.get(MODE_SENSORS[target_state], []))
        open_sensors = self._get_open_sensors(sensors)
        if self._block_arm_if_open and open_sensors:
            self._log_open_sensors(open_sensors)
            self._async_report_arm_failure(
                REASON_OPEN_SENSORS,
                target_state,
                open_sensors,
            )
            return

        self._cancel_delays()
        self._active_sensors = sensors
        self._open_sensors = {}
        self._arm_failure = None
        exit_delay = float(self._config.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY))
        if exit_delay <= 0:
            self._finish_arming(target_state)
            return

        self._arm_mode = target_state
        self._attr_alarm_state = AlarmControlPanelState.ARMING
        self.async_write_ha_state()
        self._schedule_exit_delay(target_state)

    @callback
    def _schedule_exit_delay(self, target_state: AlarmControlPanelState) -> None:
        """Arm the panel once the configured exit delay has elapsed."""
        exit_delay = float(self._config.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY))
        self._cancel_exit_delay = async_call_later(
            self.hass,
            max(exit_delay, 0),
            callback(lambda _now: self._finish_arming(target_state)),
        )

    @callback
    def _finish_arming(self, target_state: AlarmControlPanelState) -> None:
        """Complete arming after the exit delay."""
        self._cancel_exit_delay = None
        open_sensors = self._get_open_sensors(self._active_sensors)
        if self._block_arm_if_open and open_sensors:
            self._log_open_sensors(open_sensors)
            self._active_sensors = []
            self._open_sensors = {}
            self._arm_mode = None
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
            self._async_report_arm_failure(
                REASON_OPEN_SENSORS,
                target_state,
                open_sensors,
            )
            return

        self._arm_failure = None
        self._arm_mode = target_state
        self._attr_alarm_state = target_state
        self.async_write_ha_state()

    @property
    def _block_arm_if_open(self) -> bool:
        """Return whether arming is refused while a sensor is open."""
        return bool(
            self._config.get(CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN)
        )

    @callback
    def _async_report_arm_failure(
        self,
        reason: str,
        target_state: AlarmControlPanelState,
        open_sensors: dict[str, str] | None = None,
    ) -> None:
        """Expose an arming failure as an attribute and a bus event."""
        self._arm_failure = {
            "reason": reason,
            "mode": target_state.value,
            ATTR_OPEN_SENSORS: dict(open_sensors or {}),
        }
        self.async_write_ha_state()
        self.hass.bus.async_fire(
            EVENT_ARM_FAILED,
            {ATTR_ENTITY_ID: self.entity_id, **self._arm_failure},
        )

    @staticmethod
    def _log_open_sensors(open_sensors: dict[str, str]) -> None:
        """Log the sensors that prevent arming."""
        _LOGGER.warning(
            "Refusing to arm CDA Alarm because sensors are open: %s",
            ", ".join(open_sensors),
        )

    @callback
    def _async_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle an active sensor opening."""
        if self._attr_alarm_state not in MODE_SENSORS:
            return
        new_state = event.data["new_state"]
        if (
            new_state is None
            or new_state.entity_id not in self._active_sensors
            or new_state.state not in _OPEN_STATES
        ):
            return

        self._open_sensors = self._get_open_sensors(self._active_sensors)
        self.async_write_ha_state()
        self._start_entry_delay()

    @callback
    def _start_entry_delay(self) -> None:
        """Start the entry delay unless one is already running."""
        if self._cancel_entry_delay is not None:
            return
        entry_delay = float(self._config.get(CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY))
        if entry_delay <= 0:
            self._finish_entry_delay()
            return
        self._cancel_entry_delay = async_call_later(
            self.hass,
            entry_delay,
            self._finish_entry_delay,
        )

    @callback
    def _finish_entry_delay(self, _now: datetime | None = None) -> None:
        """Trigger the alarm after the entry delay."""
        self._cancel_entry_delay = None
        self._open_sensors = self._get_open_sensors(self._active_sensors)
        self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        self.async_write_ha_state()

    def _get_open_sensors(self, sensors: list[str]) -> dict[str, str]:
        """Return currently open sensors and their states."""
        return {
            entity_id: state.state
            for entity_id in sensors
            if (state := self.hass.states.get(entity_id)) is not None
            and state.state in _OPEN_STATES
        }

    def _is_valid_code(self, code: str | None) -> bool:
        """Return whether a supplied PIN, RFID badge, or NFC tag id is valid."""
        if not self._has_credentials:
            return True
        # The same string can be a PIN, an RFID badge, or an NFC tag id.
        return match_code(self._codes, pin=code, rfid=code, nfc_tag_id=code) is not None

    @callback
    def _cancel_delays(self) -> None:
        """Cancel pending entry and exit delay callbacks."""
        if self._cancel_exit_delay is not None:
            self._cancel_exit_delay()
            self._cancel_exit_delay = None
        if self._cancel_entry_delay is not None:
            self._cancel_entry_delay()
            self._cancel_entry_delay = None


def _parse_arm_mode(value: Any) -> AlarmControlPanelState | None:
    """Return the restored arm mode when it maps to a monitored mode."""
    try:
        mode = AlarmControlPanelState(value)
    except ValueError:
        return None
    return mode if mode in MODE_SENSORS else None
