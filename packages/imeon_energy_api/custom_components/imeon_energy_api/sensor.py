"""Sensor platform for Imeon Energy API."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import ImeonEnergyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Imeon Energy sensors from a config entry."""
    coordinator: ImeonEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # Energy sensors for Energy Dashboard (kWh, total_increasing)
        ImeonEnergySensor(
            coordinator,
            "grid_consumption",
            "Grid Consumption",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:transmission-tower",
            "grid_consumption_power",
        ),
        ImeonEnergySensor(
            coordinator,
            "grid_return",
            "Grid Return",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:transmission-tower-export",
            "grid_return_power",
        ),
        ImeonEnergySensor(
            coordinator,
            "solar_production",
            "Solar Production",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:solar-power",
            "solar_power",
        ),
        ImeonEnergySensor(
            coordinator,
            "battery_charging",
            "Battery Charging",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:battery-charging",
            "battery_charging_power",
        ),
        ImeonEnergySensor(
            coordinator,
            "battery_discharging",
            "Battery Discharging",
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            UnitOfEnergy.KILO_WATT_HOUR,
            "mdi:battery",
            "battery_discharging_power",
        ),
        # Power sensors (W, measurement)
        ImeonPowerSensor(
            coordinator,
            "grid_power",
            "Grid Power",
            "mdi:transmission-tower",
        ),
        ImeonPowerSensor(
            coordinator,
            "solar_power",
            "Solar Power",
            "mdi:solar-power",
        ),
        ImeonPowerSensor(
            coordinator,
            "battery_power",
            "Battery Power",
            "mdi:battery",
        ),
        ImeonPowerSensor(
            coordinator,
            "home_power",
            "Home Consumption",
            "mdi:home-lightning-bolt",
        ),
        # Battery state of charge (%)
        ImeonBatterySocSensor(
            coordinator,
            "battery_soc",
            "Battery State of Charge",
            "mdi:battery-high",
        ),
    ]

    async_add_entities(entities)


class ImeonEnergySensor(CoordinatorEntity[ImeonEnergyCoordinator], SensorEntity, RestoreEntity):
    """Base class for energy sensors that integrate power over time."""

    def __init__(
        self,
        coordinator: ImeonEnergyCoordinator,
        sensor_id: str,
        name: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
        unit: str,
        icon: str,
        power_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = f"{coordinator.host} {name}"
        self._attr_unique_id = f"{coordinator.host}_{sensor_id}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._power_key = power_key
        self._last_update = None
        self._last_power = 0.0
        self._accumulated_energy = 0.0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=DEFAULT_NAME,
            manufacturer="Imeon Energy",
            model="Inverter",
        )

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
        
        energy_key = energy_mapping.get(self._sensor_id)
        if energy_key and energy_key in data and data[energy_key] > 0:
            # Use energy value from API if available (already in kWh)
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
        sensor_id: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = f"{coordinator.host} {name}"
        self._attr_unique_id = f"{coordinator.host}_{sensor_id}"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=DEFAULT_NAME,
            manufacturer="Imeon Energy",
            model="Inverter",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get(self._sensor_id, 0.0)


class ImeonBatterySocSensor(CoordinatorEntity[ImeonEnergyCoordinator], SensorEntity):
    """Sensor for battery state of charge."""

    def __init__(
        self,
        coordinator: ImeonEnergyCoordinator,
        sensor_id: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = f"{coordinator.host} {name}"
        self._attr_unique_id = f"{coordinator.host}_{sensor_id}"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=DEFAULT_NAME,
            manufacturer="Imeon Energy",
            model="Inverter",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get(self._sensor_id, 0.0)
