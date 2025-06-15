"""Config flow for Cover Manager integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

class CoverManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cover Manager."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the switch entity exists
                if not self.hass.states.get(user_input["switch_entity"]):
                    raise InvalidSwitchEntity

                # Create a unique ID for this cover
                cover_id = user_input["name"].lower().replace(" ", "_")
                await self.async_set_unique_id(f"{DOMAIN}_{cover_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input,
                )
            except InvalidSwitchEntity:
                errors["base"] = "invalid_switch_entity"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("switch_entity"): str,
                    vol.Required("travel_time", default=30): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=300)
                    ),
                }
            ),
            errors=errors,
        )

class InvalidSwitchEntity(HomeAssistantError):
    """Error to indicate the switch entity is invalid.""" 