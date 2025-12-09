"""Cover platform for Cover Manager integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cover Manager cover."""
    async_add_entities([CoverManagerCover(config_entry)])

class CoverManagerCover(CoverEntity, RestoreEntity):
    """Representation of a Cover Manager cover."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the cover."""
        self.config_entry = config_entry
        self._attr_name = config_entry.data["name"]
        self._attr_unique_id = config_entry.entry_id
        self._switch_entity = config_entry.data["switch_entity"]
        self._travel_time = config_entry.data["travel_time"]
        # Use same format as in __init__.py for consistency
        cover_id = config_entry.data["name"].lower().replace(" ", "_")
        self._position_helper = f"input_text.{cover_id}_position"
        self._direction_helper = f"input_text.{cover_id}_direction"
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        self._helpers_warning_shown = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=self._attr_name,
            manufacturer="Cover Manager",
            model="Template Cover",
        )

    def _safe_state(self, entity_id: str, default: Any) -> Any:
        """Return state string or default if missing."""
        state_obj = self.hass.states.get(entity_id)
        return state_obj.state if state_obj else default

    def _ensure_helpers(self) -> bool:
        """Check helpers exist; log once if missing."""
        pos_ok = self.hass.states.get(self._position_helper) is not None
        dir_ok = self.hass.states.get(self._direction_helper) is not None
        if not (pos_ok and dir_ok) and not self._helpers_warning_shown:
            _LOGGER.warning(
                "Helpers missing for %s. Ensure input_text helpers exist for position (%s) and direction (%s).",
                self._attr_name,
                self._position_helper,
                self._direction_helper,
            )
            self._helpers_warning_shown = True
        return pos_ok and dir_ok

    @property
    def current_cover_position(self) -> int:
        """Return the current position of the cover."""
        try:
            return int(self._safe_state(self._position_helper, 0))
        except (TypeError, ValueError):
            return 0

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self.current_cover_position == 0

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        return self._safe_state(self._direction_helper, "stopped") == "opening"

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return self._safe_state(self._direction_helper, "stopped") == "closing"

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if not self._ensure_helpers():
            return
        await self.hass.services.async_call(
            "script",
            "set_cover_position",
            {
                "cover_switch": self._switch_entity,
                "position": 100,
                "travel_time": self._travel_time,
                "last_state": self._position_helper,
            },
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if not self._ensure_helpers():
            return
        await self.hass.services.async_call(
            "script",
            "set_cover_position",
            {
                "cover_switch": self._switch_entity,
                "position": 0,
                "travel_time": self._travel_time,
                "last_state": self._position_helper,
            },
        )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        if not self._ensure_helpers():
            return
        await self.hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": self._switch_entity},
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover position."""
        if not self._ensure_helpers():
            return
        position = kwargs[ATTR_POSITION]
        await self.hass.services.async_call(
            "script",
            "set_cover_position",
            {
                "cover_switch": self._switch_entity,
                "position": position,
                "travel_time": self._travel_time,
                "last_state": self._position_helper,
            },
        ) 