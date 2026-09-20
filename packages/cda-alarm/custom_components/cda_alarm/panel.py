"""Sidebar panel registration for CDA Alarm."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DATA_PANEL_REGISTERED, DOMAIN, FRONTEND_URL_BASE, PANEL_URL_PATH

_FRONTEND_DIR = Path(__file__).parent / "frontend"


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Serve frontend assets and register the CDA Alarm sidebar panel once."""
    if hass.data.get(DATA_PANEL_REGISTERED):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL_BASE,
                str(_FRONTEND_DIR),
                cache_headers=False,
            )
        ]
    )

    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name="cda-alarm-panel",
        sidebar_title="CDA Alarm",
        sidebar_icon="mdi:shield-home",
        module_url=f"{FRONTEND_URL_BASE}/cda-alarm-panel.js",
        embed_iframe=False,
        require_admin=False,
        config={"entry_domain": DOMAIN},
    )
    hass.data[DATA_PANEL_REGISTERED] = True
