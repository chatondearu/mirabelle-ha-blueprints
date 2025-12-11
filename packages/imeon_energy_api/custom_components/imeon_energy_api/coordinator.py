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
        self.meta: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Imeon Energy API."""
        try:
            if self._client is None:
                # Reuse HA aiohttp session to avoid needless sockets and keep cookies
                self._session = async_get_clientsession(self.hass)

                # Instantiate client (async API)
                self._client = ImeonHttpClient(
                    self.host,
                    self._session,
                    username=self.username,
                    password=self.password,
                )
                await self._client.login(self.username, self.password)

            # Fetch data from API (instant snapshot)
            primary = await self._client.get_data_instant("data")
            # Also fetch scan (often contains live power values)
            try:
                scan = await self._client.get_data_instant("scan")
            except Exception as scan_err:
                _LOGGER.debug("Scan endpoint failed, continuing with primary only: %s", scan_err)
                scan = {}
            data = {"data": primary, "scan": scan}
            self.meta = self._extract_meta(primary)

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
                primary = await self._client.get_data_instant("data")
                try:
                    scan = await self._client.get_data_instant("scan")
                except Exception as scan_err:
                    _LOGGER.debug("Scan endpoint failed after retry: %s", scan_err)
                    scan = {}
                data = {"data": primary, "scan": scan}
                self.meta = self._extract_meta(primary)
                return self._transform_data(data)
            except Exception as err2:
                _LOGGER.exception("Error fetching Imeon Energy data after retry: %s", err2)
                raise UpdateFailed(f"Error communicating with API: {err2}") from err2


    def _transform_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform raw API data to standardized format for sensors."""
        # Prefer scan payload (live power) if available; merge data and scan
        payload_data = self._normalize_payload(raw_data.get("data", raw_data))
        payload_scan = self._normalize_payload(raw_data.get("scan", {}))
        payload = {**payload_data, **payload_scan}

        grid_power = float(payload.get("ac_input_total_active_power") or 0.0)
        home_power = float(payload.get("ac_output_total_active_power") or payload.get("ac_output_power_r") or 0.0)
        solar_power = float(self._sum_pv_inputs(payload) or 0.0)

        battery_power_val = payload.get("battery_power")
        if battery_power_val is None:
            battery_power_val = self._estimate_battery_power(payload) or 0.0
        battery_power = float(battery_power_val)

        battery_soc = float(payload.get("battery_soc") or 0.0)

        transformed = {
            "grid_power": grid_power,
            "solar_power": solar_power,
            "battery_power": battery_power,
            "home_power": home_power,
            "battery_soc": battery_soc,
            # Energy placeholders (not provided by scan)
            "grid_energy_import": 0.0,
            "grid_energy_export": 0.0,
            "solar_energy": 0.0,
            "battery_energy_charged": 0.0,
            "battery_energy_discharged": 0.0,
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

    def _normalize_payload(self, raw_data: Any) -> dict[str, Any]:
        """Handle the various response shapes from the inverter."""
        data = raw_data

        # If response has a "result" key with JSON string, decode it
        if isinstance(data, dict) and "result" in data and isinstance(data["result"], str):
            try:
                import json

                decoded = json.loads(data["result"])
                if isinstance(decoded, dict):
                    data = decoded
                elif isinstance(decoded, list) and decoded:
                    data = decoded[0]
            except Exception:
                pass

        # If top-level is list, take first element
        if isinstance(data, list) and data:
            data = data[0]

        # If wrapped in "val" (scan), unwrap first element
        if isinstance(data, dict) and "val" in data and isinstance(data["val"], list) and data["val"]:
            data = data["val"][0]

        # If wrapped in "data"/"payload", unwrap
        for key in ("data", "payload"):
            if isinstance(data, dict) and key in data and isinstance(data[key], (dict, list)):
                data = data[key]
                if isinstance(data, list) and data:
                    data = data[0]
                break

        return data if isinstance(data, dict) else {}

    def _extract_meta(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Extract device metadata (serial, model, software) from /data payload."""
        payload = self._normalize_payload(raw_data)
        return {
            "serial": payload.get("serial"),
            "model": payload.get("type"),
            "sw_version": payload.get("software"),
        }

    def _sum_pv_inputs(self, payload: dict[str, Any]) -> float | None:
        """Sum PV inputs if present."""
        total = 0.0
        found = False
        for key in ("pv_input_power1", "pv_input_power2", "pv_input_power3", "pv_power", "pv_input_power"):
            val = payload.get(key)
            if val is not None:
                found = True
                try:
                    total += float(val)
                except (ValueError, TypeError):
                    pass
        return total if found else None

    def _estimate_battery_power(self, payload: dict[str, Any]) -> float | None:
        """Estimate battery power from current * voltage if direct power is missing."""
        current = payload.get("battery_current")
        voltage = payload.get("p_battery_voltage") or payload.get("battery_voltage")
        if current is None or voltage is None:
            return None
        try:
            return float(current) * float(voltage)
        except (ValueError, TypeError):
            return None

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
