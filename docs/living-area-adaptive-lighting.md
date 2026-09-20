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
  -> Night: blue starlight (late "night simulation" window)
  -> Evening: warm, capped brightness from dusk until night start
  -> Morning: soft profile after night ends
  -> Day: warm-to-cool kelvin from sun elevation, brightness from lux + covers

Occupancy OFF (after delay) / manual off / away
  -> All configured lights off
```

Priority in **auto** mode: `night > evening > morning > day`.

### Night profile (starlight)

- Color lights: `hs_color` around a configurable blue hue with **stable per-lamp variation** (derived from each `entity_id`, so the look does not change on every trigger).
- White lights: low `brightness_pct` only (no forced hue).
- Night is the late simulation window (e.g. fixed 22:30), **not** simply sunset.

### Evening / morning / day profiles

- **Kelvin**: interpolated between each profile’s min/max from sun elevation, then warmed when covers are more closed.
- **Brightness**: higher when lux is lower; boosted when covers are more closed; evening/morning max defaults stay below full day to avoid a sudden 100% jump after sunset when night start is late.

### Open-cover privacy

When average cover **open** position is at or above **Cover Open Privacy Threshold**:

- **block** — do not turn lights on for low lux (night profile can still run)
- **cap** — allow lighting but clamp brightness to **Open Covers Brightness Cap**
- **off** — legacy behavior

### When artificial light is needed

Lighting runs only if the zone is occupied and at least one of:

- Active profile is **night**
- Active profile is **evening** (unless open-cover privacy is **block**)
- Illuminance below the effective lux dark threshold (skipped when privacy is **block**)
- Average **closed** amount at or above **Cover Shade Threshold**

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
| Lux Dark (Covers Open) | Stricter dark threshold when covers open; `0` = reuse dark | `0` |
| Lux Bright (Covers Open) | Stricter bright threshold when covers open; `0` = reuse bright | `0` |

Use **Lux Dark** lower than **Lux Bright** to avoid flicker when lux hovers near a single threshold.

### Profile schedule

| Parameter | Description | Default |
|-----------|-------------|---------|
| Night Start (Fixed Time) | Clock time when night trigger is `fixed_time`; empty → `22:00` if evening enabled else sunset | empty |
| Night End / Morning Start | Ends night / can start morning; empty → sunrise | empty |
| Night Trigger | `fixed_time` / `sunset` / `sunrise` / `sun_elevation` | `fixed_time` |
| Night Delay | Minutes after night trigger (negative = earlier) | `0` |
| Night Elevation | Elevation threshold for night when trigger is elevation | `-12` |
| Evening Profile Enabled | Dusk profile until night | `true` |
| Evening Trigger | `sunset` / `fixed_time` / `sun_elevation` | `sunset` |
| Evening Fixed Time | When evening trigger is fixed | `18:00:00` |
| Evening Elevation | Elevation for evening start | `0` |
| Evening Delay | Minutes after evening trigger | `0` |
| Morning Profile Enabled | Soft profile after night | `true` |
| Morning Trigger | `fixed_time` / `sunrise` / `sun_elevation` | `fixed_time` |
| Morning Fixed Time | Empty → reuse Night End time | empty |
| Morning Elevation | Elevation for morning start | `-6` |
| Morning Delay | Minutes after morning trigger | `0` |
| Morning Duration | Morning length (minutes) | `180` |

### Covers

| Parameter | Description | Default |
|-----------|-------------|---------|
| Living Area Covers | Optional cover entities | `[]` |
| Cover Shade Threshold | Average closed % to trigger lighting | `60` |
| Cover Open Privacy Threshold | Average open % where privacy policy applies | `50` |
| Open Covers Privacy Policy | `block` / `cap` / `off` | `block` |
| Open Covers Brightness Cap | Max % when policy is `cap` | `25` |

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

### Morning / day / evening profiles

| Parameter | Description | Default |
|-----------|-------------|---------|
| Morning Kelvin Min / Max | Soft morning CT | `2500` / `3500` |
| Morning Brightness Min / Max | Soft morning brightness | `25` / `70` |
| Day Kelvin Min / Max | Day CT | `2700` / `4000` |
| Day Brightness Min / Max | Day brightness | `35` / `100` |
| Cover Kelvin Warm Shift | Kelvin subtracted at 100% closed | `300` |
| Evening Kelvin Min / Max | Evening CT | `2200` / `3000` |
| Evening Brightness Min / Max | Evening brightness (caps the post-sunset spike) | `25` / `55` |

### Horizon transition

| Parameter | Description | Default |
|-----------|-------------|---------|
| Progressive Transition | Blend across a sun elevation band near the horizon | `false` |
| Transition Elevation Low | Night side of the band | `-6` |
| Transition Elevation High | Day side of the band | `6` |
| Transition Warm Kelvin | Warmest CT at the horizon (golden hour) | `2200` |

When enabled (auto mode only), lamps blend across the elevation band. Outside the band, morning/day/evening/night apply normally — after dusk and before night start, **evening** is used instead of full day brightness.

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

- `input_select.living_area_lighting_mode` — options: `auto`, `morning`, `day`, `evening`, `night`, `off`
- `input_boolean.living_area_lighting_hold` — when `on`, the automation does not change lights

**Migration:** existing helpers created before 1.3.0 only have `auto/day/night/off`. Re-run the companion script after deleting the old package helper, or edit the `input_select` options to add `morning` and `evening`.

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

### Lights turn on at 100% after sunset while night starts later

- Enable **Evening Profile** (default on). Evening uses its own brightness max (default 55%), not day max.
- Confirm **Night Start** is your simulation time (e.g. 22:30) and **Evening Trigger** is sunset (or elevation).
- Re-import/reload the blueprint after upgrading to 1.3.0+.

### Lights turn on while covers are still open at dusk

- Set **Open Covers Privacy Policy** to `block` (default) or `cap`.
- Adjust **Cover Open Privacy Threshold** (default 50% open).

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

### 1.5.0

- Per-mode **Preset** (`local` / shared packs) and **Animation** on Night / Morning / Day / Evening sections.
- Empty/`local` preset uses that section’s manual config (including animation).
- Removed the single global Profile Preset selector.

### 1.4.0

- Add **profile presets** (`local` / `starlight_blue` / `ember_red` / `soft_day`) via package helpers.
- Add pluggable **animations** (`none`, `leaf_cloud`) with per-lamp brightness sway.
- Optional **Follow Global Profile Hub** for shared morning/day/evening/night mode.

### 1.3.0

- Add **morning** and **evening** profiles (kelvin + brightness min/max) so a late fixed night start no longer forces full **day** brightness after sunset.
- Add **profile schedule** triggers (`sunrise` / `sunset` / `sun_elevation` / `fixed_time`) with postpone delays for night, evening, and morning.
- Add **open-cover privacy** policy: `block` or brightness `cap` when covers are mostly open.
- Manual mode helper options: `auto`, `morning`, `day`, `evening`, `night`, `off`.

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
