"""Config flow registration; user-facing flow steps are implemented in Task 3."""

from homeassistant import config_entries

from .const import DOMAIN


class CdaAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Register CDA Alarm config entries."""

    VERSION = 1
