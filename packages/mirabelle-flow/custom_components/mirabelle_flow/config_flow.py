"""Config flow for Mirabelle Flow."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class MirabelleFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mirabelle Flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create entry without extra credentials (uses HA session in panel)."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Mirabelle Flow", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow."""
        return MirabelleFlowOptionsFlow(config_entry)


class MirabelleFlowOptionsFlow(config_entries.OptionsFlow):
    """Options flow placeholder."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        return self.async_create_entry(title="", data=self.config_entry.options)
