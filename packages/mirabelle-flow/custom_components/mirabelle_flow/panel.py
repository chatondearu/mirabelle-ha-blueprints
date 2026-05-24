"""Sidebar panel for Mirabelle Flow."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_ICON, PANEL_TITLE

_LOGGER = logging.getLogger(__name__)
PANEL_NAME = f"{DOMAIN}-panel"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Mirabelle Flow custom panel."""
    www_path = Path(__file__).parent / "www"

    if not www_path.exists():
        _LOGGER.warning(
            "Mirabelle Flow www/ not found — run pnpm run build:flow:ha from the monorepo"
        )
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig("/mirabelle-flow", str(www_path), False)]
    )

    wrapper_path = www_path / "assets" / "panel-wrapper.js"
    if not wrapper_path.exists():
        index_assets = list((www_path / "assets").glob("index-*.js"))
        if index_assets:
            module_url = f"/mirabelle-flow/assets/{index_assets[0].name}?v={int(time.time())}"
        else:
            _LOGGER.error("No frontend bundle in %s", www_path)
            return
    else:
        module_url = f"/mirabelle-flow/assets/panel-wrapper.js?v={int(time.time())}"

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_NAME,
        frontend_url_path=DOMAIN,
        module_url=module_url,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=True,
        config={},
        config_panel_domain=DOMAIN,
    )
    _LOGGER.info("Mirabelle Flow panel registered")


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the Mirabelle Flow panel."""
    frontend.async_remove_panel(hass, DOMAIN)
