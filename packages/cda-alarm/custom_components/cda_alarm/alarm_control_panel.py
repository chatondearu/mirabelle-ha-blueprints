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
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .codes import match_code
from .const import (
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
)

_LOGGER = logging.getLogger(__name__)
_OPEN_STATES = {"on", "open"}

MODE_SENSORS = {
    AlarmControlPanelState.ARMED_AWAY: CONF_SENSORS_AWAY,
    AlarmControlPanelState.ARMED_HOME: CONF_SENSORS_HOME,
    AlarmControlPanelState.ARMED_NIGHT: CONF_SENSORS_NIGHT,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CDA Alarm panel entity."""
    async_add_entities([CdaAlarmControlPanel(entry, hass.data[DOMAIN][entry.entry_id])])


class CdaAlarmControlPanel(AlarmControlPanelEntity):
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
        self._has_pin = any(code.get("pin") for code in self._codes)
        self._attr_code_arm_required = self._has_pin
        self._attr_code_format = CodeFormat.NUMBER if self._has_pin else None
        self._active_sensors: list[str] = []
        self._open_sensors: dict[str, str] = {}
        self._cancel_exit_delay: Callable[[], None] | None = None
        self._cancel_entry_delay: Callable[[], None] | None = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return panel-specific state attributes."""
        return {ATTR_OPEN_SENSORS: self._open_sensors}

    async def async_added_to_hass(self) -> None:
        """Subscribe to configured sensor changes."""
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
            return

        sensors = list(self._config.get(MODE_SENSORS[target_state], []))
        open_sensors = self._get_open_sensors(sensors)
        if (
            self._config.get(CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN)
            and open_sensors
        ):
            _LOGGER.warning(
                "Refusing to arm CDA Alarm because sensors are open: %s",
                ", ".join(open_sensors),
            )
            return

        self._cancel_delays()
        self._active_sensors = sensors
        self._open_sensors = {}
        exit_delay = float(self._config.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY))
        if exit_delay <= 0:
            self._finish_arming(target_state)
            return

        self._attr_alarm_state = AlarmControlPanelState.ARMING
        self.async_write_ha_state()
        self._cancel_exit_delay = async_call_later(
            self.hass,
            exit_delay,
            callback(lambda _now: self._finish_arming(target_state)),
        )

    @callback
    def _finish_arming(self, target_state: AlarmControlPanelState) -> None:
        """Complete arming after the exit delay."""
        self._cancel_exit_delay = None
        open_sensors = self._get_open_sensors(self._active_sensors)
        if (
            self._config.get(CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN)
            and open_sensors
        ):
            _LOGGER.warning(
                "Refusing to arm CDA Alarm because sensors are open: %s",
                ", ".join(open_sensors),
            )
            self._active_sensors = []
            self._open_sensors = {}
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
            self.async_write_ha_state()
            return

        self._attr_alarm_state = target_state
        self.async_write_ha_state()

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
        """Return whether a supplied PIN is valid."""
        return not self._has_pin or match_code(self._codes, pin=code) is not None

    @callback
    def _cancel_delays(self) -> None:
        """Cancel pending entry and exit delay callbacks."""
        if self._cancel_exit_delay is not None:
            self._cancel_exit_delay()
            self._cancel_exit_delay = None
        if self._cancel_entry_delay is not None:
            self._cancel_entry_delay()
            self._cancel_entry_delay = None
