"""DataUpdateCoordinator for Imeon Energy API."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from aiohttp import ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .client import ImeonHttpClient

_LOGGER = logging.getLogger(__name__)


class ImeonEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Imeon Energy API data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        username: str,
        password: str,
        scan_interval: int = 30,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        # Normalise host (strip protocol if provided)
        self.host = host.replace("http://", "").replace("https://", "")
        self.username = username
        self.password = password
        self._client: Any | None = None
        self._session: ClientSession | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Imeon Energy API."""
        try:
            if self._client is None:
                # Reuse HA aiohttp session to avoid needless sockets and keep cookies
                self._session = async_get_clientsession(self.hass)

                # Instantiate client (async API)
                self._client = ImeonHttpClient(self.host, self._session)
                await self._client.login(self.username, self.password)

            # Fetch data from API (instant snapshot)
            data = await self._client.get_data_instant("data")

            # Transform data to a standardized format
            return self._transform_data(data)

        except Exception as err:
            # If session expired, try to re-login once
            _LOGGER.warning("Error fetching Imeon Energy data, retrying login: %s", err)
            try:
                if self._client is None:
                    self._session = async_get_clientsession(self.hass)
                    self._client = ImeonHttpClient(self.host, self._session)

                await self._client.login(self.username, self.password)
                data = await self._client.get_data_instant("data")
                return self._transform_data(data)
            except Exception as err2:
                _LOGGER.exception("Error fetching Imeon Energy data after retry: %s", err2)
                raise UpdateFailed(f"Error communicating with API: {err2}") from err2


    def _transform_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform raw API data to standardized format for sensors."""
        # The API structure may vary, so we try multiple possible paths
        # Common field names to try (in order of preference)
        
        # Try to extract power values from various possible structures
        grid_power = (
            self._get_nested_value(raw_data, ["grid", "power"], None) or
            self._get_nested_value(raw_data, ["gridPower"], None) or
            self._get_nested_value(raw_data, ["grid_power"], None) or
            self._get_value_by_key(raw_data, ["grid", "p", "Pgrid", "gridPower", "grid_power"], None) or
            0.0
        )
        
        solar_power = (
            self._get_nested_value(raw_data, ["solar", "power"], None) or
            self._get_nested_value(raw_data, ["solarPower"], None) or
            self._get_nested_value(raw_data, ["solar_power"], None) or
            self._get_value_by_key(raw_data, ["solar", "p", "Psolar", "solarPower", "solar_power", "pv"], None) or
            0.0
        )
        
        battery_power = (
            self._get_nested_value(raw_data, ["battery", "power"], None) or
            self._get_nested_value(raw_data, ["batteryPower"], None) or
            self._get_nested_value(raw_data, ["battery_power"], None) or
            self._get_value_by_key(raw_data, ["battery", "p", "Pbattery", "batteryPower", "battery_power", "bat"], None) or
            0.0
        )
        
        home_power = (
            self._get_nested_value(raw_data, ["home", "power"], None) or
            self._get_nested_value(raw_data, ["homePower"], None) or
            self._get_nested_value(raw_data, ["home_power"], None) or
            self._get_value_by_key(raw_data, ["home", "p", "Phome", "homePower", "home_power", "load"], None) or
            (grid_power + solar_power + battery_power)  # Calculate as sum if not available
        )
        
        battery_soc = (
            self._get_nested_value(raw_data, ["battery", "soc"], None) or
            self._get_nested_value(raw_data, ["batterySoc"], None) or
            self._get_nested_value(raw_data, ["battery_soc"], None) or
            self._get_value_by_key(raw_data, ["battery", "soc", "batterySoc", "battery_soc", "soc", "charge"], None) or
            0.0
        )
        
        # Try to get energy values if available
        grid_energy_import = (
            self._get_nested_value(raw_data, ["grid", "energy_import"], None) or
            self._get_nested_value(raw_data, ["grid", "energyImport"], None) or
            self._get_value_by_key(raw_data, ["grid", "energy_import", "energyImport", "Egrid"], None) or
            0.0
        )
        
        grid_energy_export = (
            self._get_nested_value(raw_data, ["grid", "energy_export"], None) or
            self._get_nested_value(raw_data, ["grid", "energyExport"], None) or
            self._get_value_by_key(raw_data, ["grid", "energy_export", "energyExport"], None) or
            0.0
        )
        
        solar_energy = (
            self._get_nested_value(raw_data, ["solar", "energy"], None) or
            self._get_nested_value(raw_data, ["solarEnergy"], None) or
            self._get_value_by_key(raw_data, ["solar", "energy", "solarEnergy", "Esolar"], None) or
            0.0
        )
        
        battery_energy_charged = (
            self._get_nested_value(raw_data, ["battery", "energy_charged"], None) or
            self._get_nested_value(raw_data, ["battery", "energyCharged"], None) or
            self._get_value_by_key(raw_data, ["battery", "energy_charged", "energyCharged"], None) or
            0.0
        )
        
        battery_energy_discharged = (
            self._get_nested_value(raw_data, ["battery", "energy_discharged"], None) or
            self._get_nested_value(raw_data, ["battery", "energyDischarged"], None) or
            self._get_value_by_key(raw_data, ["battery", "energy_discharged", "energyDischarged"], None) or
            0.0
        )
        
        # Ensure all values are floats
        grid_power = float(grid_power) if grid_power is not None else 0.0
        solar_power = float(solar_power) if solar_power is not None else 0.0
        battery_power = float(battery_power) if battery_power is not None else 0.0
        home_power = float(home_power) if home_power is not None else 0.0
        battery_soc = float(battery_soc) if battery_soc is not None else 0.0
        
        transformed = {
            # Power values (W)
            "grid_power": grid_power,
            "solar_power": solar_power,
            "battery_power": battery_power,
            "home_power": home_power,
            
            # Battery state of charge (%)
            "battery_soc": battery_soc,
            
            # Energy values (kWh) - if available from API
            "grid_energy_import": float(grid_energy_import) if grid_energy_import is not None else 0.0,
            "grid_energy_export": float(grid_energy_export) if grid_energy_export is not None else 0.0,
            "solar_energy": float(solar_energy) if solar_energy is not None else 0.0,
            "battery_energy_charged": float(battery_energy_charged) if battery_energy_charged is not None else 0.0,
            "battery_energy_discharged": float(battery_energy_discharged) if battery_energy_discharged is not None else 0.0,
        }

        # Calculate grid consumption/return from power
        if grid_power > 0:
            # Positive = importing from grid (consumption)
            transformed["grid_consumption_power"] = grid_power
            transformed["grid_return_power"] = 0.0
        else:
            # Negative = exporting to grid (return)
            transformed["grid_consumption_power"] = 0.0
            transformed["grid_return_power"] = abs(grid_power)

        # Calculate battery charging/discharging from power
        if battery_power > 0:
            # Positive = charging
            transformed["battery_charging_power"] = battery_power
            transformed["battery_discharging_power"] = 0.0
        else:
            # Negative = discharging
            transformed["battery_charging_power"] = 0.0
            transformed["battery_discharging_power"] = abs(battery_power)

        # Log raw data structure for debugging (only first time or on error)
        if not hasattr(self, "_logged_structure"):
            _LOGGER.debug("Raw API data structure: %s", raw_data)
            self._logged_structure = True

        return transformed

    def _get_nested_value(self, data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
        """Get nested value from dictionary using list of keys."""
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def _get_value_by_key(self, data: dict[str, Any], possible_keys: list[str], default: Any = None) -> Any:
        """Try to get a value by trying multiple possible key names."""
        # First try direct keys
        for key in possible_keys:
            if key in data:
                return data[key]
        
        # Then try nested in common structures
        for key in possible_keys:
            for prefix in ["", "data", "values", "status", "state"]:
                if prefix:
                    nested = self._get_nested_value(data, [prefix, key], None)
                else:
                    nested = self._get_nested_value(data, [key], None)
                if nested is not None:
                    return nested
        
        return default
