# Imeon Energy API - Installation and Configuration Guide

## Prerequisites

- Home Assistant 2025.5.3 or later
- HACS installed (for HACS installation method)
- Imeon OS One v1.8.1.0 or later (released in January 2025)
- Ethernet (ETH) port connection to your inverter (WiFi connection lacks NAT feature)
- Network access to your Imeon inverter on your local network
- Inverter IP address, username, and password

## Installation Methods

### Method 1: Via HACS (Recommended)

**Important**: Imeon Energy API is automatically synced from the monorepo to a dedicated sub-repository for HACS installation.

1. **Add Custom Repository to HACS**
   - Open Home Assistant
   - Go to **HACS** > **Integrations**
   - Click the three dots (⋮) in the top right corner
   - Select **Custom repositories**
   - Add the following:
     - **Repository**: `https://github.com/chatondearu/myrabelle-hacs-imeon-energy`
     - **Category**: Integration
   - Click **Add**

2. **Install Imeon Energy API**
   - In HACS, search for "Imeon Energy API"
   - Click on **Imeon Energy API**
   - Click **Download**
   - Restart Home Assistant

3. **Configure the Integration**
   - Go to **Settings** > **Devices & Services**
   - Click **Add Integration**
   - Search for "Imeon Energy API"
   - Click on it and follow the setup wizard

### Method 2: Manual Installation

1. **Download the Component**
   ```bash
   # Clone or download the repository
   git clone https://github.com/chatondearu/mirabelle-ha-blueprints.git
   cd mirabelle-ha-blueprints/packages/imeon_energy_api
   ```

2. **Copy to Home Assistant**
   - Copy the `custom_components/imeon_energy_api` folder to your Home Assistant `custom_components` directory
   - The path should be: `<config>/custom_components/imeon_energy_api/`

3. **Restart Home Assistant**
   - Restart Home Assistant to load the custom component

4. **Configure the Integration**
   - Go to **Settings** > **Devices & Services**
   - Click **Add Integration**
   - Search for "Imeon Energy API"
   - Click on it and follow the setup wizard

## Configuration

### Setup Wizard Parameters

When adding the integration, you'll be asked for:

1. **Host**: The IP address of your Imeon inverter (no protocol, e.g., `192.168.1.100`)
2. **Username**: The username for your inverter
3. **Password**: The password for your inverter
4. **Update Interval**: How often to poll data from the inverter (default: 30 seconds, range: 10-300 seconds)

### Example Configuration

```
Host: 192.168.1.100
Username: admin
Password: ********
Update Interval: 30 seconds
```

### Finding Your Inverter IP Address

1. **Check Inverter Display**: Some inverters display the IP address on their screen
2. **Router Admin Panel**: Check your router's connected devices list
3. **Network Scanner**: Use a network scanning tool to find devices on your network
4. **Inverter Web Interface**: If you can access the web interface, the IP is in the URL

## What Gets Created

After configuration, the integration creates the following sensors:

### Energy Sensors (kWh, total_increasing)

- `sensor.<host>_grid_consumption` - Grid energy consumption
- `sensor.<host>_grid_return` - Grid energy return
- `sensor.<host>_solar_production` - Solar energy production
- `sensor.<host>_battery_charging` - Battery energy charging
- `sensor.<host>_battery_discharging` - Battery energy discharging

### Power Sensors (W, measurement)

- `sensor.<host>_grid_power` - Grid power (positive = import, negative = export)
- `sensor.<host>_solar_power` - Solar power production
- `sensor.<host>_battery_power` - Battery power (positive = charging, negative = discharging)
- `sensor.<host>_home_power` - Home power consumption

### Battery Sensor

- `sensor.<host>_battery_soc` - Battery state of charge (%)

Where `<host>` is your inverter IP address with dots replaced by underscores (e.g., `192_168_1_100`).

## Energy Dashboard Configuration

### Setting Up the Energy Dashboard

1. **Go to Energy Dashboard**
   - Navigate to **Settings** > **Dashboards** > **Energy**
   - If you don't have an Energy Dashboard yet, click **Add Dashboard** > **Energy**

2. **Configure Grid Consumption**
   - Click **Configure** next to "Grid consumption"
   - Select your grid consumption sensor: `sensor.<host>_grid_consumption`
   - If you have return to grid, also select: `sensor.<host>_grid_return`

3. **Configure Solar Production**
   - Click **Configure** next to "Solar panels"
   - Select your solar production sensor: `sensor.<host>_solar_production`

4. **Configure Battery**
   - Click **Configure** next to "Battery"
   - Select:
     - **Energy Charging**: `sensor.<host>_battery_charging`
     - **Energy Discharging**: `sensor.<host>_battery_discharging`
     - **State of Charge**: `sensor.<host>_battery_soc`

5. **Save Configuration**
   - Click **Save** to apply your configuration

### Energy Dashboard Tips

- **Wait for Data**: Energy sensors start at 0 and accumulate over time. Wait a few minutes after installation for meaningful data.
- **Check Sensor States**: Ensure all sensors show values (not `unknown` or `unavailable`)
- **Update Interval**: A shorter update interval (10-30s) provides more accurate energy calculations but uses more resources
- **Multiple Inverters**: If you have multiple inverters, you can add multiple integrations

## Testing the Integration

### 1. Verify Installation

1. **Check Integration Status**
   - Go to **Settings** > **Devices & Services**
   - Find **Imeon Energy API** in the list
   - Verify it shows as "Loaded" (green)
   - Click on it to see connection status

2. **Check Created Sensors**
   - Go to **Settings** > **Devices & Services** > **Entities**
   - Filter by "Imeon Energy"
   - You should see all the sensors listed above

### 2. Test Sensor Values

1. **Check Power Sensors**
   - Go to **Developer Tools** > **States**
   - Search for your power sensors (e.g., `sensor.192_168_1_100_solar_power`)
   - Verify they show current power values in watts
   - Values should update every 30 seconds (or your configured interval)

2. **Check Energy Sensors**
   - Check energy sensors (e.g., `sensor.192_168_1_100_solar_production`)
   - Initially, they may show 0.0 kWh (this is normal)
   - After a few minutes, values should start accumulating
   - Values should only increase (total_increasing state class)

3. **Check Battery Sensor**
   - Check `sensor.<host>_battery_soc`
   - Should show a percentage between 0-100%

### 3. Test in Energy Dashboard

1. **View Energy Dashboard**
   - Go to **Settings** > **Dashboards** > **Energy**
   - You should see graphs for:
     - Grid consumption/return
     - Solar production
     - Battery charging/discharging
     - Home consumption

2. **Verify Data Updates**
   - Wait a few minutes
   - Refresh the dashboard
   - Verify data is updating and graphs are showing trends

## Troubleshooting

### Issue: Integration doesn't connect

**Symptoms:**
- Error during setup: "Failed to connect to Imeon inverter"
- Integration shows as "Failed to load"

**Solutions:**
- Verify your inverter IP address is correct and reachable from Home Assistant
- Check that your username and password are correct
- Ensure Imeon OS One v1.8.1.0 or later is installed on your inverter
- Verify you're using Ethernet connection (not WiFi)
- Check your network firewall isn't blocking the connection
- Try accessing the inverter web interface from the same network as Home Assistant
- Check Home Assistant logs for detailed error messages

### Issue: Sensors don't appear

**Symptoms:**
- Integration loads but no sensors are created
- Sensors show as `unknown` or `unavailable`

**Solutions:**
- Check Home Assistant logs for errors
- Verify the integration is loaded (green status)
- Restart Home Assistant
- Check that the coordinator is successfully fetching data
- Verify your inverter is powered on and connected to the network

### Issue: Energy values are zero or not accumulating

**Symptoms:**
- Energy sensors show 0.0 kWh
- Values don't increase over time

**Solutions:**
- Wait a few minutes - energy sensors integrate power over time
- Verify power sensors are showing non-zero values
- Check that the update interval is appropriate (not too long)
- Verify your inverter is actually producing/consuming energy
- Check Home Assistant logs for integration errors

### Issue: Sensors don't appear in Energy Dashboard

**Symptoms:**
- Sensors exist but don't show in Energy Dashboard configuration

**Solutions:**
- Verify sensors have correct attributes:
  - `device_class: energy`
  - `state_class: total_increasing`
  - `unit_of_measurement: kWh`
- Ensure sensors are showing values (not `unknown`)
- Wait a few minutes for energy values to accumulate
- Check Developer Tools > Statistics for sensor statistics errors

### Issue: Incorrect values

**Symptoms:**
- Power or energy values seem incorrect
- Negative values where they shouldn't be

**Solutions:**
- Grid power: Positive = importing, Negative = exporting (this is correct)
- Battery power: Positive = charging, Negative = discharging (this is correct)
- Verify your inverter's actual readings match
- Check if the API response structure matches what the integration expects
- Enable debug logging to see raw API responses

## Logs and Debugging

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.imeon_energy_api: debug
```

Then restart Home Assistant and check the logs for detailed information.

### Check Logs

1. Go to **Settings** > **System** > **Logs**
2. Filter for "imeon_energy_api" or "Imeon Energy"
3. Look for errors or warnings
4. Check coordinator update messages

### Common Log Messages

- `"Imeon Energy API setup completed"` - Integration loaded successfully
- `"Error fetching Imeon Energy data"` - Connection or API error
- `"Failed to connect to Imeon inverter"` - Initial connection failed

## Uninstallation

1. **Remove Integration**
   - Go to **Settings** > **Devices & Services**
   - Find **Imeon Energy API**
   - Click on it
   - Click **Delete** (trash icon)
   - Confirm deletion

2. **Remove Files** (if manual installation)
   - Delete `<config>/custom_components/imeon_energy_api/`
   - Restart Home Assistant

3. **Clean Up Energy Dashboard** (optional)
   - Go to **Settings** > **Dashboards** > **Energy**
   - Remove sensors from Energy Dashboard configuration
   - Or remove the entire Energy Dashboard if no longer needed

## Next Steps

After successful installation and configuration:

1. **Monitor Your Energy**
   - Use the Energy Dashboard to track your energy consumption and production
   - Create automations based on energy levels
   - Set up notifications for low battery or high consumption

2. **Create Automations**
   - Example: Notify when battery is fully charged
   - Example: Turn on devices when solar production is high
   - Example: Reduce consumption when grid import is high

3. **Integrate with Other Systems**
   - Use energy data in other Home Assistant integrations
   - Export data to external systems
   - Create custom dashboards

## Support

If you encounter issues:

1. Check the [Home Assistant Community Forum](https://community.home-assistant.io/)
2. Check the [GitHub Issues](https://github.com/chatondearu/mirabelle-ha-blueprints/issues)
3. Review the logs for error messages
4. Verify all prerequisites are met
5. Check the official Imeon API documentation: https://github.com/Imeon-Inverters-for-Home-Assistant/inverter-api
