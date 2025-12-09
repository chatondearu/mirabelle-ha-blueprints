# Cover Manager

A Home Assistant custom integration to easily manage covers controlled by switches.

## ⚠️ Important: HACS Installation

This custom component is part of a monorepo structure. It is automatically synced to a dedicated sub-repository for HACS installation.

**Use the dedicated repository for HACS:**
- Repository: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`
- This repository is automatically synced from the monorepo

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for detailed installation instructions.

### Quick Start (HACS)

1. Add repository to HACS: `https://github.com/chatondearu/myrabelle-hacs-cover-manager`
2. Search for "Cover Manager" in HACS
3. Click **Download**
4. Restart Home Assistant
5. Configure via **Settings** > **Devices & Services** > **Add Integration**
6. Include generated covers in `configuration.yaml`:
   ```yaml
   cover: !include_dir_merge_list config/covers
   ```

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

## Configuration

1. Go to Configuration > Integrations
2. Click "Add Integration"
3. Search for "Cover Manager"
4. Follow the on-screen instructions

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| Name | Name of the cover | Yes |
| Switch Entity | Switch that controls the cover | Yes |
| Travel Time | Time in seconds to open/close | Yes |

## Usage

Once configured, the cover will appear in your interface with:
- A slider to control the position
- Buttons to open/close/stop
- Dynamic icons based on state

## Troubleshooting

1. **Cover doesn't appear**
   - Verify that the integration is installed
   - Restart Home Assistant

2. **Cover doesn't respond**
   - Verify that the switch is configured correctly
   - Check helpers in Configuration > Helpers

3. **Incorrect position**
   - Verify the travel time
   - Reset the helpers

## Development

This component is part of the `mirabelle-ha-blueprints` monorepo. It is automatically synced to a dedicated sub-repository (`myrabelle-hacs-cover-manager`) for HACS installation via GitHub Actions.

See [HACS_SETUP.md](./HACS_SETUP.md) and [.github/MONOREPO_SYNC.md](../../.github/MONOREPO_SYNC.md) for details on the sync process.

## License

MIT License - see the main repository LICENSE file for details.


## Other

Similar projects:
- https://github.com/duhow/hass-cover-time-based/tree/main
- https://github.com/jo-ket/compact-cover-control-card
- https://github.com/marcelhoogantink/enhanced-shutter-card
