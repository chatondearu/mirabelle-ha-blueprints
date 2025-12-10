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
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.select import SelectEntity
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
PULSE_GAP = 0.8


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cover Manager cover."""
    cover = CoverManagerCover(config_entry)
    travel = CoverManagerTravelTime(config_entry, cover)
    position = CoverManagerPosition(config_entry, cover)
    direction = CoverManagerDirection(config_entry, cover)
    cover.register_sub_entities(travel, position, direction)
    async_add_entities([cover, travel, position, direction])


class CoverManagerCover(CoverEntity, RestoreEntity):
    """Representation of a Cover Manager cover driven by an impulse switch."""

    def __init__(self, config_entry: ConfigEntry) -> None:
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
        self._start_position: float = self._position
        self._ignore_next_impulse = False
        self._listener_remove = None
        self._traveltime_entity: Optional["CoverManagerTravelTime"] = None
        self._position_entity: Optional["CoverManagerPosition"] = None
        self._direction_entity: Optional["CoverManagerDirection"] = None
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
        }

    @property
    def state(self) -> str | None:
        if self.is_opening:
            return STATE_OPENING
        if self.is_closing:
            return STATE_CLOSING
        return STATE_OPEN if self.current_cover_position > 0 else STATE_CLOSED

    async def _trigger_pulse(self) -> None:
        self._ignore_next_impulse = True
        try:
            await self.hass.services.async_call(
                "switch", "turn_on", {"entity_id": self._switch_entity}
            )
            await asyncio.sleep(PULSE_GAP)
        finally:
            self._ignore_next_impulse = False

    def _stop_movement(self, update_position: bool = True) -> None:
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
        self._notify_sub_entities()

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
                    self._stop_movement(update_position=False)
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
        new_state = event.data.get("new_state")
        if not new_state or new_state.state != "on":
            return
        if self._ignore_next_impulse:
            return
        if self._direction in ("opening", "closing"):
            self._stop_movement(update_position=True)
            return

        if self._position <= 0.0:
            dir_to_start = "opening"
        elif self._position >= 100.0:
            dir_to_start = "closing"
        else:
            dir_to_start = "opening" if self._last_direction == "closing" else "closing"

        self._start_movement(dir_to_start)

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._go_direction("opening")

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._go_direction("closing")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        self._stop_movement(update_position=True)
        await self._trigger_pulse()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        target = max(0, min(100, int(kwargs[ATTR_POSITION])))
        self._stop_movement(update_position=True)
        if target == self.current_cover_position:
            return
        direction = "opening" if target > self.current_cover_position else "closing"
        await self._go_direction(direction, target=target)

    # Sub-entity hooks
    def register_sub_entities(
        self,
        travel: "CoverManagerTravelTime",
        position: "CoverManagerPosition",
        direction: "CoverManagerDirection",
    ) -> None:
        self._traveltime_entity = travel
        self._position_entity = position
        self._direction_entity = direction

    def _notify_sub_entities(self) -> None:
        for ent in (self._traveltime_entity, self._position_entity, self._direction_entity):
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

    async def _go_direction(self, direction: str, target: Optional[int] = None) -> None:
        """Handle direction change with impulse switch (may require two pulses)."""
        # If already in desired direction and moving, do nothing
        if self._direction == direction:
            return

        # If moving opposite, stop and send a pulse to stop physical relay, then switch
        if self._direction in ("opening", "closing") and self._direction != direction:
            self._stop_movement(update_position=True)
            await self._trigger_pulse()  # first pulse stops current motion physically

        # Start movement in target direction
        self._position = float(self.current_cover_position)
        self._start_position = self._position
        self._movement_start_time = time.monotonic()
        self._direction = direction
        self._last_direction = direction

        async def _move_with_target():
            try:
                if target is None:
                    # free run until bound
                    await self._movement_loop()
                    return
                remaining = abs(target - self._position)
                if remaining == 0:
                    self._stop_movement(update_position=False)
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
                        self._stop_movement(update_position=False)
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

        # Second pulse to start motion in the new direction
        await self._trigger_pulse()


class CoverManagerTravelTime(NumberEntity):
    """Number entity to adjust travel time."""

    _attr_native_min_value = 1
    _attr_native_max_value = 300
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_travel_time"
        self._attr_name = f"{entry.data['name']} Travel Time"
        self._attr_device_info = cover.device_info

    @property
    def native_value(self) -> float | None:
        return float(self._cover._travel_time)  # noqa: SLF001

    async def async_set_native_value(self, value: float) -> None:
        self._cover.update_travel_time(int(value))


class CoverManagerPosition(NumberEntity):
    """Number entity to adjust position."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_position_ctl"
        self._attr_name = f"{entry.data['name']} Position"
        self._attr_device_info = cover.device_info

    @property
    def native_value(self) -> float | None:
        return float(self._cover.current_cover_position)

    async def async_set_native_value(self, value: float) -> None:
        await self._cover.async_set_cover_position(position=int(value))


class CoverManagerDirection(SelectEntity):
    """Select entity to adjust direction."""

    _attr_options = ["opening", "closing", "idle"]

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_direction_ctl"
        self._attr_name = f"{entry.data['name']} Direction"
        self._attr_device_info = cover.device_info

    @property
    def current_option(self) -> str | None:
        return self._cover._direction  # noqa: SLF001

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            return
        self._cover.update_direction(option)