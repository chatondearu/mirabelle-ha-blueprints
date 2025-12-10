"""Cover platform for Cover Manager integration (impulse switch, no templates/helpers)."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_CLOSED, STATE_OPEN, STATE_OPENING, STATE_CLOSING
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TICK_SECONDS = 0.3


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cover Manager cover."""
    async_add_entities([CoverManagerCover(config_entry)])


class CoverManagerCover(CoverEntity, RestoreEntity):
    """Representation of a Cover Manager cover driven by an impulse switch."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the cover."""
        self.config_entry = config_entry
        self._attr_name = config_entry.data["name"]
        self._attr_unique_id = config_entry.entry_id
        self._switch_entity = config_entry.data["switch_entity"]
        self._travel_time = max(1, int(config_entry.data["travel_time"]))
        self._initial_position = max(0, min(100, int(config_entry.data.get("initial_position", 0))))
        self._position: float = float(self._initial_position)
        self._direction: str = "idle"  # opening / closing / idle
        self._last_direction: str = "closing"
        self._update_task: Optional[asyncio.Task] = None
        self._movement_start_time: Optional[float] = None
        self._start_position: float = 0.0
        self._ignore_next_impulse = False
        self._listener_remove = None
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=self._attr_name,
            manufacturer="Cover Manager",
            model="Impulse Cover",
        )

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self) -> None:
        """Restore state and listen for switch impulses."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self._position = float(last_state.attributes.get("position", 0.0))
            self._direction = last_state.attributes.get("direction", "idle")
            self._last_direction = last_state.attributes.get("last_direction", "closing")
        else:
            self._position = float(self._initial_position)
            self._direction = "idle"

        self._listener_remove = async_track_state_change_event(
            self.hass, [self._switch_entity], self._handle_switch_event
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners and tasks."""
        if self._listener_remove:
            self._listener_remove()
        if self._update_task:
            self._update_task.cancel()

    @property
    def current_cover_position(self) -> int:
        return int(round(self._position))

    @property
    def is_closed(self) -> bool:
        return self.current_cover_position == 0

    @property
    def is_opening(self) -> bool:
        return self._direction == "opening"

    @property
    def is_closing(self) -> bool:
        return self._direction == "closing"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "position": round(self._position, 1),
            "direction": self._direction,
            "last_direction": self._last_direction,
            "travel_time": self._travel_time,
        }

    @property
    def state(self) -> str | None:
        if self.is_opening:
            return STATE_OPENING
        if self.is_closing:
            return STATE_CLOSING
        return STATE_OPEN if self.current_cover_position > 0 else STATE_CLOSED

    async def _trigger_pulse(self) -> None:
        """Send an impulse to the switch."""
        self._ignore_next_impulse = True
        try:
            await self.hass.services.async_call(
                "switch", "turn_on", {"entity_id": self._switch_entity}
            )
            await asyncio.sleep(1)
        finally:
            # allow next physical change to be handled
            self._ignore_next_impulse = False

    def _stop_movement(self, update_position: bool = True) -> None:
        """Stop movement and optionally update position based on elapsed time."""
        if self._direction in ("opening", "closing") and self._movement_start_time and update_position:
            elapsed = time.monotonic() - self._movement_start_time
            delta = (elapsed / self._travel_time) * 100
            if self._direction == "opening":
                self._position = min(100.0, self._start_position + delta)
            else:
                self._position = max(0.0, self._start_position - delta)
        self._direction = "idle"
        self._movement_start_time = None
        self._start_position = self._position
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None
        self.async_write_ha_state()

    async def _movement_loop(self) -> None:
        """Periodic update of position based on time and direction."""
        try:
            while self._direction in ("opening", "closing"):
                now = time.monotonic()
                elapsed = now - (self._movement_start_time or now)
                delta = (elapsed / self._travel_time) * 100
                if self._direction == "opening":
                    self._position = min(100.0, self._start_position + delta)
                else:
                    self._position = max(0.0, self._start_position - delta)

                # Stop at bounds
                if self._position <= 0.0 or self._position >= 100.0:
                    self._stop_movement(update_position=False)
                    break

                self.async_write_ha_state()
                await asyncio.sleep(TICK_SECONDS)
        except asyncio.CancelledError:
            return

    def _start_movement(self, direction: str) -> None:
        """Start movement in a given direction."""
        self._stop_movement(update_position=True)
        self._direction = direction
        self._last_direction = direction
        self._start_position = self._position
        self._movement_start_time = time.monotonic()
        self._update_task = asyncio.create_task(self._movement_loop())
        self.async_write_ha_state()

    @callback
    def _handle_switch_event(self, event) -> None:
        """Handle physical switch impulse (state change)."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if not new_state or new_state.state != "on":
            return
        if self._ignore_next_impulse:
            return
        # Physical impulse: toggle behaviour with stop then reverse
        if self._direction in ("opening", "closing"):
            self._stop_movement(update_position=True)
            return

        # Idle: decide direction
        if self._position <= 0.0:
            dir_to_start = "opening"
        elif self._position >= 100.0:
            dir_to_start = "closing"
        else:
            dir_to_start = "opening" if self._last_direction == "closing" else "closing"

        self._start_movement(dir_to_start)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self._direction == "opening":
            return
        self._start_movement("opening")
        await self._trigger_pulse()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if self._direction == "closing":
            return
        self._start_movement("closing")
        await self._trigger_pulse()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        self._stop_movement(update_position=True)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover position."""
        target = max(0, min(100, int(kwargs[ATTR_POSITION])))
        self._stop_movement(update_position=True)
        if target == self.current_cover_position:
            return
        direction = "opening" if target > self.current_cover_position else "closing"
        self._position = float(self.current_cover_position)
        self._start_position = self._position
        self._movement_start_time = time.monotonic()
        # Adjust travel_time fraction to stop early
        remaining = abs(target - self._position)
        if remaining == 0:
            return
        self._direction = direction
        self._last_direction = direction

        async def _move_to_target():
            try:
                start_time = time.monotonic()
                total_duration = self._travel_time * (remaining / 100)
                while self._direction == direction:
                    elapsed = time.monotonic() - start_time
                    progress = min(1.0, elapsed / total_duration)
                    if direction == "opening":
                        self._position = self._start_position + remaining * progress
                    else:
                        self._position = self._start_position - remaining * progress
                    if progress >= 1.0:
                        self._stop_movement(update_position=False)
                        break
                    self.async_write_ha_state()
                    await asyncio.sleep(TICK_SECONDS)
            except asyncio.CancelledError:
                return

        # Cancel any previous update loop and start targeted move
        if self._update_task:
            self._update_task.cancel()
        self._update_task = asyncio.create_task(_move_to_target())
        await self._trigger_pulse()