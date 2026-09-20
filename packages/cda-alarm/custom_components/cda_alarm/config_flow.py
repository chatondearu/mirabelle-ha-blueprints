"""Config and options flows for CDA Alarm."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BLOCK_ARM_IF_OPEN,
    CONF_CODES,
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    CONF_NAME,
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSORS,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    DEFAULT_BLOCK_ARM_IF_OPEN,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DEFAULT_KEYPAD_ENDPOINT,
    DEFAULT_MODES,
    DOMAIN,
    MODE_OPTIONS,
)
from .sensors import (
    assignments_from_legacy,
    expand_assignments,
    normalize_assignments,
)

CONF_CODES_JSON = "codes_json"
CODE_KEYS = {"name", "pin", "rfid", "nfc_tag_id"}


class CdaAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the CDA Alarm config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Create a CDA Alarm entry."""
        if user_input is not None:
            name = user_input[CONF_NAME]
            return self.async_create_entry(
                title=name,
                data={
                    CONF_NAME: name,
                    CONF_CODES: [],
                    CONF_SENSOR_ASSIGNMENTS: [],
                    CONF_SENSORS_AWAY: [],
                    CONF_SENSORS_HOME: [],
                    CONF_SENSORS_NIGHT: [],
                    CONF_ENTRY_DELAY: DEFAULT_ENTRY_DELAY,
                    CONF_EXIT_DELAY: DEFAULT_EXIT_DELAY,
                    CONF_BLOCK_ARM_IF_OPEN: DEFAULT_BLOCK_ARM_IF_OPEN,
                    CONF_FRIENT_DEVICE_ID: "",
                    CONF_ENABLE_KEYPAD_FEEDBACK: False,
                    CONF_KEYPAD_ENDPOINT: DEFAULT_KEYPAD_ENDPOINT,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME): str}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the CDA Alarm options flow."""
        return CdaAlarmOptionsFlow()


class CdaAlarmOptionsFlow(config_entries.OptionsFlow):
    """Handle CDA Alarm options in two steps: sensors, then per-entity modes."""

    def __init__(self) -> None:
        """Initialize the options flow."""
        self._pending: dict[str, Any] = {}
        self._sensors: list[str] = []

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Pick sensors and general settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                codes = _parse_codes(user_input[CONF_CODES_JSON])
            except (json.JSONDecodeError, TypeError, ValueError):
                errors[CONF_CODES_JSON] = "invalid_codes"
            else:
                sensors = list(user_input.get(CONF_SENSORS) or [])
                self._sensors = sensors
                self._pending = {
                    CONF_ENTRY_DELAY: user_input[CONF_ENTRY_DELAY],
                    CONF_EXIT_DELAY: user_input[CONF_EXIT_DELAY],
                    CONF_BLOCK_ARM_IF_OPEN: user_input[CONF_BLOCK_ARM_IF_OPEN],
                    CONF_FRIENT_DEVICE_ID: user_input.get(
                        CONF_FRIENT_DEVICE_ID,
                        "",
                    )
                    or "",
                    CONF_ENABLE_KEYPAD_FEEDBACK: user_input[
                        CONF_ENABLE_KEYPAD_FEEDBACK
                    ],
                    CONF_KEYPAD_ENDPOINT: user_input[CONF_KEYPAD_ENDPOINT],
                    CONF_CODES: codes,
                }
                if not sensors:
                    return self._async_store_assignments([])
                return await self.async_step_assign_modes()

        return self.async_show_form(
            step_id="init",
            data_schema=self._init_schema(user_input),
            errors=errors,
        )

    async def async_step_assign_modes(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Assign away / home / night modes for each selected sensor."""
        if user_input is not None:
            assignments: list[dict[str, Any]] = []
            for entity_id in self._sensors:
                modes = [
                    mode
                    for mode in MODE_OPTIONS
                    if mode in (user_input.get(entity_id) or [])
                ]
                if modes:
                    assignments.append({"entity_id": entity_id, "modes": modes})
            return self._async_store_assignments(assignments)

        return self.async_show_form(
            step_id="assign_modes",
            data_schema=self._assign_schema(),
        )

    def _async_store_assignments(
        self,
        assignments: list[dict[str, Any]],
    ) -> config_entries.ConfigFlowResult:
        """Persist assignments and derived per-mode lists."""
        normalized = normalize_assignments(assignments)
        expanded = expand_assignments(normalized)
        return self.async_create_entry(
            title="",
            data={
                **self._pending,
                CONF_SENSOR_ASSIGNMENTS: normalized,
                **expanded,
            },
        )

    def _option(
        self,
        key: str,
        default: Any,
        user_input: dict[str, Any] | None = None,
    ) -> Any:
        """Read an option with fallbacks to entry data then defaults."""
        if user_input is not None and key in user_input:
            return user_input[key]
        if key in self.config_entry.options:
            return self.config_entry.options[key]
        return self.config_entry.data.get(key, default)

    def _current_assignments(self) -> list[dict[str, Any]]:
        """Return saved assignments or rebuild them from legacy lists."""
        raw = self.config_entry.options.get(
            CONF_SENSOR_ASSIGNMENTS,
            self.config_entry.data.get(CONF_SENSOR_ASSIGNMENTS),
        )
        if raw:
            return normalize_assignments(raw)
        return assignments_from_legacy(
            {**self.config_entry.data, **self.config_entry.options}
        )

    def _init_schema(self, user_input: dict[str, Any] | None) -> vol.Schema:
        """Build the first options step schema."""
        assignments = self._current_assignments()
        default_sensors = [item["entity_id"] for item in assignments]
        if user_input is not None and CONF_SENSORS in user_input:
            sensors_default = user_input[CONF_SENSORS]
        else:
            sensors_default = default_sensors
        values = {
            CONF_SENSORS: sensors_default,
            CONF_ENTRY_DELAY: self._option(
                CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY, user_input
            ),
            CONF_EXIT_DELAY: self._option(
                CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY, user_input
            ),
            CONF_BLOCK_ARM_IF_OPEN: self._option(
                CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN, user_input
            ),
            CONF_FRIENT_DEVICE_ID: self._option(
                CONF_FRIENT_DEVICE_ID, "", user_input
            ),
            CONF_ENABLE_KEYPAD_FEEDBACK: self._option(
                CONF_ENABLE_KEYPAD_FEEDBACK, False, user_input
            ),
            CONF_KEYPAD_ENDPOINT: self._option(
                CONF_KEYPAD_ENDPOINT, DEFAULT_KEYPAD_ENDPOINT, user_input
            ),
            CONF_CODES_JSON: (
                user_input.get(CONF_CODES_JSON)
                if user_input is not None and CONF_CODES_JSON in user_input
                else json.dumps(self._option(CONF_CODES, [], None), indent=2)
            ),
        }

        delay_selector = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=3600,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        )
        return vol.Schema(
            {
                vol.Required(
                    CONF_SENSORS,
                    default=values[CONF_SENSORS],
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
                vol.Required(
                    CONF_ENTRY_DELAY,
                    default=values[CONF_ENTRY_DELAY],
                ): delay_selector,
                vol.Required(
                    CONF_EXIT_DELAY,
                    default=values[CONF_EXIT_DELAY],
                ): delay_selector,
                vol.Required(
                    CONF_BLOCK_ARM_IF_OPEN,
                    default=values[CONF_BLOCK_ARM_IF_OPEN],
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_FRIENT_DEVICE_ID,
                    default=values[CONF_FRIENT_DEVICE_ID],
                ): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(integration="zha")
                ),
                vol.Required(
                    CONF_ENABLE_KEYPAD_FEEDBACK,
                    default=values[CONF_ENABLE_KEYPAD_FEEDBACK],
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_KEYPAD_ENDPOINT,
                    default=values[CONF_KEYPAD_ENDPOINT],
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=255,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_CODES_JSON,
                    default=values[CONF_CODES_JSON],
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
            }
        )

    def _assign_schema(self) -> vol.Schema:
        """Build per-entity mode selectors for the selected sensors."""
        saved = {
            item["entity_id"]: item["modes"] for item in self._current_assignments()
        }
        mode_selector = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"value": MODE_OPTIONS[0], "label": "Away"},
                    {"value": MODE_OPTIONS[1], "label": "Home"},
                    {"value": MODE_OPTIONS[2], "label": "Night"},
                ],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
            )
        )
        schema: dict[Any, Any] = {}
        for entity_id in self._sensors:
            default_modes = saved.get(entity_id) or list(DEFAULT_MODES)
            schema[vol.Required(entity_id, default=default_modes)] = mode_selector
        return vol.Schema(schema)


def _parse_codes(value: str) -> list[dict[str, Any]]:
    """Parse and validate the codes JSON field."""
    codes = json.loads(value)
    if not isinstance(codes, list):
        raise ValueError("Codes must be a list")
    for code in codes:
        if not isinstance(code, dict):
            raise ValueError("Each code must be an object")
        if not set(code).issubset(CODE_KEYS):
            raise ValueError("Code contains an unsupported key")
        if any(
            item is not None and not isinstance(item, str) for item in code.values()
        ):
            raise ValueError("Code values must be strings or null")
    return codes
