"""Config flow for Cover Manager integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import DOMAIN

class CoverManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cover Manager."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                switch_entity = user_input["switch_entity"]
                
                state = self.hass.states.get(switch_entity)
                if not state:
                    raise InvalidSwitchEntity
                
                entity_domain = switch_entity.split(".")[0] if "." in switch_entity else None
                if entity_domain != "switch":
                    raise InvalidSwitchEntity

                cover_id = user_input["name"].lower().replace(" ", "_")
                await self.async_set_unique_id(f"{DOMAIN}_{cover_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "name": user_input["name"],
                        "switch_entity": user_input["switch_entity"],
                        "travel_time": user_input["travel_time"],
                        "initial_position": user_input["initial_position"],
                        "pulse_gap": user_input.get("pulse_gap", 0.8),
                        "acceleration_duration": user_input.get("acceleration_duration", 0.0),
                    },
                )
            except InvalidSwitchEntity:
                errors["base"] = "invalid_switch_entity"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("switch_entity"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch")
                    ),
                    vol.Required("travel_time", default=30): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=300)
                    ),
                    vol.Optional("initial_position", default=0): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=100, step=1, mode="box")
                    ),
                    vol.Optional("pulse_gap", default=0.8): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0.1, max=5.0, step=0.1, mode="box", unit_of_measurement="s")
                    ),
                    vol.Optional("acceleration_duration", default=0.0): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0.0, max=30.0, step=0.1, mode="box", unit_of_measurement="s")
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return CoverManagerOptionsFlow(config_entry)


class CoverManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Cover Manager."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage integration options."""
        errors = {}

        if user_input is not None:
            try:
                switch_entity = user_input["switch_entity"]
                state = self.hass.states.get(switch_entity)
                if not state:
                    raise InvalidSwitchEntity

                entity_domain = switch_entity.split(".")[0] if "." in switch_entity else None
                if entity_domain != "switch":
                    raise InvalidSwitchEntity

                return self.async_create_entry(
                    title="",
                    data={
                        "switch_entity": switch_entity,
                        "acceleration_duration": user_input.get("acceleration_duration", 0.0),
                    },
                )
            except InvalidSwitchEntity:
                errors["base"] = "invalid_switch_entity"

        current_switch = self._config_entry.options.get(
            "switch_entity",
            self._config_entry.data["switch_entity"],
        )
        current_acceleration_duration = self._config_entry.options.get(
            "acceleration_duration",
            self._config_entry.data.get("acceleration_duration", 0.0),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("switch_entity", default=current_switch): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch")
                    ),
                    vol.Optional(
                        "acceleration_duration",
                        default=current_acceleration_duration,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.0,
                            max=30.0,
                            step=0.1,
                            mode="box",
                            unit_of_measurement="s",
                        )
                    ),
                }
            ),
            errors=errors,
        )

class InvalidSwitchEntity(HomeAssistantError):
    """Error to indicate the switch entity is invalid.""" 