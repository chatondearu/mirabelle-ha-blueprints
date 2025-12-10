"""Number platform for Cover Manager integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up the Cover Manager number entities."""
    cover: CoverManagerCover = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        CoverManagerTravelTime(config_entry, cover),
        CoverManagerPosition(config_entry, cover),
        CoverManagerPulseGap(config_entry, cover),
    ]
    
    cover.register_sub_entities(
        travel=entities[0],
        position=entities[1],
        pulse_gap=entities[2],
    )
    
    async_add_entities(entities)


class CoverManagerTravelTime(NumberEntity):
    """Number entity to adjust travel time."""

    _attr_native_min_value = 1
    _attr_native_max_value = 300
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_travel_time"
        self._attr_name = "Travel Time"
        self._attr_device_info = cover.device_info

    @property
    def native_value(self) -> float | None:
        return float(self._cover._travel_time)  # noqa: SLF001

    async def async_set_native_value(self, value: float) -> None:
        self._cover.update_travel_time(int(value))


class CoverManagerPosition(NumberEntity):
    """Number entity to override/reset position value."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_position_ctl"
        self._attr_name = "Position Override"
        self._attr_device_info = cover.device_info

    @property
    def native_value(self) -> float | None:
        return float(self._cover.current_cover_position)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "current_position": round(self._cover._position, 1),  # noqa: SLF001
            "description": "Override position to reset/correct the cover position",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Override position value - directly sets position without moving."""
        self._cover.update_position(float(value))


class CoverManagerPulseGap(NumberEntity):
    """Number entity to adjust pulse gap (switch delay)."""

    _attr_native_min_value = 0.1
    _attr_native_max_value = 5.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, cover: CoverManagerCover) -> None:
        self._cover = cover
        self._attr_unique_id = f"{entry.entry_id}_pulse_gap"
        self._attr_name = "Pulse Gap"
        self._attr_device_info = cover.device_info

    @property
    def native_value(self) -> float | None:
        return float(self._cover._pulse_gap)  # noqa: SLF001

    async def async_set_native_value(self, value: float) -> None:
        self._cover.update_pulse_gap(value)
