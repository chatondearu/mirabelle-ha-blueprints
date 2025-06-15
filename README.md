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

#### Scripts
- [[CDA] 🔊 Play Sound with Volume Control](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fplay_sound_with_volume_control.yaml)
- [[CDA] 📅 Create Schedule](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate_schedule.yaml)

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
```

#### Scripts
```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/scripts/play_sound_with_volume_control.yaml
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/scripts/create_schedule.yaml
```

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

## Repository Structure

```
mirabelle-ha-blueprints/
├── blueprints/
│   ├── automations/
│   │   └── scheduled_bell_sound.yaml
│   └── scripts/
│       ├── play_sound_with_volume_control.yaml
│       └── create_schedule.yaml
├── docs/
│   ├── scheduled_bell_sound.md
│   ├── play_sound_with_volume_control.md
│   └── create_schedule.md
└── README.md
```

## Development

### Prerequisites
- Node.js (for version management)
- Git

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

### Version Management
- Use semantic versioning
- Update version in package.json
- Run `npm version` to create a new version
- The script will automatically commit and tag the changes

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 