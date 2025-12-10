"""Select platform for Cover Manager integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .cover import CoverManagerCover


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cover Manager select entities."""
    cover: CoverManagerCover = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        CoverManagerDirection(config_entry, cover),
        CoverManagerLastDirection(config_entry, cover),
    ]
    
    cover.register_sub_entities(
        direction=entities[0],
        last_direction=entities[1],
    )
    
    async_add_entities(entities)


class CoverManagerDirection(SelectEntity):
    """Select entity to adjust direction and last_direction."""

    _attr_options = ["opening", "closing", "idle"]
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_direction_ctl"
        self._attr_name = "Direction"
        self._attr_device_info = cover.device_info

    @property
    def current_option(self) -> str | None:
        return self._cover._direction  # noqa: SLF001

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes including last_direction."""
        return {
            "direction": self._cover._direction,  # noqa: SLF001
            "last_direction": self._cover._last_direction,  # noqa: SLF001
            "description": "Set direction. Last direction is updated automatically when direction changes.",
        }

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            return
        if option == "idle":
            await self._cover.async_stop_cover()
        else:
            await self._cover._go_direction(option)


class CoverManagerLastDirection(SelectEntity):
    """Select entity to adjust/reset last_direction."""

    _attr_options = ["opening", "closing"]
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_last_direction_ctl"
        self._attr_name = "Last Direction"
        self._attr_device_info = cover.device_info

    @property
    def current_option(self) -> str | None:
        return self._cover._last_direction  # noqa: SLF001

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "description": "Reset last_direction value. Used to determine next direction when cover is idle.",
        }

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            return
        self._cover.update_last_direction(option)
