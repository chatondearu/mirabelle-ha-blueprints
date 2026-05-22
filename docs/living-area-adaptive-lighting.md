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
- Optional helpers: `input_select` (manual mode), `input_boolean` (manual hold)

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
- Average cover position at or above **Cover Shade Threshold** (and lux is not above **Lux Bright Threshold** — hysteresis)

If the zone is occupied but none of the above apply (bright day, open covers), lights are turned off.

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
| Night Start (Fallback) | Optional time for night without lux | empty |
| Day Start (Fallback) | Optional day window start without lux | empty |

Use **Lux Dark** lower than **Lux Bright** to avoid flicker when lux hovers near a single threshold.

### Covers

| Parameter | Description | Default |
|-----------|-------------|---------|
| Living Area Covers | Optional cover entities | `[]` |
| Cover Shade Threshold | Average position % to trigger day lighting | `60` |

Average uses `current_position` (0 = open, 100 = closed). If no covers are selected, shading factor is `0`.

### Night profile

| Parameter | Description | Default |
|-----------|-------------|---------|
| Night Hue Base | Base hue (blue ~235) | `235` |
| Night Hue Spread | Per-lamp hue variation ± | `15` |
| Night Saturation | Saturation % | `85` |
| Night Brightness (Color) | % | `40` |
| Night Brightness (White) | % | `15` |

### Day profile

| Parameter | Description | Default |
|-----------|-------------|---------|
| Day Kelvin Minimum | Warmest (evening) | `2700` |
| Day Kelvin Maximum | Coolest (midday) | `4000` |
| Day Brightness Minimum | % | `35` |
| Day Brightness Maximum | % | `100` |
| Cover Kelvin Warm Shift | Kelvin subtracted at 100% closed average | `300` |

### Manual control

| Parameter | Description | Default |
|-----------|-------------|---------|
| Manual Mode Helper | `input_select`: `auto`, `day`, `night`, `off` | empty |
| Manual Hold Helper | `input_boolean`: when `on`, automation skips all actions | empty |
| Light Transition | Seconds | `3` |

### Optional helpers (UI)

Create in **Settings → Helpers**:

```yaml
# input_select.living_area_lighting_mode
options:
  - auto
  - day
  - night
  - off

# input_boolean.living_area_lighting_hold
```

Map them in the blueprint under **Manual Control**.

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

## Changelog

### 1.0.0

- Initial release: computed day/night profiles, occupancy + optional persons, lux and cover shading, manual helpers.
