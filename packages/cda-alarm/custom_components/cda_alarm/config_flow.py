"""Config and options flows for CDA Alarm."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .access import normalize_access
from .const import (
    CONF_ACCESS,
    CONF_BLOCK_ARM_IF_OPEN,
    CONF_CAMERAS,
    CONF_CODES,
    CONF_ENABLE_KEYPAD_FEEDBACK,
    CONF_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    CONF_FRIENT_DEVICE_ID,
    CONF_KEYPAD_ENDPOINT,
    CONF_KEYPADS,
    CONF_NAME,
    CONF_RESPONSE,
    CONF_SENSOR_ASSIGNMENTS,
    CONF_SENSOR_CAMERA_MAP,
    CONF_SENSORS_AWAY,
    CONF_SENSORS_HOME,
    CONF_SENSORS_NIGHT,
    DEFAULT_BLOCK_ARM_IF_OPEN,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DEFAULT_KEYPAD_ENDPOINT,
    DOMAIN,
    PANEL_URL_PATH,
)
from .response import normalize_response
from .sensors import merge_runtime_config


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
                    CONF_KEYPADS: [],
                    CONF_RESPONSE: normalize_response(None),
                    CONF_CAMERAS: [],
                    CONF_SENSOR_CAMERA_MAP: {},
                    CONF_ACCESS: normalize_access(None),
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
    """Thin options flow that points users to the sidebar panel."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Show a redirect note; saving keeps the current options unchanged."""
        if user_input is not None:
            merged = merge_runtime_config(
                {**self.config_entry.data, **self.config_entry.options}
            )
            return self.async_create_entry(
                title="",
                data={
                    CONF_SENSOR_ASSIGNMENTS: merged.get(CONF_SENSOR_ASSIGNMENTS, []),
                    CONF_SENSORS_AWAY: merged.get(CONF_SENSORS_AWAY, []),
                    CONF_SENSORS_HOME: merged.get(CONF_SENSORS_HOME, []),
                    CONF_SENSORS_NIGHT: merged.get(CONF_SENSORS_NIGHT, []),
                    CONF_ENTRY_DELAY: merged.get(CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY),
                    CONF_EXIT_DELAY: merged.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY),
                    CONF_BLOCK_ARM_IF_OPEN: merged.get(
                        CONF_BLOCK_ARM_IF_OPEN, DEFAULT_BLOCK_ARM_IF_OPEN
                    ),
                    CONF_CODES: merged.get(CONF_CODES, []),
                    CONF_KEYPADS: merged.get(CONF_KEYPADS, []),
                    CONF_RESPONSE: merged.get(CONF_RESPONSE, normalize_response(None)),
                    CONF_FRIENT_DEVICE_ID: merged.get(CONF_FRIENT_DEVICE_ID, ""),
                    CONF_ENABLE_KEYPAD_FEEDBACK: merged.get(
                        CONF_ENABLE_KEYPAD_FEEDBACK, False
                    ),
                    CONF_KEYPAD_ENDPOINT: merged.get(
                        CONF_KEYPAD_ENDPOINT, DEFAULT_KEYPAD_ENDPOINT
                    ),
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={
                "panel_path": f"/{PANEL_URL_PATH}",
                "panel_name": "CDA Alarm",
            },
        )
