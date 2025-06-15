# Cover Generator

This system allows automatic generation of cover configurations for Home Assistant from a template.

## Description
A tool to generate Home Assistant cover configurations using command-line arguments and a template system. It supports position tracking, dynamic icons, and predefined positions.

## Prerequisites
- Node.js 16 or later
- pnpm package manager
- Home Assistant instance
- Required directories structure

## Installation

1. Ensure dependencies are installed:
   ```bash
   pnpm install
   ```

2. Verify the following directories exist:
   - `templates/` : Contains the configuration template
   - `configuration/` : Will contain the generated configuration
   - `scripts/` : Contains the generation script

## Usage

### Generating Configuration

To generate a cover configuration, use the command:

```bash
pnpm tsx scripts/generate_cover.ts <name> <switch_entity> <travel_time>
```

Arguments:
- `name` : Cover name (in quotes if contains spaces)
- `switch_entity` : Switch entity controlling the cover
- `travel_time` : Time in seconds to fully open/close the cover

Example:
```bash
pnpm tsx scripts/generate_cover.ts "Living Room Cover" switch.living_room_cover 30
```

### Home Assistant Configuration

1. Ensure `configuration/covers.yaml` is included in your `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named configuration
   ```

2. Restart Home Assistant to apply changes.

3. The cover will appear in the interface with a slider.

4. Use the `cover_state_tracker.yaml` blueprint to track the cover state.

## File Structure

```
.
├── configuration/
│   └── covers.yaml        # Generated configuration
├── templates/
│   └── cover_template.txt # Configuration template
└── scripts/
    └── generate_cover.ts  # Generation script
```

## Features

- Automatic cover configuration generation
- Support for predefined positions (0%, 25%, 50%, 75%, 100%)
- Dynamic icons based on cover state
- YAML validation
- Input text helpers management

## Configuration

| Parameter | Description | Required |
|-----------|-------------|----------|
| name | Cover name | Yes |
| switch_entity | Switch entity ID | Yes |
| travel_time | Time in seconds | Yes |

## Troubleshooting

1. **YAML Validation Error**:
   - Verify arguments are correct
   - Ensure template is valid

2. **Cover Not Visible in Interface**:
   - Check `covers.yaml` is included in `configuration.yaml`
   - Restart Home Assistant

3. **Script Error**:
   - Verify all arguments are provided
   - Ensure `travel_time` is a number

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.