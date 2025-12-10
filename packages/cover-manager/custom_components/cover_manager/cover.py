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

from .const import (
    DOMAIN,
    DIRECTION_IDLE,
    DIRECTION_OPENING,
    DIRECTION_CLOSING,
    POSITION_MIN,
    POSITION_MAX,
)

_LOGGER = logging.getLogger(__name__)
TICK_SECONDS = 0.3
LIMIT_STOP_IGNORE_DURATION = 2.0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cover Manager cover."""
    cover = CoverManagerCover(config_entry)
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
        self._initial_position = self._clamp_position(float(config_entry.data.get("initial_position", 0)))
        self._pulse_gap = max(0.1, min(5.0, float(config_entry.data.get("pulse_gap", 0.8))))
        self._position: float = float(self._initial_position)
        self._direction: str = DIRECTION_IDLE
        self._last_direction: str = DIRECTION_CLOSING
        self._update_task: Optional[asyncio.Task] = None
        self._movement_start_time: Optional[float] = None
        self._start_position: float = self._position
        self._ignore_until: Optional[float] = None
        self._last_limit_stop_time: Optional[float] = None
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

    def _is_at_limit(self) -> bool:
        """Check if cover is at position limit (0% or 100%)."""
        return self._position <= POSITION_MIN or self._position >= POSITION_MAX

    def _clamp_position(self, value: float) -> float:
        """Clamp position value between 0 and 100."""
        return max(POSITION_MIN, min(POSITION_MAX, float(value)))

    def _calculate_position_from_elapsed(
        self, direction: str, start_time: Optional[float], start_pos: float
    ) -> float:
        """Calculate current position based on elapsed time and direction."""
        if start_time is None:
            return start_pos
        elapsed = time.monotonic() - start_time
        delta = (elapsed / self._travel_time) * 100
        if direction == DIRECTION_OPENING:
            return self._clamp_position(start_pos + delta)
        return self._clamp_position(start_pos - delta)

    def _calculate_position_from_progress(
        self, direction: str, start_pos: float, remaining: float, progress: float
    ) -> float:
        """Calculate position based on progress (0.0 to 1.0) for targeted movement."""
        if direction == DIRECTION_OPENING:
            return self._clamp_position(start_pos + (remaining * progress))
        return self._clamp_position(start_pos - (remaining * progress))

    def _initialize_movement_state(self) -> None:
        """Initialize movement state variables."""
        self._position = float(self.current_cover_position)
        self._start_position = self._position
        self._movement_start_time = time.monotonic()
        self._last_limit_stop_time = None

    def _cancel_and_create_task(self, coro) -> None:
        """Cancel existing update task and create a new one."""
        if self._update_task:
            self._update_task.cancel()
        self._update_task = asyncio.create_task(coro)

    def _determine_direction_from_position(self) -> str:
        """Determine direction to start based on current position and last direction."""
        if self._position <= POSITION_MIN:
            return DIRECTION_OPENING
        if self._position >= POSITION_MAX:
            return DIRECTION_CLOSING
        return DIRECTION_OPENING if self._last_direction == DIRECTION_CLOSING else DIRECTION_CLOSING

    def _update_and_notify(self, notify_sub_entities: bool = True) -> None:
        """Update HA state and optionally notify dynamic sub-entities."""
        self.async_write_ha_state()
        if notify_sub_entities:
            self._notify_dynamic_entities()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state:
            self._position = float(last_state.attributes.get("position", self._initial_position))
            self._direction = last_state.attributes.get("direction", DIRECTION_IDLE)
            self._last_direction = last_state.attributes.get("last_direction", DIRECTION_CLOSING)
            if "travel_time" in last_state.attributes:
                self._travel_time = max(1, int(last_state.attributes["travel_time"]))
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
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    @property
    def current_cover_position(self) -> int:
        return int(round(self._position))

    @property
    def is_closed(self) -> bool:
        return self.current_cover_position == 0

    @property
    def is_opening(self) -> bool:
        return self._direction == DIRECTION_OPENING

    @property
    def is_closing(self) -> bool:
        return self._direction == DIRECTION_CLOSING

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
        if self._direction == DIRECTION_OPENING:
            return "mdi:arrow-up-bold"
        if self._direction == DIRECTION_CLOSING:
            return "mdi:arrow-down-bold"
        pos = self.current_cover_position
        if pos == 0:
            return "mdi:window-shutter"
        if pos == 100:
            return "mdi:window-shutter-open"
        return "mdi:window-shutter-alert"

    async def _trigger_pulse(self) -> None:
        ignore_duration = self._pulse_gap + 0.5
        self._ignore_until = time.monotonic() + ignore_duration
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self._switch_entity}
        )
        await asyncio.sleep(self._pulse_gap)

    def _stop_movement(self, update_position: bool = True, cancel_task: bool = True) -> None:
        """Stop movement internally (no pulse). For physical stop, use async_stop_cover or _stop_and_pulse."""
        if self._direction in (DIRECTION_OPENING, DIRECTION_CLOSING) and self._movement_start_time and update_position:
            self._position = self._calculate_position_from_elapsed(
                self._direction, self._movement_start_time, self._start_position
            )
        self._direction = DIRECTION_IDLE
        self._movement_start_time = None
        self._start_position = self._position
        if cancel_task and self._update_task:
            self._update_task.cancel()
            self._update_task = None
        self._update_and_notify()

    async def _stop_and_pulse(self, update_position: bool = True, send_pulse: bool = True) -> None:
        """
        Stop movement and optionally send pulse.
        According to specification: when reaching target (not at limit), send 1 pulse to stop.
        When at limit naturally, DO NOT send pulse.
        """
        at_limit = self._is_at_limit()
        previous_direction = self._direction
        self._stop_movement(update_position=update_position, cancel_task=False)
        self._last_direction = previous_direction
        if send_pulse and not at_limit:
            await self._trigger_pulse()
        if at_limit:
            self._last_limit_stop_time = time.monotonic()
        self._update_and_notify()

    async def _movement_loop(self) -> None:
        try:
            while self._direction in (DIRECTION_OPENING, DIRECTION_CLOSING):
                self._position = self._calculate_position_from_elapsed(
                    self._direction, self._movement_start_time, self._start_position
                )

                if self._is_at_limit():
                    self._last_limit_stop_time = time.monotonic()
                    previous_direction = self._direction
                    self._stop_movement(update_position=False, cancel_task=False)
                    self._last_direction = previous_direction
                    self._update_and_notify()
                    break

                self.async_write_ha_state()
                await asyncio.sleep(TICK_SECONDS)
        except asyncio.CancelledError:
            return

    def _start_movement(self, direction: str) -> None:
        """Start movement in given direction (internal method, no pulse)."""
        was_moving = self._direction in (DIRECTION_OPENING, DIRECTION_CLOSING)
        if was_moving and self._movement_start_time:
            self._position = self._calculate_position_from_elapsed(
                self._direction, self._movement_start_time, self._start_position
            )
        self._direction = DIRECTION_IDLE
        self._movement_start_time = None
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None
        
        self._direction = direction
        self._last_direction = direction
        self._initialize_movement_state()
        self._cancel_and_create_task(self._movement_loop())
        self._update_and_notify()

    @callback
    def _handle_switch_event(self, event) -> None:
        """Handle physical switch activation - always follow manual actions."""
        new_state = event.data.get("new_state")
        if not new_state or new_state.state != "on":
            return
        
        if self._ignore_until is not None:
            if time.monotonic() < self._ignore_until:
                return
            self._ignore_until = None
        
        if self._last_limit_stop_time is not None:
            time_since_limit_stop = time.monotonic() - self._last_limit_stop_time
            if time_since_limit_stop < LIMIT_STOP_IGNORE_DURATION and self._is_at_limit():
                self._last_limit_stop_time = None
                return
        
        if self._direction in (DIRECTION_OPENING, DIRECTION_CLOSING):
            if self._movement_start_time:
                self._position = self._calculate_position_from_elapsed(
                    self._direction, self._movement_start_time, self._start_position
                )
            previous_direction = self._direction
            self._stop_movement(update_position=False)
            self._last_direction = previous_direction
            self._update_and_notify()
            return

        dir_to_start = self._determine_direction_from_position()
        self._last_direction = dir_to_start
        self._start_movement(dir_to_start)

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._go_direction(DIRECTION_OPENING)

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._go_direction(DIRECTION_CLOSING)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop cover movement. According to specification: send 1 pulse to stop."""
        if self._direction == DIRECTION_IDLE:
            return
        if self._movement_start_time:
            self._position = self._calculate_position_from_elapsed(
                self._direction, self._movement_start_time, self._start_position
            )
        previous_direction = self._direction
        self._stop_movement(update_position=False)
        self._last_direction = previous_direction
        await self._trigger_pulse()
        self._update_and_notify()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """
        Set cover to target position.
        According to specification:
        - If moving in same direction: update target (no pulse)
        - If moving in opposite direction: stop (1 pulse), then start (1 pulse)
        - If idle and last_direction = desired: 3 pulses
        - If idle and last_direction ≠ desired: 1 pulse
        - Special cases: at 0% last_direction must be closing, at 100% must be opening
        """
        target = int(self._clamp_position(float(kwargs[ATTR_POSITION])))
        if target == self.current_cover_position:
            return
        
        if self._direction == DIRECTION_IDLE:
            if self._position == 0.0:
                if self._last_direction != DIRECTION_CLOSING:
                    _LOGGER.warning("Cover at 0% but last_direction is %s, should be closing. Correcting.", self._last_direction)
                    self._last_direction = DIRECTION_CLOSING
            elif self._position == 100.0:
                if self._last_direction != DIRECTION_OPENING:
                    _LOGGER.warning("Cover at 100% but last_direction is %s, should be opening. Correcting.", self._last_direction)
                    self._last_direction = DIRECTION_OPENING
        
        required_direction = DIRECTION_OPENING if target > self.current_cover_position else DIRECTION_CLOSING
        await self._go_direction(required_direction, target=target)

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

    def _notify_dynamic_entities(self) -> None:
        """Notify entities that change during cover operation (position, direction, last_direction)."""
        for ent in (self._position_entity, self._direction_entity, self._lastdirection_entity):
            if ent:
                ent.schedule_update_ha_state()
    
    def _notify_static_entities(self) -> None:
        """Notify entities that only change when user modifies them (travel_time, pulse_gap)."""
        for ent in (self._traveltime_entity, self._pulsegap_entity):
            if ent:
                ent.schedule_update_ha_state()

    def update_travel_time(self, new_time: int) -> None:
        self._travel_time = max(1, int(new_time))
        if self._traveltime_entity:
            self._traveltime_entity.schedule_update_ha_state()

    def update_position(self, new_pos: float) -> None:
        self._position = self._clamp_position(new_pos)
        self._stop_movement(update_position=False)
        self._update_and_notify()

    def update_direction(self, new_dir: str) -> None:
        if new_dir not in (DIRECTION_OPENING, DIRECTION_CLOSING, DIRECTION_IDLE):
            return
        self._direction = new_dir
        if new_dir != DIRECTION_IDLE:
            self._last_direction = new_dir
        self._update_and_notify()

    def update_last_direction(self, new_last_dir: str) -> None:
        """Update last_direction without affecting current direction."""
        if new_last_dir not in (DIRECTION_OPENING, DIRECTION_CLOSING):
            return
        self._last_direction = new_last_dir
        self._update_and_notify()

    def update_pulse_gap(self, new_gap: float) -> None:
        self._pulse_gap = max(0.1, min(5.0, float(new_gap)))
        if self._pulsegap_entity:
            self._pulsegap_entity.schedule_update_ha_state()

    async def _go_direction(self, direction: str, target: Optional[int] = None, skip_stop_pulse: bool = False) -> None:
        """
        Handle direction change with impulse switch.
        According to specification:
        - If already moving in same direction: just update target (no pulse)
        - If moving in opposite direction: stop (1 pulse), then start (1 pulse)
        - If idle and last_direction = desired: 3 pulses (idle→opposite→idle→desired)
        - If idle and last_direction ≠ desired: 1 pulse (idle→desired, which is next in cycle)
        """
        if self._direction == direction:
            if target is not None:
                if self._movement_start_time:
                    self._position = self._calculate_position_from_elapsed(
                        direction, self._movement_start_time, self._start_position
                    )
                self._start_position = self._position
                self._movement_start_time = time.monotonic()
                self._cancel_and_create_task(self._start_targeted_movement(direction, target))
            return

        was_moving = self._direction in (DIRECTION_OPENING, DIRECTION_CLOSING)
        
        if was_moving:
            if not skip_stop_pulse:
                if self._movement_start_time:
                    self._position = self._calculate_position_from_elapsed(
                        self._direction, self._movement_start_time, self._start_position
                    )
                previous_direction = self._direction
                self._stop_movement(update_position=False)
                self._last_direction = previous_direction
                await self._trigger_pulse()
            self._initialize_movement_state()
            self._direction = direction
            self._last_direction = direction
            await self._trigger_pulse()
            await self._start_targeted_movement(direction, target)
        else:
            if self._last_direction == direction:
                opposite = DIRECTION_CLOSING if direction == DIRECTION_OPENING else DIRECTION_OPENING
                await self._trigger_pulse()
                await self._trigger_pulse()
                self._last_direction = opposite
                await self._trigger_pulse()
                self._last_direction = direction
                self._initialize_movement_state()
                self._direction = direction
                await self._start_targeted_movement(direction, target)
            else:
                self._initialize_movement_state()
                self._direction = direction
                self._last_direction = direction
                await self._trigger_pulse()
                await self._start_targeted_movement(direction, target)
        
        self._last_limit_stop_time = None

    async def _start_targeted_movement(self, direction: str, target: Optional[int]) -> None:
        """Start movement with optional target position."""
        async def _move_with_target():
            try:
                if target is None:
                    await self._movement_loop()
                    return
                remaining = abs(target - self._position)
                if remaining == 0:
                    self._stop_movement(update_position=False, cancel_task=False)
                    return
                self._start_position = self._position
                start_time = time.monotonic()
                total_duration = self._travel_time * (remaining / 100)
                while self._direction == direction:
                    elapsed = time.monotonic() - start_time
                    progress = min(1.0, elapsed / total_duration)
                    self._position = self._calculate_position_from_progress(
                        direction, self._start_position, remaining, progress
                    )
                    
                    target_reached = False
                    if direction == DIRECTION_OPENING:
                        target_reached = self._position >= target
                    else:
                        target_reached = self._position <= target
                    
                    if progress >= 1.0 or target_reached:
                        self._position = self._clamp_position(float(target))
                        if self._is_at_limit():
                            self._last_limit_stop_time = time.monotonic()
                            previous_direction = self._direction
                            self._stop_movement(update_position=False, cancel_task=False)
                            self._last_direction = previous_direction
                            self._update_and_notify()
                        else:
                            previous_direction = self._direction
                            self._stop_movement(update_position=False, cancel_task=False)
                            self._last_direction = previous_direction
                            await self._trigger_pulse()
                            self._update_and_notify()
                        break
                    
                    self.async_write_ha_state()
                    await asyncio.sleep(TICK_SECONDS)
            except asyncio.CancelledError:
                return

        if target is None:
            self._cancel_and_create_task(self._movement_loop())
        else:
            self._cancel_and_create_task(_move_with_target())