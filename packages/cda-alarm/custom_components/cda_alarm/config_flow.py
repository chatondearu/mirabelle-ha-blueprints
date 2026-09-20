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
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    DEFAULT_BLOCK_ARM_IF_OPEN,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DEFAULT_KEYPAD_ENDPOINT,
    DOMAIN,
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
        return CdaAlarmOptionsFlow(config_entry)


class CdaAlarmOptionsFlow(config_entries.OptionsFlow):
    """Handle CDA Alarm options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Edit all CDA Alarm options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                codes = _parse_codes(user_input[CONF_CODES_JSON])
            except (json.JSONDecodeError, TypeError, ValueError):
                errors[CONF_CODES_JSON] = "invalid_codes"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SENSORS_AWAY: user_input[CONF_SENSORS_AWAY],
                        CONF_SENSORS_HOME: user_input[CONF_SENSORS_HOME],
                        CONF_SENSORS_NIGHT: user_input[CONF_SENSORS_NIGHT],
                        CONF_ENTRY_DELAY: user_input[CONF_ENTRY_DELAY],
                        CONF_EXIT_DELAY: user_input[CONF_EXIT_DELAY],
                        CONF_BLOCK_ARM_IF_OPEN: user_input[
                            CONF_BLOCK_ARM_IF_OPEN
                        ],
                        CONF_FRIENT_DEVICE_ID: user_input.get(
                            CONF_FRIENT_DEVICE_ID,
                            "",
                        ),
                        CONF_ENABLE_KEYPAD_FEEDBACK: user_input[
                            CONF_ENABLE_KEYPAD_FEEDBACK
                        ],
                        CONF_KEYPAD_ENDPOINT: user_input[CONF_KEYPAD_ENDPOINT],
                        CONF_CODES: codes,
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=self._options_schema(user_input),
            errors=errors,
        )

    def _options_schema(
        self,
        user_input: dict[str, Any] | None,
    ) -> vol.Schema:
        """Build the options schema using saved or submitted values."""
        values = {
            key: self._config_entry.options.get(
                key,
                self._config_entry.data.get(key, default),
            )
            for key, default in (
                (CONF_SENSORS_AWAY, []),
                (CONF_SENSORS_HOME, []),
                (CONF_SENSORS_NIGHT, []),
                (CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY),
                (CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY),
                (CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN),
                (CONF_FRIENT_DEVICE_ID, ""),
                (CONF_ENABLE_KEYPAD_FEEDBACK, False),
                (CONF_KEYPAD_ENDPOINT, DEFAULT_KEYPAD_ENDPOINT),
            )
        }
        values[CONF_CODES_JSON] = json.dumps(
            self._config_entry.options.get(
                CONF_CODES,
                self._config_entry.data.get(CONF_CODES, []),
            ),
            indent=2,
        )
        if user_input is not None:
            values.update(user_input)

        entity_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                multiple=True,
            )
        )
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
                    CONF_SENSORS_AWAY,
                    default=values[CONF_SENSORS_AWAY],
                ): entity_selector,
                vol.Required(
                    CONF_SENSORS_HOME,
                    default=values[CONF_SENSORS_HOME],
                ): entity_selector,
                vol.Required(
                    CONF_SENSORS_NIGHT,
                    default=values[CONF_SENSORS_NIGHT],
                ): entity_selector,
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
        if any(item is not None and not isinstance(item, str) for item in code.values()):
            raise ValueError("Code values must be strings or null")
    return codes
