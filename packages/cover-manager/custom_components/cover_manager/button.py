"""Button platform for Cover Manager integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .cover import CoverManagerCover


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cover Manager button entities."""
    cover: CoverManagerCover = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([CoverManagerResetPositionButton(config_entry, cover)])


class CoverManagerResetPositionButton(ButtonEntity):
    """Button to reset internal cover position state."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:restore"

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_reset_position"
        self._attr_name = "Reset Position"
        self._attr_device_info = cover.device_info

    async def async_press(self) -> None:
        """Handle button press."""
        self._cover.reset_position_state()
