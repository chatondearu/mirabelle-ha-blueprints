"""Cover platform for Cover Manager integration (impulse switch, internal state)."""
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
    cover = CoverManagerCover(config_entry)
    # Store cover instance in hass.data for other platforms to access
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][config_entry.entry_id] = cover
    async_add_entities([cover])


class CoverManagerCover(CoverEntity, RestoreEntity):
    """Representation of a Cover Manager cover driven by an impulse switch."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        self._attr_name = config_entry.data["name"]
        self._attr_unique_id = config_entry.entry_id
        self._switch_entity = config_entry.data["switch_entity"]
        self._travel_time = max(1, int(config_entry.data["travel_time"]))
        self._initial_position = max(0, min(100, int(config_entry.data.get("initial_position", 0))))
        self._pulse_gap = max(0.1, min(5.0, float(config_entry.data.get("pulse_gap", 0.8))))
        self._position: float = float(self._initial_position)
        self._direction: str = "idle"  # opening / closing / idle
        self._last_direction: str = "closing"
        self._update_task: Optional[asyncio.Task] = None
        self._movement_start_time: Optional[float] = None
        self._start_position: float = self._position
        self._ignore_next_impulse = False
        self._ignore_until: Optional[float] = None
        self._listener_remove = None
        self._traveltime_entity: Optional[Any] = None
        self._position_entity: Optional[Any] = None
        self._direction_entity: Optional[Any] = None
        self._lastdirection_entity: Optional[Any] = None
        self._pulsegap_entity: Optional[Any] = None
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def device_info(self) -> DeviceInfo:
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
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self._position = float(last_state.attributes.get("position", self._initial_position))
            self._direction = last_state.attributes.get("direction", "idle")
            self._last_direction = last_state.attributes.get("last_direction", "closing")
            # Restore travel time if stored
            if "travel_time" in last_state.attributes:
                self._travel_time = max(1, int(last_state.attributes["travel_time"]))
            # Restore pulse gap if stored
            if "pulse_gap" in last_state.attributes:
                self._pulse_gap = max(0.1, min(5.0, float(last_state.attributes["pulse_gap"])))
        self._listener_remove = async_track_state_change_event(
            self.hass, [self._switch_entity], self._handle_switch_event
        )

    async def async_will_remove_from_hass(self) -> None:
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
            "pulse_gap": self._pulse_gap,
        }

    @property
    def state(self) -> str | None:
        if self.is_opening:
            return STATE_OPENING
        if self.is_closing:
            return STATE_CLOSING
        return STATE_OPEN if self.current_cover_position > 0 else STATE_CLOSED

    @property
    def icon(self) -> str:
        """Return the icon based on state and position."""
        if self._direction == "opening":
            return "mdi:arrow-up-bold"
        if self._direction == "closing":
            return "mdi:arrow-down-bold"
        # Idle state: reflect actual position
        pos = self.current_cover_position
        if pos == 0:
            return "mdi:window-shutter"
        if pos == 100:
            return "mdi:window-shutter-open"
        return "mdi:window-shutter-alert"

    async def _trigger_pulse(self) -> None:
        # Ignore switch events for a bit longer than pulse_gap to account for switch response time
        ignore_duration = self._pulse_gap + 0.5  # Add 0.5s buffer for switch response
        self._ignore_until = time.monotonic() + ignore_duration
        try:
            await self.hass.services.async_call(
                "switch", "turn_on", {"entity_id": self._switch_entity}
            )
            await asyncio.sleep(self._pulse_gap)
        finally:
            # Keep ignoring until the timestamp expires (handled in _handle_switch_event)
            pass

    def _stop_movement(self, update_position: bool = True, cancel_task: bool = True) -> None:
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
        if cancel_task and self._update_task:
            self._update_task.cancel()
            self._update_task = None
        self.async_write_ha_state()
        self._notify_sub_entities()

    async def _stop_and_pulse(self, update_position: bool = True, send_pulse: bool = True) -> None:
        """Stop movement, update position if requested, and optionally send a pulse to stop physically."""
        self._stop_movement(update_position=update_position, cancel_task=False)
        if send_pulse:
            await self._trigger_pulse()

    async def _movement_loop(self) -> None:
        try:
            while self._direction in ("opening", "closing"):
                now = time.monotonic()
                elapsed = now - (self._movement_start_time or now)
                delta = (elapsed / self._travel_time) * 100
                if self._direction == "opening":
                    self._position = min(100.0, self._start_position + delta)
                else:
                    self._position = max(0.0, self._start_position - delta)

                if self._position <= 0.0 or self._position >= 100.0:
                    # At natural limit, no pulse needed - cover stops physically by itself
                    self._stop_movement(update_position=False, cancel_task=False)
                    break

                self.async_write_ha_state()
                self._notify_sub_entities()
                await asyncio.sleep(TICK_SECONDS)
        except asyncio.CancelledError:
            return

    def _start_movement(self, direction: str) -> None:
        self._stop_movement(update_position=True)
        self._direction = direction
        self._last_direction = direction
        self._start_position = self._position
        self._movement_start_time = time.monotonic()
        self._update_task = asyncio.create_task(self._movement_loop())
        self.async_write_ha_state()
        self._notify_sub_entities()

    @callback
    def _handle_switch_event(self, event) -> None:
        """Handle physical switch activation - always follow manual actions."""
        new_state = event.data.get("new_state")
        if not new_state or new_state.state != "on":
            return
        
        # Ignore if this is our own automatic pulse (within ignore window)
        if self._ignore_until is not None:
            if time.monotonic() < self._ignore_until:
                return
            # Window expired, reset
            self._ignore_until = None
        
        # If cover is moving, stop it (physical switch toggles direction)
        if self._direction in ("opening", "closing"):
            self._stop_movement(update_position=True)
            return

        # Cover is idle - determine direction based on position and last direction
        if self._position <= 0.0:
            # At bottom, must go up
            dir_to_start = "opening"
        elif self._position >= 100.0:
            # At top, must go down
            dir_to_start = "closing"
        else:
            # In between, toggle direction
            dir_to_start = "opening" if self._last_direction == "closing" else "closing"

        self._start_movement(dir_to_start)

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._go_direction("opening")

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._go_direction("closing")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        # If already stopped, do nothing
        if self._direction == "idle":
            return
        await self._stop_and_pulse(update_position=True)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        target = max(0, min(100, int(kwargs[ATTR_POSITION])))
        if target == self.current_cover_position:
            return
        
        # Calculate required direction based on current position
        required_direction = "opening" if target > self.current_cover_position else "closing"
        
        # Check current state
        was_moving = self._direction in ("opening", "closing")
        current_direction = self._direction if was_moving else None
        previous_direction = self._last_direction if was_moving else None
        
        # If we're already moving in the required direction, just update the target
        # No need to stop or send any pulses - just update the target position
        if was_moving and current_direction == required_direction:
            # Same direction: just update target, no need to stop or change direction
            if self._update_task:
                self._update_task.cancel()
            # Update position based on elapsed time
            if self._movement_start_time:
                elapsed = time.monotonic() - self._movement_start_time
                delta = (elapsed / self._travel_time) * 100
                if current_direction == "opening":
                    self._position = min(100.0, self._start_position + delta)
                else:
                    self._position = max(0.0, self._start_position - delta)
            # Restart movement with new target from current position
            self._start_position = self._position
            self._movement_start_time = time.monotonic()
            # Continue movement in same direction, just with new target - NO PULSE
            await self._start_targeted_movement(required_direction, target)
            return
        
        # Need to stop current movement and change direction
        self._stop_movement(update_position=True)
        
        # Now check if we need to change direction
        if was_moving and previous_direction != required_direction:
            # Was moving in opposite direction: send a pulse to stop, then go in new direction
            await self._trigger_pulse()  # Stop current motion
            await self._go_direction(required_direction, target=target, skip_stop_pulse=True)
        elif not was_moving and self._last_direction != required_direction:
            # Cover is idle but last_direction doesn't match required direction
            # Need to send pulses to align the switch state with required direction
            # Pulse 1: starts in opposite direction (switch inverts from last_direction)
            await self._trigger_pulse()  # First pulse: starts in opposite direction (switch inverts)
            # Update last_direction to reflect the switch state after first pulse
            self._last_direction = "opening" if self._last_direction == "closing" else "closing"
            # Pulse 2: stops and inverts to correct direction
            await self._trigger_pulse()  # Second pulse: stops and inverts to correct direction
            # Now last_direction matches required_direction, update it
            self._last_direction = required_direction
            # Pulse 3: starts in correct direction (handled by _go_direction)
            await self._go_direction(required_direction, target=target, skip_stop_pulse=True)
        else:
            # Was idle and last_direction matches, or need to start: just go in the required direction
            await self._go_direction(required_direction, target=target)

    # Sub-entity hooks
    def register_sub_entities(
        self,
        travel: Any = None,
        position: Any = None,
        direction: Any = None,
        last_direction: Any = None,
        pulse_gap: Any = None,
    ) -> None:
        if travel is not None:
            self._traveltime_entity = travel
        if position is not None:
            self._position_entity = position
        if direction is not None:
            self._direction_entity = direction
        if last_direction is not None:
            self._lastdirection_entity = last_direction
        if pulse_gap is not None:
            self._pulsegap_entity = pulse_gap

    def _notify_sub_entities(self) -> None:
        for ent in (self._traveltime_entity, self._position_entity, self._direction_entity, self._lastdirection_entity, self._pulsegap_entity):
            if ent:
                ent.schedule_update_ha_state()

    def update_travel_time(self, new_time: int) -> None:
        self._travel_time = max(1, int(new_time))
        self._notify_sub_entities()

    def update_position(self, new_pos: float) -> None:
        self._position = max(0.0, min(100.0, float(new_pos)))
        self._stop_movement(update_position=False)
        self.async_write_ha_state()
        self._notify_sub_entities()

    def update_direction(self, new_dir: str) -> None:
        if new_dir not in ("opening", "closing", "idle"):
            return
        self._direction = new_dir
        if new_dir != "idle":
            self._last_direction = new_dir
        self.async_write_ha_state()
        self._notify_sub_entities()

    def update_last_direction(self, new_last_dir: str) -> None:
        """Update last_direction without affecting current direction."""
        if new_last_dir not in ("opening", "closing"):
            return
        self._last_direction = new_last_dir
        self.async_write_ha_state()
        self._notify_sub_entities()

    def update_pulse_gap(self, new_gap: float) -> None:
        self._pulse_gap = max(0.1, min(5.0, float(new_gap)))
        self.async_write_ha_state()
        self._notify_sub_entities()

    async def _go_direction(self, direction: str, target: Optional[int] = None, skip_stop_pulse: bool = False) -> None:
        """Handle direction change with impulse switch (may require two pulses)."""
        # If already in desired direction and moving, update target if needed
        if self._direction == direction:
            # If we have a target and we're already moving, update the target
            if target is not None:
                # Cancel current task and restart with new target
                if self._update_task:
                    self._update_task.cancel()
                # Continue to start new movement below
            else:
                # No target change, already moving in right direction
                return

        # If moving opposite direction and not already stopped, stop and send a pulse
        if self._direction in ("opening", "closing") and self._direction != direction and not skip_stop_pulse:
            self._stop_movement(update_position=True)
            await self._trigger_pulse()  # first pulse stops current motion physically

        # Start movement in target direction
        self._position = float(self.current_cover_position)
        self._start_position = self._position
        self._movement_start_time = time.monotonic()
        self._direction = direction
        self._last_direction = direction

        # Start the movement task
        await self._start_targeted_movement(direction, target)

        # Send pulse to start motion in the new direction
        # This is needed when direction changes or when starting from idle
        await self._trigger_pulse()

    async def _start_targeted_movement(self, direction: str, target: Optional[int]) -> None:
        """Start movement with optional target position."""
        async def _move_with_target():
            try:
                if target is None:
                    # free run until bound
                    await self._movement_loop()
                    return
                remaining = abs(target - self._position)
                if remaining == 0:
                    self._stop_movement(update_position=False, cancel_task=False)
                    return
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
                        await self._stop_and_pulse(update_position=False)
                        break
                    self.async_write_ha_state()
                    self._notify_sub_entities()
                    await asyncio.sleep(TICK_SECONDS)
            except asyncio.CancelledError:
                return

        if self._update_task:
            self._update_task.cancel()
        # Kick off the movement (bound or targeted)
        if target is None:
            self._update_task = asyncio.create_task(self._movement_loop())
        else:
            self._update_task = asyncio.create_task(_move_with_target())

        # Send pulse to start motion (only if direction was changed, not if just updating target)
        # This is handled in _go_direction, so we don't send pulse here if called from async_set_cover_position
        # with same direction