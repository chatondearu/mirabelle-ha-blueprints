"""Sensor platform for Imeon Energy API."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ImeonEnergyCoordinator
from .sensor_config import SENSORS, get_energy_sensors, get_power_sensors

_LOGGER = logging.getLogger(__name__)


def _get_device_info(coordinator: ImeonEnergyCoordinator) -> DeviceInfo:
    """Get device info for all sensors (shared across entities)."""
    serial = coordinator.meta.get("serial") or coordinator.host
    model = coordinator.meta.get("model") or "Imeon Inverter"
    sw = coordinator.meta.get("sw_version")
    return DeviceInfo(
        identifiers={(DOMAIN, serial)},
        name=f"Imeon Inverter {serial}",
        manufacturer="Imeon",
        model=model,
        sw_version=sw,
        configuration_url=f"http://{coordinator.host}/",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Imeon Energy sensors from a config entry."""
    coordinator: ImeonEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    device_info = _get_device_info(coordinator)

    # Create energy sensors
    for config in get_energy_sensors():
        entities.append(
            ImeonEnergySensor(coordinator, config, device_info)
        )

    # Create power sensors
    for config in get_power_sensors():
        entities.append(
            ImeonPowerSensor(coordinator, config, device_info)
        )

    async_add_entities(entities)


class ImeonEnergySensor(CoordinatorEntity[ImeonEnergyCoordinator], SensorEntity, RestoreEntity):
    """Energy sensors that integrate power over time."""

    def __init__(
        self,
        coordinator: ImeonEnergyCoordinator,
        config: Any,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config = config
        serial = coordinator.meta.get("serial") or coordinator.host
        self._attr_name = config.name
        self._attr_unique_id = f"{serial}_{config.sensor_id}"
        self._attr_device_class = config.device_class
        self._attr_state_class = config.state_class
        self._attr_native_unit_of_measurement = config.unit
        self._attr_icon = config.icon
        self._power_key = config.power_key
        self._last_update = None
        self._last_power = 0.0
        self._accumulated_energy = 0.0
        self._attr_device_info = device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass, restore state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in ("unknown", "unavailable"):
                try:
                    self._accumulated_energy = float(last_state.state)
                except (ValueError, TypeError):
                    pass

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None

        # Try to get energy value directly from API if available
        energy_mapping = {
            "grid_consumption": "grid_energy_import",
            "grid_return": "grid_energy_export",
            "solar_production": "solar_energy",
            "battery_charging": "battery_energy_charged",
            "battery_discharging": "battery_energy_discharged",
        }
        energy_key = energy_mapping.get(self._config.sensor_id)
        if energy_key and energy_key in data and data[energy_key] > 0:
            return data[energy_key]

        # If no energy value from API, integrate power over time
        # This is a simple Riemann sum integration
        power = data.get(self._power_key, 0.0)  # Power in W
        now = dt_util.utcnow()

        if self._last_update is not None:
            # Calculate time difference in hours
            time_diff = (now - self._last_update).total_seconds() / 3600.0
            
            # Integrate: energy = power * time (convert W to kW, then multiply by hours)
            energy_increment = (power / 1000.0) * time_diff
            
            # Only accumulate positive energy (for total_increasing)
            if energy_increment > 0:
                self._accumulated_energy += energy_increment

        self._last_update = now
        self._last_power = power

        # Return accumulated energy in kWh
        return round(self._accumulated_energy, 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if not data:
            return {}

        power = data.get(self._power_key, 0.0)
        return {
            "power": power,  # Current power in W
        }


class ImeonPowerSensor(CoordinatorEntity[ImeonEnergyCoordinator], SensorEntity):
    """Sensor for instantaneous power values."""

    def __init__(
        self,
        coordinator: ImeonEnergyCoordinator,
        config: Any,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config = config
        serial = coordinator.meta.get("serial") or coordinator.host
        self._attr_name = config.name
        self._attr_unique_id = f"{serial}_{config.sensor_id}"
        self._attr_device_class = config.device_class
        self._attr_state_class = config.state_class
        self._attr_native_unit_of_measurement = config.unit
        self._attr_icon = config.icon
        self._attr_device_info = device_info

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get(self._config.sensor_id, 0.0)
