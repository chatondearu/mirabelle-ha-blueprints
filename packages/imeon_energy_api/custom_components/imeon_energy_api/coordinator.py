"""DataUpdateCoordinator for Imeon Energy API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from aiohttp import ClientSession

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .client import ImeonHttpClient
from .sensor_config import (
    API_FIELD_GRID_POWER,
    API_FIELD_BATTERY_SOC,
    API_FIELD_PV_INPUTS,
    API_FIELD_BATTERY_CHARGING,
    API_FIELD_BATTERY_DISCHARGING,
)

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
        self._scan_history: list[dict[str, Any]] = []
        self._known_timestamps: set[int] = set()
        self._last_processed_count: int = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Imeon Energy API."""
        try:
            await self._ensure_client_connected()
            return await self._fetch_and_process_data()
        except Exception as err:
            _LOGGER.warning("Error fetching Imeon Energy data, retrying login: %s", err)
            try:
                await self._ensure_client_connected(force_reconnect=True)
                return await self._fetch_and_process_data()
            except Exception as err2:
                _LOGGER.exception("Error fetching Imeon Energy data after retry: %s", err2)
                raise UpdateFailed(f"Error communicating with API: {err2}") from err2

    async def _ensure_client_connected(self, force_reconnect: bool = False) -> None:
        """Ensure client is initialized and authenticated."""
        if self._client is None or force_reconnect:
            self._session = async_get_clientsession(self.hass)
            self._client = ImeonHttpClient(
                self.host,
                self._session,
                username=self.username,
                password=self.password,
            )
        await self._client.login(self.username, self.password)

    async def _fetch_and_process_data(self) -> dict[str, Any]:
        """Fetch and process data from API."""
        primary = await self._client.get_data_instant("data")
        
        scan = {}
        try:
            scan = await self._client.get_data_instant("scan")
        except Exception as scan_err:
            _LOGGER.debug("Scan endpoint failed: %s", scan_err)
        
        monitor = {}
        try:
            monitor = await self._client.get_monitor("hour")
        except Exception as monitor_err:
            _LOGGER.debug("Monitor endpoint failed: %s", monitor_err)
        
        self._process_scan_history(scan)
        self.meta = self._extract_meta(primary)
        
        transformed = self._transform_data({"data": primary, "scan": scan, "monitor": monitor})
        self._record_historical_values(transformed)
        
        return transformed


    def _transform_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform raw API data to standardized format for sensors."""
        # Use scan data with timestamps for more realistic values
        # Get the most recent scan entry (or average if multiple)
        scan_entry = self._get_latest_scan_entry()
        
        if not scan_entry:
            # Fallback to normalized payload if no scan history
            payload_data = self._normalize_payload(raw_data.get("data", raw_data))
            payload_scan = self._normalize_payload(raw_data.get("scan", {}))
            payload = {**payload_data, **payload_scan}
        else:
            payload = scan_entry

        grid_power = float(payload.get(API_FIELD_GRID_POWER) or 0.0)
        solar_power = float(self._sum_pv_inputs(payload) or 0.0)
        
        # Use AC fields for battery power (more accurate)
        # Fallback to estimation if AC fields are not available
        if API_FIELD_BATTERY_CHARGING in payload or API_FIELD_BATTERY_DISCHARGING in payload:
            battery_charging = float(payload.get(API_FIELD_BATTERY_CHARGING) or 0.0)
            battery_discharging = float(payload.get(API_FIELD_BATTERY_DISCHARGING) or 0.0)
            # battery_power: positive = discharging, negative = charging
            battery_power = battery_discharging - battery_charging
        else:
            # Fallback: estimate from current * voltage
            estimated = self._estimate_battery_power(payload)
            if estimated is not None:
                battery_power = float(estimated)
                battery_charging = battery_power if battery_power > 0 else 0.0
                battery_discharging = abs(battery_power) if battery_power < 0 else 0.0
            else:
                battery_power = 0.0
                battery_charging = 0.0
                battery_discharging = 0.0

        battery_soc = float(payload.get(API_FIELD_BATTERY_SOC) or 0.0)
        home_power = grid_power + solar_power + battery_power

        transformed = {
            "grid_power": grid_power,
            "solar_power": solar_power,
            "battery_power": battery_power,
            "home_power": home_power,
            "battery_soc": battery_soc,
            "grid_energy_import": 0.0,
            "grid_energy_export": 0.0,
            "solar_energy": 0.0,
            "battery_energy_charged": 0.0,
            "battery_energy_discharged": 0.0,
        }

        # Calculate grid consumption/return from power
        if grid_power > 0:
            transformed["grid_consumption_power"] = grid_power
            transformed["grid_return_power"] = 0.0
        else:
            transformed["grid_consumption_power"] = 0.0
            transformed["grid_return_power"] = abs(grid_power)

        # Use direct AC fields for battery charging/discharging
        transformed["battery_charging_power"] = battery_charging
        transformed["battery_discharging_power"] = battery_discharging

        return transformed

    def _normalize_payload(self, raw_data: Any) -> dict[str, Any]:
        """Normalize API response to a flat dictionary."""
        data = raw_data

        if isinstance(data, dict) and "result" in data and isinstance(data["result"], str):
            try:
                import json
                decoded = json.loads(data["result"])
                data = decoded[0] if isinstance(decoded, list) and decoded else decoded
            except Exception:
                pass

        if isinstance(data, list) and data:
            data = data[0]

        if isinstance(data, dict):
            for key in ("data", "payload"):
                if key in data and isinstance(data[key], (dict, list)):
                    unwrapped = data[key]
                    data = unwrapped[0] if isinstance(unwrapped, list) and unwrapped else unwrapped
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
        for key in API_FIELD_PV_INPUTS:
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

    def _process_scan_history(self, scan_data: dict[str, Any]) -> None:
        """Process scan data with timestamps to build a history, avoiding duplicates."""
        if not isinstance(scan_data, dict):
            return
        
        scan_entries = scan_data.get("val", [])
        if not isinstance(scan_entries, list) or not scan_entries:
            return
        
        # Process each entry with its timestamp
        new_entries = []
        for entry in scan_entries:
            if not isinstance(entry, dict):
                continue
            
            timestamp = entry.get("timestamp")
            timestamp_int = None
            
            # Convert timestamp to datetime and get integer representation
            try:
                if isinstance(timestamp, (int, float)):
                    timestamp_int = int(timestamp)
                    entry["_timestamp"] = datetime.fromtimestamp(timestamp_int)
                elif isinstance(timestamp, str):
                    # Try parsing time string if available
                    time_str = entry.get("time")
                    if time_str:
                        try:
                            entry["_timestamp"] = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                            timestamp_int = int(entry["_timestamp"].timestamp())
                        except ValueError:
                            entry["_timestamp"] = datetime.now()
                            timestamp_int = int(entry["_timestamp"].timestamp())
                    else:
                        entry["_timestamp"] = datetime.now()
                        timestamp_int = int(entry["_timestamp"].timestamp())
                else:
                    entry["_timestamp"] = datetime.now()
                    timestamp_int = int(entry["_timestamp"].timestamp())
            except Exception:
                entry["_timestamp"] = datetime.now()
                timestamp_int = int(entry["_timestamp"].timestamp())
            
            # Skip if we've already processed this timestamp
            if timestamp_int and timestamp_int in self._known_timestamps:
                continue
            
            # Mark as processed
            if timestamp_int:
                self._known_timestamps.add(timestamp_int)
            
            new_entries.append(entry)
        
        # Add new entries to history (keep last 100 entries to avoid memory issues)
        self._scan_history.extend(new_entries)
        if len(self._scan_history) > 100:
            removed = self._scan_history[:-100]
            for entry in removed:
                ts = entry.get("_timestamp")
                if ts:
                    ts_int = int(ts.timestamp())
                    self._known_timestamps.discard(ts_int)
            self._scan_history = self._scan_history[-100:]
            self._last_processed_count = max(0, self._last_processed_count - len(removed))
        
        # Sort by timestamp (most recent first)
        self._scan_history.sort(key=lambda x: x.get("_timestamp", datetime.min), reverse=True)

    def _get_latest_scan_entry(self) -> dict[str, Any] | None:
        """Get the most recent scan entry, or average of recent entries if available."""
        if not self._scan_history:
            return None
        
        # Return the most recent entry (already sorted)
        return self._scan_history[0] if self._scan_history else None

    @callback
    def _record_historical_values(self, transformed_data: dict[str, Any]) -> None:
        """Track new scan entries for potential future timestamp-based recording."""
        if not self._scan_history:
            return
        
        new_count = len(self._scan_history) - self._last_processed_count
        if new_count > 0:
            _LOGGER.debug("Processed %d new scan entries with timestamps", new_count)
            self._last_processed_count = len(self._scan_history)

