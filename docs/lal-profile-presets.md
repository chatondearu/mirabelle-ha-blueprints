# LAL Profile Presets

Shared **profile value** packs (kelvin / brightness / night hue) as Home Assistant
helpers. Select a preset from each Living Area Adaptive Lighting automation, or keep
`local` to use that automation’s own inputs.

Schedule, privacy, and occupancy stay per room.

## Using a preset on one mode

In the automation editor, open e.g. **Night Profile**:

1. **Night Profile Enabled** — toggle the mode on/off
2. **Night Preset** — `Local` or a shared pack (`Starlight Blue`, `Ember Red`, `Soft Day`)
3. If **Local**: set hue/brightness and **Night Animation** in the same section
4. If a pack is selected: values + animation come from the preset helpers (`lal_preset_<id>_*`)

Each mode (morning / day / evening / night) has its own preset. They are independent.

| Id | Description |
|----|-------------|
| `starlight_blue` | Blue night (default look); animation `leaf_cloud` on night |
| `ember_red` | Red/amber night; animation `none` |
| `soft_day` | Softer day/morning/evening brightness |

Edit helpers under Developer Tools or a dashboard (entities
`input_number.lal_preset_<id>_*` and `input_select.lal_preset_<id>_animation`).

## Installation

1. Same `shell_command` as LAL mode helpers.
2. Import and run **[CDA] Create LAL Profile Presets**.
3. In each LAL automation, set **Profile Preset**.

[Import Create LAL Profile Presets](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate-lal-profile-presets.yaml)

## Animations

| Type | Effect |
|------|--------|
| `none` | No motion |
| `leaf_cloud` | Slow desynced brightness sway (leaves / clouds) |

Preset packages store animation type + amplitude + period. For **local** preset,
use the Local Animation inputs on the automation. Additional animation types can be
added later without changing the schedule model.

## Changelog

### 1.0.0

- Initial three presets + companion package script.
