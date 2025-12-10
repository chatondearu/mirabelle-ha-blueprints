# Cover Manager - Installation and Testing Guide

## Prerequisites

- Home Assistant 2025.5.3 or later
- HACS installed (for HACS installation method)
- A switch entity to control your cover/blind

## Installation Methods

### Method 1: Via HACS (Recommended)

**Important**: Cover Manager is automatically synced from the monorepo to a dedicated sub-repository for HACS installation.

1. **Add Custom Repository to HACS**
   - Open Home Assistant
   - Go to **HACS** > **Integrations**
   - Click the three dots (⋮) in the top right corner
   - Select **Custom repositories**
   - Add the following:
     - **Repository**: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`
     - **Category**: Integration
   - Click **Add**

2. **Install Cover Manager**
   - In HACS, search for "Cover Manager"
   - Click on **Cover Manager**
   - Click **Download**
   - Restart Home Assistant

3. **Configuration**
   - Choose the existing impulse switch controlling the cover.
   - Set travel time (seconds) and optional initial position (0-100).
   - No YAML includes are required. The integration manages state internally; the cover state is estimated in the entity.

**Note**: If Cover Manager doesn't appear in HACS, ensure:
- The sub-repository exists and is up to date (synced from monorepo)
- Your Home Assistant version is 2025.5.3 or later
- You're using the correct repository URL: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`

3. **Configure the Integration**
   - Go to **Settings** > **Devices & Services**
   - Click **Add Integration**
   - Search for "Cover Manager"
   - Click on it and follow the setup wizard

### Method 2: Manual Installation

1. **Download the Component**
   ```bash
   # Clone or download the repository
   git clone https://github.com/chatondearu/mirabelle-ha-blueprints.git
   cd mirabelle-ha-blueprints/packages/cover-manager
   ```

2. **Copy to Home Assistant**
   - Copy the `custom_components/cover_manager` folder to your Home Assistant `custom_components` directory
   - The path should be: `<config>/custom_components/cover_manager/`

3. **Restart Home Assistant**
   - Restart Home Assistant to load the custom component

4. **Configure the Integration**
   - Go to **Settings** > **Devices & Services**
   - Click **Add Integration**
   - Search for "Cover Manager"
   - Click on it and follow the setup wizard

## Configuration

### Setup Wizard Parameters

When adding the integration, you'll be asked for:

1. **Name**: The name of your cover (e.g., "Living Room Blind")
2. **Switch Entity**: The switch entity that controls your cover (e.g., `switch.living_room_blind`)
3. **Travel Time**: Time in seconds for the cover to travel from fully closed to fully open (1-300 seconds)

### Example Configuration

```
Name: Living Room Blind
Switch Entity: switch.living_room_blind
Travel Time: 30
```

## What Gets Created

After configuration, the integration automatically creates:

1. **Input Text Helpers**:
   - `input_text.living_room_blind_position` - Stores the current position (0-100)
   - `input_text.living_room_blind_direction` - Stores the direction (opening/closing/stopped)

2. **Cover Template Entity**:
   - `cover.living_room_blind` - The cover entity you can control

3. **Script** (if not already exists):
   - `script.set_cover_position` - Script to set cover position

4. **Configuration Files**:
   - `configuration/packages/cover_manager_<cover_id>_helpers.yaml` - Helper configuration
   - `configuration/covers.yaml` - Cover template configuration

## Testing the Integration

### 1. Verify Installation

1. **Check Integration Status**
   - Go to **Settings** > **Devices & Services**
   - Find **Cover Manager** in the list
   - Verify it shows as "Loaded" (green)

2. **Check Created Entities**
   - Go to **Settings** > **Devices & Services** > **Entities**
   - Search for your cover name (e.g., "Living Room Blind")
   - You should see:
     - `cover.living_room_blind` (or similar)
     - `input_text.living_room_blind_position`
     - `input_text.living_room_blind_direction`

### 2. Test Cover Controls

1. **Open the Cover**
   - Go to **Developer Tools** > **Services**
   - Service: `cover.open_cover`
   - Target: Select your cover entity (e.g., `cover.living_room_blind`)
   - Click **Call Service**
   - Verify:
     - The switch turns on
     - After the travel time, the switch turns off
     - The position helper updates to 100

2. **Close the Cover**
   - Service: `cover.close_cover`
   - Target: Your cover entity
   - Click **Call Service**
   - Verify:
     - The switch turns on
     - After the travel time, the switch turns off
     - The position helper updates to 0

3. **Set Specific Position**
   - Service: `cover.set_cover_position`
   - Target: Your cover entity
   - Service Data:
     ```yaml
     position: 50
     ```
   - Click **Call Service**
   - Verify:
     - The switch turns on
     - After half the travel time, the switch turns off
     - The position helper updates to 50

4. **Stop the Cover**
   - Service: `cover.stop_cover`
   - Target: Your cover entity
   - Click **Call Service**
   - Verify:
     - The switch turns off immediately
     - The direction helper updates to "stopped"

### 3. Test in Lovelace UI

1. **Add Cover Card**
   - Go to your dashboard
   - Click **Edit Dashboard**
   - Add a new card
   - Select **Entities** card
   - Add your cover entity
   - You should see:
     - A slider to control position (0-100%)
     - Buttons for Open/Close/Stop
     - Dynamic icon based on state

2. **Test UI Controls**
   - Use the slider to set position to 25%
   - Verify the cover moves
   - Click **Open** button
   - Verify the cover opens fully
   - Click **Stop** button
   - Verify the cover stops

### 4. Verify Helpers

1. **Check Position Helper**
   - Go to **Settings** > **Devices & Services** > **Helpers**
   - Find `input_text.living_room_blind_position`
   - Verify it updates when you control the cover

2. **Check Direction Helper**
   - Find `input_text.living_room_blind_direction`
   - Verify it shows:
     - "opening" when the switch is on and position is 0
     - "closing" when the switch is on and position is 100
     - "stopped" when the switch is off

## Troubleshooting

### Issue: Integration doesn't appear

**Solution:**
- Verify Home Assistant version is 2025.5.3 or later
- Check that the custom component is in the correct location: `<config>/custom_components/cover_manager/`
- Check the Home Assistant logs for errors
- Restart Home Assistant

### Issue: Cover entity doesn't appear

**Solution:**
- Check that `covers.yaml` is included in your `configuration.yaml`:
  ```yaml
  cover: !include covers.yaml
  ```
- Check Home Assistant logs for errors
- Verify the helpers were created successfully
- Try reloading YAML configurations: **Developer Tools** > **YAML** > **Reload All YAML Configurations**

### Issue: Cover doesn't respond to commands

**Solution:**
- Verify the switch entity exists and is accessible
- Check that the switch entity ID is correct
- Verify the travel time is appropriate for your cover
- Check Home Assistant logs for service call errors

### Issue: Position is incorrect

**Solution:**
- Verify the travel time is accurate
- Reset the position helper manually:
  - Go to **Settings** > **Devices & Services** > **Helpers**
  - Edit `input_text.<cover_name>_position`
  - Set value to current actual position
- Recalibrate by fully opening and closing the cover

### Issue: Helpers not created

**Solution:**
- Check that the `packages` directory exists: `<config>/configuration/packages/`
- Verify file permissions allow writing
- Check Home Assistant logs for errors
- Manually create helpers if needed:
  ```yaml
  input_text:
    living_room_blind_position:
      name: "Living Room Blind Position"
      initial: "0"
      min: 0
      max: 100
      mode: box
    living_room_blind_direction:
      name: "Living Room Blind Direction"
      initial: "stopped"
      mode: text
  ```

## Logs and Debugging

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.cover_manager: debug
```

Then restart Home Assistant and check the logs for detailed information.

### Check Logs

1. Go to **Settings** > **System** > **Logs**
2. Filter for "cover_manager" or "Cover Manager"
3. Look for errors or warnings

## Uninstallation

1. **Remove Integration**
   - Go to **Settings** > **Devices & Services**
   - Find **Cover Manager**
   - Click on it
   - Click **Delete** (trash icon)
   - Confirm deletion

2. **Remove Files** (if manual installation)
   - Delete `<config>/custom_components/cover_manager/`
   - Restart Home Assistant

3. **Clean Up Configuration** (optional)
   - Remove helper files from `configuration/packages/`
   - Remove cover configuration from `configuration/covers.yaml`
   - Reload YAML configurations

## Next Steps

After successful installation and testing:

1. **Create Automations**
   - Use the cover entity in automations
   - Example: Open blinds at sunrise, close at sunset

2. **Use with Blueprints**
   - Use the `[CDA] 🪟 Cover Control` blueprint
   - Use the `[CDA] 🪟 Blind State Tracker` blueprint

3. **Integrate with Energy Dashboard**
   - The cover entity can be used in energy monitoring if needed

## Support

If you encounter issues:

1. Check the [Home Assistant Community Forum](https://community.home-assistant.io/)
2. Check the [GitHub Issues](https://github.com/chatondearu/mirabelle-ha-blueprints/issues)
3. Review the logs for error messages
4. Verify all prerequisites are met
