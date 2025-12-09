"""Config flow for Cover Manager integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import DOMAIN

class CoverManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cover Manager."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        default_helpers_path = "config/helpers"
        default_covers_path = "config/covers"

        if user_input is not None:
            try:
                switch_entity = user_input["switch_entity"]
                
                # Validate the switch entity exists and is a switch
                state = self.hass.states.get(switch_entity)
                if not state:
                    raise InvalidSwitchEntity
                
                # Validate the entity domain is switch
                entity_domain = switch_entity.split(".")[0] if "." in switch_entity else None
                if entity_domain != "switch":
                    raise InvalidSwitchEntity

                # Create a unique ID for this cover
                cover_id = user_input["name"].lower().replace(" ", "_")
                await self.async_set_unique_id(f"{DOMAIN}_{cover_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "name": user_input["name"],
                        "switch_entity": user_input["switch_entity"],
                        "travel_time": user_input["travel_time"],
                        "helpers_path": user_input.get("helpers_path", default_helpers_path),
                        "covers_path": user_input.get("covers_path", default_covers_path),
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
                    vol.Optional("helpers_path", default=default_helpers_path): str,
                    vol.Optional("covers_path", default=default_covers_path): str,
                }
            ),
            errors=errors,
        )

class InvalidSwitchEntity(HomeAssistantError):
    """Error to indicate the switch entity is invalid.""" 