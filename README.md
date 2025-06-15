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
     ```bash
     cp .env.example .env
     ```
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
- `HA_URL`: Home Assistant URL (default: http://supervisor/core)
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

# Cover Manager

Une intégration Home Assistant pour gérer facilement les volets contrôlés par des interrupteurs.

## Fonctionnalités

- Configuration simple via l'interface web
- Création automatique des helpers nécessaires
- Support des positions (0-100%)
- Icônes dynamiques selon l'état
- Support multilingue (FR/EN)

## Installation

### Via HACS (recommandé)

1. Assurez-vous que [HACS](https://hacs.xyz/) est installé
2. Ajoutez ce repository dans HACS
3. Recherchez "Cover Manager"
4. Cliquez sur "Installer"

### Installation manuelle

1. Téléchargez les fichiers
2. Copiez le dossier `cover_manager` dans votre dossier `custom_components`
3. Redémarrez Home Assistant

## Configuration

1. Allez dans Configuration > Intégrations
2. Cliquez sur "Ajouter une intégration"
3. Recherchez "Cover Manager"
4. Suivez les instructions à l'écran

### Paramètres

| Paramètre | Description | Obligatoire |
|-----------|-------------|-------------|
| Nom | Nom du volet | Oui |
| Entité Switch | Switch qui contrôle le volet | Oui |
| Temps de Trajet | Temps en secondes pour ouvrir/fermer | Oui |

## Utilisation

Une fois configuré, le volet apparaîtra dans votre interface avec :
- Un slider pour contrôler la position
- Des boutons pour ouvrir/fermer/arrêter
- Des icônes dynamiques selon l'état

## Dépannage

1. **Le volet n'apparaît pas**
   - Vérifiez que l'intégration est bien installée
   - Redémarrez Home Assistant

2. **Le volet ne répond pas**
   - Vérifiez que le switch est bien configuré
   - Vérifiez les helpers dans Configuration > Helpers

3. **Position incorrecte**
   - Vérifiez le temps de trajet
   - Réinitialisez les helpers

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le repository
2. Créer une branche
3. Faire vos modifications
4. Soumettre une pull request

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails. 