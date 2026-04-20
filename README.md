# Mirabelle HA Blueprints

A collection of custom blueprints for Home Assistant.

## Installation

### Quick Start

1. Go to your Home Assistant instance
2. Click on "Blueprints" in the sidebar
3. Click on the "+" button in the bottom right corner
4. Click on "Import Blueprint"
5. Click on one of the following links to import a blueprint:

#### Automations

- [[CDA] 🔔 Scheduled Bell Sound](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fscheduled_bell_sound.yaml)
- [[CDA] 💡 Presence Based Lighting](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fpresence_based_lighting.yaml)
- [[CDA] 🪟 Cover Control](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fcover_control.yaml)
- [[CDA] 🪟 Blind Cover Template](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fcover_cover.yaml)
- [[CDA] 🪟 Blind State Tracker](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fcover_state_tracker.yaml)
- [Keypad Frient (KEPZB-110) for Alarmo by Darktoinon (FR/EN)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Ffrient_keypad_with_alarmo.yaml)

#### Scripts

- [[CDA] 🔊 Play Sound with Volume Control](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fplay_sound_with_volume_control.yaml)
- [[CDA] 📅 Create Schedule](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate_schedule.yaml)
- [[CDA] 🪟 Set Cover Position](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fset_cover_position.yaml)

### Manual Installation

If the quick links don't work, you can manually import the blueprints:

1. Go to your Home Assistant instance
2. Click on "Blueprints" in the sidebar
3. Click on the "+" button in the bottom right corner
4. Click on "Import Blueprint"
5. Copy and paste one of the following URLs:

#### Automations

```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/scheduled_bell_sound.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/presence_based_lighting.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/cover_control.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/cover_cover.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/cover_state_tracker.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/frient_keypad_with_alarmo.yaml
```

#### Scripts

```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/scripts/play_sound_with_volume_control.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/scripts/create_schedule.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/scripts/set_cover_position.yaml
```

## Custom Components

### Cover Manager

[Cover Manager](packages/cover-manager/README.md) - A Home Assistant custom integration to easily manage covers controlled by switches.

**Installation via HACS:**

1. Add the dedicated sub-repository as a custom repository in HACS:
  - **Repository**: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`
  - **Category**: Integration
2. Search for "Cover Manager" and install
3. Restart Home Assistant and configure via Settings > Devices & Services

**Note**: Cover Manager is automatically synced from this monorepo to the dedicated sub-repository. See [Monorepo Sync Documentation](.github/MONOREPO_SYNC.md) for details.

See [Cover Manager Installation Guide](packages/cover-manager/INSTALLATION.md) for detailed instructions.

## Available Blueprints

### Scheduled Bell Sound

[CDA] 🔔 Scheduled Bell Sound
Play a bell sound at specific times with volume control. Supports time-based triggers, sun events, and custom triggers.

[View Documentation](docs/scheduled_bell_sound.md)

### Play Sound with Volume Control

[CDA] 🔊 Play Sound with Volume Control
A script to play sounds with automatic volume control and restoration.

[View Documentation](docs/play_sound_with_volume_control.md)

### Create Schedule

[CDA] 📅 Create Schedule
A helper script to easily create schedules for your automations.

[View Documentation](docs/create_schedule.md)

### Presence Based Lighting

[CDA] 💡 Presence Based Lighting
Automatically control lights based on presence detection with configurable delay.

[View Documentation](docs/presence_based_lighting.md)

### Cover Control

[CDA] 🪟 Cover Control
Control a cover using a switch with position support (0-100%).

### Blind Cover Template

[CDA] 🪟 Blind Cover Template
Helper automation to track the state of a blind controlled by a single switch.

### Blind State Tracker

[CDA] 🪟 Blind State Tracker
Track the state of a blind controlled by a single switch.

[View Documentation](docs/blind_states.md)

### Keypad Frient for Alarmo

Keypad Frient (KEPZB-110) for Alarmo by Darktoinon (FR/EN)

Manage multiple PIN codes to arm and disarm an alarm using the Frient keypad, synchronizing state with an Alarmo alarm panel or another alarm control panel. English and French UI strings.

This blueprint does not use the `[CDA]` name prefix, so it is excluded from `pnpm run install-blueprints` (that script only processes names starting with `[CDA]`). Use the import links above or install it manually.

### Set Cover Position

[CDA] 🪟 Set Cover Position
Set a cover to a specific position using a switch with travel time calculation.

## Repository Structure

```
mirabelle-ha-blueprints/
├── blueprints/
│   ├── automations/
│   │   ├── scheduled_bell_sound.yaml
│   │   ├── presence_based_lighting.yaml
│   │   ├── cover_control.yaml
│   │   ├── cover_cover.yaml
│   │   ├── cover_state_tracker.yaml
│   │   └── frient_keypad_with_alarmo.yaml
│   └── scripts/
│       ├── play_sound_with_volume_control.yaml
│       ├── create_schedule.yaml
│       └── set_cover_position.yaml
├── docs/
│   ├── scheduled_bell_sound.md
│   ├── play_sound_with_volume_control.md
│   ├── create_schedule.md
│   ├── presence_based_lighting.md
│   ├── blind_states.md
│   └── cover_generator.md
└── README.md
```

## Development

### Prerequisites

- Node.js 18+ (for version management and scripts)
- Git

### Setup

1. Clone the repository
2. Install dependencies:
  ```bash
   pnpm i
  ```

### Version Management

- Use semantic versioning
- Update version in package.json
- Run `npm version` to create a new version
- The script will automatically commit and tag the changes

### Updating Automations

To automatically update all automations in your Home Assistant instance:

1. Get your Home Assistant token:
  - Go to your Home Assistant profile
  - Scroll to the bottom
  - Create a long-lived access token
2. Configure environment variables:
  - Copy `.env.example` to `.env`:
  - Edit `.env` and set your Home Assistant token:
    ```env
    HA_URL=http://your_ha_instance:8123
    HA_TOKEN=your_long_lived_access_token
    ```
3. Run the update script:
  ```bash
   pnpm run update-automations
  ```

The script will:

- Find all blueprints in the repository
- Get all automations from your Home Assistant instance
- Update automations that match the blueprints
- Preserve your automation configurations

Note: Only automations with names starting with "[CDA]" will be updated.

### Installing Blueprints

To install all blueprints in your Home Assistant instance:

1. Make sure you have configured your `.env` file as described above
2. Run the installation script:
  ```bash
   pnpm run install-blueprints
  ```

The script will:

- Find all blueprints in the repository
- Install them in your Home Assistant instance
- Show the installation status for each blueprint

Note: Only blueprints with names starting with "[CDA]" will be installed.

Available environment variables:

- `HA_URL`: Home Assistant URL (default: [http://supervisor/core](http://supervisor/core))
- `HA_TOKEN`: Your long-lived access token (required)
- `HA_VERIFY_SSL`: Enable/disable SSL verification (default: true)
- `HA_TIMEOUT`: Request timeout in seconds (default: 30)

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.