"""Sensor configuration and mapping definitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower, PERCENTAGE


@dataclass
class SensorConfig:
    """Configuration for a sensor entity."""

    sensor_id: str
    name: str
    device_class: SensorDeviceClass
    state_class: SensorStateClass
    unit: str
    icon: str
    api_key: str | None = None
    power_key: str | None = None
    calculation: str | None = None


# API field mappings
API_FIELD_GRID_POWER = "em_power"
API_FIELD_GRID_TO_BATTERY = "grid_power_r"
API_FIELD_SOLAR_POWER = "pv_input_power"  # Will be summed
API_FIELD_BATTERY_POWER = "battery_power"
API_FIELD_BATTERY_CHARGING = "ac_input_total_active_power"
API_FIELD_BATTERY_DISCHARGING = "ac_output_total_active_power"
API_FIELD_BATTERY_CURRENT = "battery_current"
API_FIELD_BATTERY_VOLTAGE = "p_battery_voltage"
API_FIELD_BATTERY_SOC = "battery_soc"
API_FIELD_PV_INPUTS = ["pv_input_power1", "pv_input_power2", "pv_input_power3"]

# Sensor definitions
SENSORS: list[SensorConfig] = [
    # Energy sensors (kWh, total_increasing)
    SensorConfig(
        sensor_id="grid_consumption",
        name="Grid Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:transmission-tower",
        power_key="grid_consumption_power",
    ),
    SensorConfig(
        sensor_id="grid_return",
        name="Grid Return",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:transmission-tower-export",
        power_key="grid_return_power",
    ),
    SensorConfig(
        sensor_id="solar_production",
        name="Solar Production",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:solar-power",
        power_key="solar_power",
    ),
    SensorConfig(
        sensor_id="battery_charging",
        name="Battery Charging",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery-charging",
        power_key="battery_charging_power",
    ),
    SensorConfig(
        sensor_id="battery_discharging",
        name="Battery Discharging",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery",
        power_key="battery_discharging_power",
    ),
    # Power sensors (W, measurement)
    SensorConfig(
        sensor_id="grid_power",
        name="Grid Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfPower.WATT,
        icon="mdi:transmission-tower",
        api_key=API_FIELD_GRID_POWER,
    ),
    SensorConfig(
        sensor_id="solar_power",
        name="Solar Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfPower.WATT,
        icon="mdi:solar-power",
        api_key=API_FIELD_SOLAR_POWER,
        calculation="sum_pv_inputs",
    ),
    SensorConfig(
        sensor_id="battery_power",
        name="Battery Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfPower.WATT,
        icon="mdi:battery",
        api_key=API_FIELD_BATTERY_POWER,
        calculation="estimate_if_missing",
    ),
    SensorConfig(
        sensor_id="home_power",
        name="Home Consumption",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfPower.WATT,
        icon="mdi:home-lightning-bolt",
        calculation="sum_powers",
    ),
    # Battery state of charge (%)
    SensorConfig(
        sensor_id="battery_soc",
        name="Battery State of Charge",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        unit=PERCENTAGE,
        icon="mdi:battery-high",
        api_key=API_FIELD_BATTERY_SOC,
    ),
]


def get_sensor_config(sensor_id: str) -> SensorConfig | None:
    """Get sensor configuration by sensor_id."""
    for config in SENSORS:
        if config.sensor_id == sensor_id:
            return config
    return None


def get_energy_sensors() -> list[SensorConfig]:
    """Get all energy sensors."""
    return [s for s in SENSORS if s.device_class == SensorDeviceClass.ENERGY]


def get_power_sensors() -> list[SensorConfig]:
    """Get all power sensors."""
    return [s for s in SENSORS if s.device_class == SensorDeviceClass.POWER]
