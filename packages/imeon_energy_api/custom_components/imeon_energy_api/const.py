"""Constants for the Imeon Energy API integration."""

DOMAIN = "imeon_energy_api"

# Configuration keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_NAME = "Imeon Energy"

# Sensor types for Energy Dashboard
SENSOR_TYPE_GRID_CONSUMPTION = "grid_consumption"
SENSOR_TYPE_GRID_RETURN = "grid_return"
SENSOR_TYPE_SOLAR_PRODUCTION = "solar_production"
SENSOR_TYPE_BATTERY_CHARGING = "battery_charging"
SENSOR_TYPE_BATTERY_DISCHARGING = "battery_discharging"
SENSOR_TYPE_BATTERY_SOC = "battery_soc"
SENSOR_TYPE_BATTERY_POWER = "battery_power"
SENSOR_TYPE_GRID_POWER = "grid_power"
SENSOR_TYPE_SOLAR_POWER = "solar_power"
SENSOR_TYPE_HOME_CONSUMPTION = "home_consumption"

# API data keys (these will be mapped from the API response)
API_KEY_GRID_POWER = "grid_power"
API_KEY_SOLAR_POWER = "solar_power"
API_KEY_BATTERY_POWER = "battery_power"
API_KEY_BATTERY_SOC = "battery_soc"
API_KEY_HOME_POWER = "home_power"
