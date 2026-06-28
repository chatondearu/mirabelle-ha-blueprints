# Living Area Adaptive Lighting

Computed day and night lighting profiles for living areas (living room, dining room, open plan zones). No Home Assistant scenes are required: the blueprint calculates colors, color temperature, and brightness from occupancy, illuminance, sun position, and optional cover shading.

For simple on/off presence control on a single light, see [Presence Based Lighting](presence_based_lighting.md).

## Installation

1. Click this import link:

[Import Living Area Adaptive Lighting Blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fliving-area-adaptive-lighting.yaml)

Or import manually:

1. Open Home Assistant
2. Go to **Blueprints**
3. Click **+** (bottom-right)
4. Select **Import Blueprint**
5. Paste:

```text
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/living-area-adaptive-lighting.yaml
```

## Prerequisites

- Home Assistant `2025.5.3` or later
- At least one occupancy `binary_sensor` for the living area (motion, mmWave, room occupied, or a template helper)
- One or more controllable `light` entities (split into color-capable and white-only lists)
- Recommended: illuminance sensor (`sensor` reporting lux)
- Optional: `cover` entities in the same area (for shading factor)
- Optional: `person` entities when using **Require Someone Home**
- **Automatic dashboard helpers** (recommended): one-time `shell_command` in `configuration.yaml` (see below)
- Optional: existing `input_select` / `input_boolean` overrides instead of auto-created helpers

## How It Works

```text
Occupancy ON + need artificial light + someone home (if required)
  -> Night profile (sun down / forced night): blue starlight on color lights, dim white lights
  -> Day profile: warm-to-cool kelvin from sun elevation, brightness from lux + cover shading

Occupancy OFF (after delay) / manual off / away
  -> All configured lights off
```

### Night profile (starlight)

- Color lights: `hs_color` around a configurable blue hue with **stable per-lamp variation** (derived from each `entity_id`, so the look does not change on every trigger).
- White lights: low `brightness_pct` only (no forced hue).

### Day profile

- **Kelvin**: interpolated between `day_kelvin_min` (low sun) and `day_kelvin_max` (high sun, capped at 45° elevation), then warmed when average cover position is higher.
- **Brightness**: higher when lux is lower; boosted when covers are more closed.

### When artificial light is needed

Lighting runs only if the zone is occupied and at least one of:

- Night (sun below horizon, or optional night time window)
- Illuminance below **Lux Dark Threshold**
- Average **closed** amount at or above **Cover Shade Threshold** (mostly closed blinds), even if the lux sensor still reads bright near a window

If the zone is occupied but none of the above apply (bright day, open blinds), the automation does **not** force lights on and does **not** turn them off (leaves current state unchanged).

If the zone is **not** occupied, lights are turned off after the delay.

## Configuration

### Lights

| Parameter | Description | Default |
|-----------|-------------|---------|
| Color Lights | RGB/HS-capable lights | (required list) |
| White Lights | White-only or dimmable white lights | `[]` |

### Presence

| Parameter | Description | Default |
|-----------|-------------|---------|
| Occupancy Sensors | Binary sensors for the zone (any `on` = occupied) | (required) |
| Persons At Home | Optional `person` entities | `[]` |
| Require Someone Home | Only run when a selected person is `home` | `false` |
| Delay Before Turning Off | Seconds after all sensors are `off` | `300` |

### Ambient light

| Parameter | Description | Default |
|-----------|-------------|---------|
| Illuminance Sensor | Optional lux sensor | empty |
| Lux Dark Threshold | Below this: need light (lx) | `80` |
| Lux Bright Threshold | Above this: suppress day lighting (lx) | `120` |
| Night Start | Time the night window begins; empty = sunset | empty |
| Night End (Day Start) | Time the night window ends; empty = sunrise | empty |

The night window now drives the day/night profile selection regardless of the lux sensor: leave both empty to follow the sun, or pin one/both to fixed times (handy in winter to keep day starting at the same hour). When only one is set, the other falls back to the corresponding sun time.

Use **Lux Dark** lower than **Lux Bright** to avoid flicker when lux hovers near a single threshold.

### Covers

| Parameter | Description | Default |
|-----------|-------------|---------|
| Living Area Covers | Optional cover entities | `[]` |
| Cover Shade Threshold | Average position % to trigger day lighting | `60` |

Average **closed** amount uses `100 - current_position` (Home Assistant: 0 = closed, 100 = open). Example: blinds 25% open → position `25` → **75% closed** toward the default threshold of `60`. If no covers are selected, closed factor is `0`.

### Night profile

| Parameter | Description | Default |
|-----------|-------------|---------|
| Night Hue Base | Base hue (blue ~235) | `235` |
| Night Hue Spread | Per-lamp hue variation ± | `15` |
| Night Saturation | Saturation % | `85` |
| Night Brightness (Color) | % (ramp floor when ramp enabled) | `40` |
| Night Brightness (White) | % (ramp floor when ramp enabled) | `15` |
| Night Brightness Ramp | Start bright at night start, fade to the values above | `false` |
| Night Brightness Start (Ramp) | Starting % at night start when ramp is on | `70` |
| Night Dim Until | Time the ramp reaches its minimum | `00:00:00` |

When **Night Brightness Ramp** is on, night brightness starts at **Night Brightness Start** at night start and linearly fades down to **Night Brightness (Color/White)** by **Night Dim Until** (midnight by default), then stays at the floor for the rest of the night.

### Day/Night transition

| Parameter | Description | Default |
|-----------|-------------|---------|
| Progressive Transition | Blend night↔day across a sun elevation band | `false` |
| Transition Elevation Low | Sun elevation where transition starts (night side) | `-6` |
| Transition Elevation High | Sun elevation where transition completes (day) | `6` |
| Transition Warm Kelvin | Warmest color temperature at the horizon (golden hour) | `2200` |

When enabled (auto mode only), instead of switching abruptly at sunrise/sunset, all capable lamps blend from a warm **Transition Warm Kelvin** at the horizon up to the day color temperature, with brightness interpolated from the night to the day level, recreating outdoor light. Below the low elevation the night (blue) profile applies; above the high elevation the day profile applies.

### Day profile

| Parameter | Description | Default |
|-----------|-------------|---------|
| Day Kelvin Minimum | Warmest (evening) | `2700` |
| Day Kelvin Maximum | Coolest (midday) | `4000` |
| Day Brightness Minimum | % | `35` |
| Day Brightness Maximum | % | `100` |
| Cover Kelvin Warm Shift | Kelvin subtracted at 100% closed average | `300` |

### Manual control (dashboard helpers)

| Parameter | Description | Default |
|-----------|-------------|---------|
| Create Dashboard Control Helpers | Auto-create helpers on Home Assistant start | `true` |
| Control Helper Slug | Base id slug (`input_select.{slug}_mode`, `input_boolean.{slug}_hold`) | `living_area_lighting` |
| Mode Helper Display Name | Friendly name for mode dropdown | `Living Area Lighting Mode` |
| Hold Helper Display Name | Friendly name for hold toggle | `Living Area Lighting Hold` |
| Manual Mode Helper Override | Use an existing `input_select` instead of auto id | empty |
| Manual Hold Helper Override | Use an existing `input_boolean` instead of auto id | empty |
| Manual Override Hold | Pause the automation after a manual light change | `false` |
| Manual Override Duration | How long to stay paused (minutes) | `30` |
| Light Transition | Seconds | `3` |

When **Manual Override Hold** is on, turning on at least one light of the group by hand (UI, app or voice) pauses the automation for **Manual Override Duration**, so it neither changes nor turns off the lights during that window. Detection uses the change context user, so physical/Zigbee switch actions may not be recognized as manual.

With default settings, the automation expects:

- `input_select.living_area_lighting_mode` — options: `auto`, `day`, `night`, `off`
- `input_boolean.living_area_lighting_hold` — when `on`, the automation does not change lights

### Automatic helper creation (recommended)

Home Assistant cannot create UI helpers from an automation blueprint alone. Use the **companion script** once after importing the automation.

#### One-time setup

1. Ensure packages are loaded (common default):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

2. Add this `shell_command` (see also [`templates/living-area-lighting-shell-command.yaml`](../templates/living-area-lighting-shell-command.yaml)):

```yaml
shell_command:
  cda_write_living_area_lighting_helper_package: >
    /bin/bash -c 'echo "{{ content_b64 }}" | base64 -d > "/config/packages/{{ package_filename }}"'
```

3. Reload **Shell commands** (or restart Home Assistant).

4. Create the lighting automation with **Create Dashboard Control Helpers** enabled (default).

5. Import and run the companion script blueprint (same slug and names as the automation):

Import the companion script blueprint:

[Import Create Living Area Lighting Helpers](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fcreate-living-area-lighting-helpers.yaml)

Create a script from it (same slug and names as the automation), then run it once from **Developer Tools → Actions** or from the script card in your dashboard.

#### Disable auto-creation

Turn off **Create Dashboard Control Helpers** and either:

- Leave overrides empty (mode stays `auto`, no hold), or
- Map **Manual Mode Helper Override** / **Manual Hold Helper Override** to helpers you created yourself.

## Usage Example

One automation instance for an open living + dining area:

- **Color lights**: `light.salon_rgb_1`, `light.salon_rgb_2`
- **White lights**: `light.salon_plafond`, `light.salle_manger_spots`
- **Occupancy**: `binary_sensor.salon_occupancy`, `binary_sensor.salle_manger_motion`
- **Illuminance**: `sensor.salon_illuminance`
- **Covers**: same covers as [Smart Cover Solar & Thermal Optimization](cover_solar_thermal_optimization.md) if installed
- **Persons**: `person.alice`, `person.bob` with **Require Someone Home** enabled

## Troubleshooting

### Lights never turn on

- Confirm at least one occupancy sensor is `on` in Developer Tools → States.
- Check lux: if above **Lux Bright**, day lighting is suppressed unless covers exceed the shade threshold.
- If **Require Someone Home** is on, verify a selected `person` is `home`.
- Check **Manual Hold** is `off` and **Manual Mode** is not `off`.

### Lights flicker on/off

- Increase **Lux Bright** vs **Lux Dark** gap (hysteresis).
- Increase **Delay Before Turning Off**.
- Use `mode: restart` behavior: avoid overlapping automations on the same lights.

### Night blue does not apply

- Confirm sun is below horizon (or set **Manual Mode** to `night`).
- Color lights must be in **Color Lights**, not **White Lights**.

### Kelvin not applied on some bulbs

- Some lights only accept `color_temp` or `rgb`. If kelvin fails, check the light integration; you may need to move the entity to **Color Lights** or use a compatible bulb profile.

### Covers ignored

- Covers must report `current_position`. Template or switch-only covers without position do not contribute to the average.

### Lights turn off while I am in the room

- Check **Developer Tools → States** for cover `current_position` (25% open = `25`, not `75`).
- Lower **Cover Shade Threshold** if your blinds report unusual positions.
- Lower **Lux Dark Threshold** if the room feels dark but lux stays between dark and bright thresholds.
- Confirm **Manual Hold** is off and mode is not `off`.

### Dashboard helpers not created

- Confirm `shell_command.cda_write_living_area_lighting_helper_package` exists and **Shell commands** were reloaded.
- Confirm `/config/packages/` exists and `homeassistant.packages` includes that folder.
- Check **Settings → System → Logs** after restart for shell_command errors.
- Run the **[CDA] Create Living Area Lighting Helpers** script manually with the same slug.
- As a fallback, create helpers in the UI and set **Manual Mode Helper Override** / **Manual Hold Helper Override**.

## Changelog

### 1.2.0

- Add an optional **progressive day/night transition** that recreates outdoor light: lamps blend from a warm golden-hour color temperature near the horizon up to daylight across a configurable sun elevation band (and the reverse at sunset).
- The **night window** (Night Start / Night End) now defines the day/night profile selection regardless of the lux sensor, defaulting to sun times — set fixed times to control it yourself (useful in winter).
- Add an optional **night brightness ramp**: start bright at night start and fade down to the night brightness floor by a configurable time (midnight by default).
- Add an optional **manual override hold**: turning on a light by hand pauses the automation for a configurable duration.

### 1.1.6

- Fix lights never turning on during the day: `is_time_night` and `lux_needs_light` emitted the literal string `false` instead of a boolean. As a result `is_night` became the truthy string `"false"`, which short-circuited `need_artificial_light` and made both the day and night branches evaluate to false. Emit real booleans via `{{ false }}`.

### 1.1.5

- Fix the companion helper script blueprint structure: the script body (`sequence`, `mode`) was wrapped in an extra `script:` key, which made Home Assistant reject script creation with `extra keys not allowed @ data['script']`. Move them to the top level as required for script blueprints.

### 1.1.4

- Fix the companion helper script package template: use a literal block scalar (`|`) instead of a folded one (`>`). The folded scalar collapsed the comment line and `input_select:` onto a single line, producing an invalid package file that Home Assistant refused to load.

### 1.1.3

- Fix companion helper script: use the `base64_encode` template filter (the previous `b64encode` did not exist and aborted the script).
- Quote the `off` option so the generated `input_select` exposes `off` as a string instead of the YAML boolean `false`.
- Reload via `homeassistant.reload_all` so newly written helpers are picked up (`reload_core_config` did not load them, causing a false failure notification).

### 1.1.2

- Remove helper package write from automation (fixes setup validation error); use companion script only.

### 1.1.1

- Fix cover position semantics (HA: 0 = closed, 100 = open); use closed factor `100 - position`.
- Covers mostly closed now trigger lighting even when outdoor lux is high.
- Occupied but bright/open room: no longer forces lights off (default branch idle).

### 1.1.0

- Automatic dashboard helper creation on Home Assistant start (package file + core reload).
- Companion script blueprint for manual helper setup.
- Helper slug and display names configurable; optional entity overrides retained.

### 1.0.0

- Initial release: computed day/night profiles, occupancy + optional persons, lux and cover shading, manual helpers.
