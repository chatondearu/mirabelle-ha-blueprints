# Imeon Energy API

A Home Assistant custom integration to monitor your Imeon Energy inverter, providing comprehensive energy monitoring with full compatibility with Home Assistant's Energy Dashboard.

## ⚠️ Important: HACS Installation

This custom component is part of a monorepo structure. It is automatically synced to a dedicated sub-repository for HACS installation.

**Use the dedicated repository for HACS:**
- Repository: `https://github.com/chatondearu/myrabelle-hacs-imeon-energy` (to be created)
- This repository is automatically synced from the monorepo

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for detailed installation instructions.

### Quick Start (HACS)

1. Add repository to HACS: `https://github.com/chatondearu/myrabelle-hacs-imeon-energy`
2. Search for "Imeon Energy API" in HACS
3. Click **Download**
4. Restart Home Assistant
5. Configure via **Settings** > **Devices & Services** > **Add Integration**

## Features

- **Energy Dashboard Compatible**: All sensors are properly configured for Home Assistant's Energy Dashboard
- **Comprehensive Monitoring**: 
  - Grid consumption and return
  - Solar production
  - Battery charging and discharging
  - Home consumption
  - Battery state of charge
- **Real-time Power Monitoring**: Instantaneous power values for all sources
- **Automatic Energy Integration**: Converts power to energy automatically
- **Local Polling**: Direct communication with your inverter on your local network
- **Multilingual Support**: English and French translations

## Requirements

- Home Assistant 2025.5.3 or later
- Imeon OS One v1.8.1.0 or later (released in January 2025)
- Ethernet (ETH) port connection (WiFi connection lacks NAT feature)
- Network access to your Imeon inverter

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Imeon Energy API"
4. Enter your inverter details:
   - **Host**: IP address of your inverter
   - **Username**: Inverter username
   - **Password**: Inverter password
   - **Update Interval**: How often to poll data (default: 30 seconds)

## Sensors Created

### Energy Sensors (for Energy Dashboard)

All energy sensors use `device_class: energy`, `state_class: total_increasing`, and `unit_of_measurement: kWh`:

- **Grid Consumption**: Total energy imported from the grid
- **Grid Return**: Total energy exported to the grid
- **Solar Production**: Total energy produced by solar panels
- **Battery Charging**: Total energy stored in battery
- **Battery Discharging**: Total energy drawn from battery

### Power Sensors

All power sensors use `device_class: power`, `state_class: measurement`, and `unit_of_measurement: W`:

- **Grid Power**: Current grid power (positive = import, negative = export)
- **Solar Power**: Current solar production
- **Battery Power**: Current battery power (positive = charging, negative = discharging)
- **Home Consumption**: Current home power consumption

### Battery Sensor

- **Battery State of Charge**: Battery charge level in percentage (0-100%)

## Energy Dashboard Setup

After installation, configure your Energy Dashboard:

1. Go to **Settings** > **Dashboards** > **Energy**
2. Click **Configure**
3. Select your sensors:
   - **Grid Consumption**: `sensor.<host>_grid_consumption`
   - **Grid Return**: `sensor.<host>_grid_return`
   - **Solar Production**: `sensor.<host>_solar_production`
   - **Battery Charging**: `sensor.<host>_battery_charging`
   - **Battery Discharging**: `sensor.<host>_battery_discharging`

## Repository Structure

```
packages/imeon_energy_api/
├── custom_components/
│   └── imeon_energy_api/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── manifest.json
│       └── translations/
│           ├── en.json
│           └── fr.json
├── hacs.json
├── INSTALLATION.md
└── README.md
```

## Troubleshooting

### Integration doesn't connect

- Verify your inverter IP address is correct
- Check that your Home Assistant instance can reach the inverter on your local network
- Verify your username and password are correct
- Ensure Imeon OS One v1.8.1.0 or later is installed
- Check that you're using Ethernet connection (not WiFi)

### Sensors don't appear in Energy Dashboard

- Verify sensors have `device_class: energy` and `state_class: total_increasing`
- Check that sensors are showing values (not `unknown` or `unavailable`)
- Wait a few minutes for energy values to accumulate
- Check Home Assistant logs for errors

### Energy values are zero

- Energy sensors integrate power over time, so they start at 0
- Wait a few minutes for values to accumulate
- Verify power sensors are showing non-zero values
- Check that the update interval is appropriate (not too long)

## Development

This component is part of the `mirabelle-ha-blueprints` monorepo. It uses the official `imeon-inverter-api` Python package to communicate with Imeon inverters.

## Sources

- Official API package: https://github.com/Imeon-Inverters-for-Home-Assistant/inverter-api
- Home Assistant core integration (reference): https://github.com/home-assistant/core/tree/dev/homeassistant/components/imeon_inverter

## License

MIT License - see the main repository LICENSE file for details.
