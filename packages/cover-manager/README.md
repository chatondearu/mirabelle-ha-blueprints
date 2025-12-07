# Cover Manager

A Home Assistant custom integration to easily manage covers controlled by switches.

## ⚠️ Important: HACS Installation

This custom component is part of a monorepo structure. For HACS installation to work correctly:

1. **Use GitHub Releases**: HACS will download the component from GitHub releases, not directly from the repository
2. **Release Tags**: Releases must be tagged as `cover-manager-v*` (e.g., `cover-manager-v1.0.0`)
3. **Zip File**: Each release must include `cover_manager.zip` with the correct structure

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for detailed installation instructions.

### Quick Start (HACS)

1. Add repository to HACS: `https://github.com/chatondearu/mirabelle-ha-blueprints`
2. Search for "Cover Manager" in HACS
3. Install from the latest release
4. Restart Home Assistant
5. Configure via **Settings** > **Devices & Services** > **Add Integration**

## Features

- Simple configuration via web interface
- Automatic creation of required helpers
- Position support (0-100%)
- Dynamic icons based on state
- Multilingual support (EN/FR)

## Testing

See [TESTING.md](./TESTING.md) for a complete testing checklist.

## Repository Structure

```
packages/cover-manager/
├── custom_components/
│   └── cover_manager/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── cover.py
│       ├── manifest.json
│       └── ...
├── hacs.json
├── INSTALLATION.md
├── TESTING.md
└── README.md
```

## Development

This component is part of the `mirabelle-ha-blueprints` monorepo. The GitHub release workflow automatically creates a zip file with the correct structure for HACS.

## License

MIT License - see the main repository LICENSE file for details.
