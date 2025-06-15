# Mirabelle Home Assistant Blueprints

A collection of custom blueprints for my Home Assistant configuration. This repository contains reusable automations, scripts, and scenes for Home Assistant.

## Installation

### Method 1: HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository to HACS:
   - Go to HACS > Integrations
   - Click on the three dots in the top right
   - Select "Custom repositories"
   - Add: `https://github.com/chatondearu/mirabelle-ha-blueprints`

### Method 2: Manual

1. Clone this repository into your Home Assistant `config` folder:
   ```bash
   cd /config
   git clone https://github.com/chatondearu/mirabelle-ha-blueprints.git
   ```
2. Import the blueprints through the Home Assistant web interface
3. Customize the blueprints according to your needs

## Repository Structure

```
.
├── README.md
├── package.json
├── commitlint.config.js
├── blueprints/
│   ├── automations/     # Automation blueprints
│   ├── scripts/         # Script blueprints
│   ├── scenes/          # Scene blueprints
│   └── dashboards/      # Dashboard blueprints
└── docs/               # Additional documentation
```

## Blueprint Categories

### Automations
- Presence-based automations
- Time-based automations
- Sensor-based automations
- Weather-based automations

### Scripts
- Routine scripts
- Maintenance scripts
- Configuration scripts

### Scenes
- Daily scenes
- Special scenes
- Vacation scenes

### Dashboards
- Main dashboards
- Mobile dashboards
- Specific dashboards

## Development

### Installation

```bash
# Install dependencies
npm install
```

### Version Management

This project uses semantic versioning (SemVer) for version management. Versions are managed through the `package.json` file.

#### Commit Format

Commits must follow the conventional format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Allowed commit types:
- `feat` : New feature
- `fix` : Bug fix
- `docs` : Documentation
- `style` : Formatting
- `refactor` : Code refactoring
- `perf` : Performance improvement
- `test` : Tests
- `chore` : Maintenance
- `ci` : CI configuration
- `build` : Build
- `revert` : Revert

#### Version Update

To update the project version:

1. Use the `npm version` command:
   ```bash
   npm version patch  # For bug fixes (0.0.x)
   npm version minor  # For new features (0.x.0)
   npm version major  # For major changes (x.0.0)
   ```

2. Git tags will be automatically created and pushed

## Contribution

Blueprints are organized by category and include detailed documentation in each file. Each blueprint contains:
- Clear description
- Prerequisites
- Configurable variables
- Usage examples

## License

This project is licensed under MIT. See the LICENSE file for more details. 