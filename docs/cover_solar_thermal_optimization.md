# Smart Cover Solar & Thermal Optimization

This blueprint adjusts cover positions using key positions (`0`, `25`, `50`, `75`, `100`) based on:

- Sun position (`sun.sun` azimuth + daylight)
- Outdoor and indoor temperatures
- Wind speed
- Season mode (auto, summer, winter)
- Presence and awake state
- Facade orientation groups (north/east/south/west)
- Per-cover door/window contact sensors

> **Version 2 (breaking change).** The logic is now **stateless**: the two former helper
> inputs (`Action Priority Helper` and `Summer Shading Latch Helper`) and the
> `Control Strategy` preset were removed, night handling was unified, and the global contact
> inputs were replaced by **per-cover** contact links. See [Migration from v1](#migration-from-v1).

## Installation

1. Click this import link:

[Import Smart Cover Solar & Thermal Optimization Blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fcover_solar_thermal_optimization.yaml)

Or import manually:

1. Open Home Assistant
2. Go to **Blueprints**
3. Click **+** (bottom-right)
4. Select **Import Blueprint**
5. Paste:

```text
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/cover_solar_thermal_optimization.yaml
```

## Prerequisites

- Home Assistant `2025.5.3` or later
- Covers supporting `cover.set_cover_position` (0-100 position support). Covers without a
  `current_position` attribute are ignored (no open/close-only fallback).
- Optional outdoor temperature source:
  - an outdoor temperature sensor, or
  - a weather entity fallback (forecast first, then weather temperature)
- Optional indoor temperature sensor
- Optional wind speed sensor
- One or more `person` entities for home presence detection
- Optional awake source:
  - one awake entity (`input_boolean` or `binary_sensor`), or
  - one schedule helper (`schedule`)
  - if none is configured, awake defaults to daylight (`sun.sun` above horizon)

## Configuration

Inputs are grouped into collapsible sections in the UI.

### Covers & Orientation

- **All Managed Covers** (required): all covers controlled by the automation
- **North / East / South / West-Facing Covers** (optional): facade groups. If none is
  configured, all covers are treated as one group.

### Presence & Awake

- **Persons At Home**: select one or more persons; automation runs if at least one is `home`
- **Close Covers When Away**: if enabled, all managed covers close when nobody is home
- **Awake Entity (Optional)**: primary awake source when set (`on`/`home` = awake)
- **Awake Schedule (Optional)**: used when Awake Entity is empty (`on` = awake)
- If both are empty, daylight is used (`sun.sun` above horizon)

### Contact Sensors (Per Cover)

- **Cover ↔ Contact Sensor Links**: a list of entries, each linking **one cover** to **one or
  more** contact sensors. When any linked sensor of a cover is `on`, **that cover** moves to the
  Contact Open Position. Different covers can have a different number of sensors. This input is
  edited as a YAML object (a list of `cover` + `sensors` entries).
- **Contact Open Position**: position used for a cover while one of its linked sensors is open.

Example (bay windows with two sensors, french doors with one):

```yaml
cover_contact_links:
  - cover: cover.bay_window_left
    sensors:
      - binary_sensor.bay_window_left_top
      - binary_sensor.bay_window_left_bottom
  - cover: cover.bay_window_right
    sensors:
      - binary_sensor.bay_window_right_top
      - binary_sensor.bay_window_right_bottom
  - cover: cover.french_door_left
    sensors:
      - binary_sensor.french_door_left
  - cover: cover.french_door_right
    sensors:
      - binary_sensor.french_door_right
```

Contact opening overrides comfort logic and ignores manual override / anti-wear filtering, but
stays **below** the global safety branches (away / wind / night). It also applies regardless of
the awake state (an open door implies presence).

### Night & Wind Safety

- **Night Position**: position used at night (`0` = closed, the default). Set higher to keep
  covers partly open at night. This single input replaces the former
  `Close Covers At Night` + `Winter Night Position` pair.
- **Wind Speed Sensor (Optional)**: if empty, wind protection is disabled
- **Max Wind Speed**: wind safety threshold
- **Position With High Wind**: position used when wind is above the threshold

### Temperature Sources

- **Outdoor Temperature Sensor (Optional)**: primary outdoor source
- **Weather Entity (Optional Fallback)**: used when the outdoor sensor is empty
- **Indoor Temperature Sensor (Optional)**

Outdoor temperature priority:

1. Outdoor Temperature Sensor
2. Weather forecast temperature (first forecast item)
3. Weather current temperature attribute
4. `0` if no source is available (thermal branches are guarded and skipped in that case)

### Season

- **Season Mode**: `auto` (summer between configured dates), `summer`, or `winter`
- **Summer Start/End Month & Day (Auto Mode)**: cross-year ranges are supported

### Thermal Thresholds

- **Summer Close Temperature**: outdoor threshold for summer shading
- **Indoor Hot Temperature**: indoor threshold to activate summer shading
- **Winter Open Temperature Below**: outdoor threshold to favor winter solar gains
- **Winter Indoor Cold Temperature**: indoor threshold to favor winter solar gains
- **Temperature Hysteresis Buffer**: deadband in °C to reduce threshold oscillation
- **Sensor Stability Window (Minutes)**: minimum unchanged duration before using sensor values (`0`, `5`, `10`, `15`)

### Comfort Positions

Each value is selected from key positions (`0`, `25`, `50`, `75`, `100`):

- **Summer Position (Sun-Facing Facade)**: shading applied only to the facade under the sun
- **Winter Day Position (Solar Gains)**: open position applied only to the sun-facing facade
- **Winter Day Position (Insulating / No Gains)**: insulating position for the other facades in winter
- **Neutral Position**: open position for non-sun facades in summer and for all facades once cool

### Motion & Manual Override

- **Manual Override Hold (Minutes)**: hold a manually changed cover out of comfort/night moves for this duration
- **Minimum Position Delta**: ignore small comfort moves below this difference (default `10`)
- **Minimum Action Interval (Minutes)**: minimum delay between comfort moves for the same cover (default `5`)

Only the true safety branches (away / wind) and contact opening ignore the delta, interval and
manual override. **Night closing now respects manual override**, so a manual open in the evening
is held for the Manual Override duration instead of being reverted immediately.

## Behavior Summary

The automation reevaluates immediately on:

- Presence changes
- Managed cover state changes
- `sun.sun` state changes (daylight, azimuth)
- Awake entity/schedule changes
- A linked contact sensor opening or closing

Temperature, weather and wind changes are picked up on the **10-minute** re-evaluation
(thermal signals are slow, so they do not need instant triggers).

### Decision model

The automation computes a single global **mode**, then a **target position per cover**, then
applies each target through one loop (a cover absent from the target map is left untouched):

1. **Away** (safety): nobody home and *Close When Away* enabled → all covers to `0`
   (if *Close When Away* is disabled, nothing happens)
2. **Wind** (safety): wind above threshold → all covers to *Position With High Wind*
3. **Night**: sun below horizon → all covers to *Night Position* (respects manual override)
4. **Active** (daytime, someone home), decided **per cover**:
   1. a linked contact sensor is open → *Contact Open Position*
   2. not awake → no movement
   3. **summer + daylight** (follows the sun):
      - hot (`threshold + buffer`) → the sun-facing facade goes to *Summer Position (Sun-Facing Facade)*; every other facade goes to *Neutral Position* (stays open)
      - cool enough (`threshold - buffer`) → all facades to *Neutral Position*
      - in between → **hold** (no movement)
   4. **winter + daylight** (follows the sun):
      - solar gain needed (`threshold - buffer`) → the sun-facing facade goes to *Winter Day Position (Solar Gains)*; every other facade goes to *Winter Day Position (Insulating / No Gains)*
      - otherwise → all facades to *Winter Day Position (Insulating / No Gains)*

Only the facade currently exposed to the sun is shaded (summer) or opened for gains (winter);
the other facades are never closed against the heat nor left losing heat in winter. When **no
facade group** is configured, the blueprint cannot tell which side faces the sun, so it falls
back to applying the sun-facing behavior to **all** managed covers.

### Stateless anti-oscillation

Version 2 removes the external priority/latch helpers. Stability is achieved with:

- **Hysteresis**: summer hot uses `threshold + buffer`, release/gain checks use `threshold - buffer`
- **Hold band**: in the summer deadband, covers keep their current position (no helper needed)
- **No-op guard**: a cover is never commanded if it is already at its target
- **Minimum Position Delta** and **Minimum Action Interval** for comfort moves
- **Sensor Stability Window**: noisy sensor values are used only once stable
- Optional sensor entities are validated before use (`unknown`/`unavailable`/missing are ignored)

## Orientation Mapping

The sun-facing facade is inferred using `sun.sun` azimuth:

- East: `45° <= azimuth < 135°`
- South: `135° <= azimuth < 225°`
- West: `225° <= azimuth < 315°`
- North: all other azimuth values

If a facade group is empty for the current sun azimuth, all managed covers are treated as
sun-facing for shading (safety fallback).

## Example Profiles

### North/South House (common setup)

- Configure only `North-Facing Covers` and `South-Facing Covers`; leave east/west empty
- Suggested start: neutral `100`, summer sun-facing `25`, winter gains `100`, winter insulating `50`

### Aggressive Summer Shading

- Neutral: `100`
- Summer sun-facing: `0` or `25`
- Indoor hot temp: lower value (e.g. `23.5`)

## Migration from v1

If you used the previous version, re-import the blueprint and update your automation:

- **Removed** `Action Priority Helper` and `Summer Shading Latch Helper`: delete those inputs.
  You can also delete the `input_number` / `input_boolean` helpers if they were created only for
  this blueprint. Anti-oscillation is now handled internally.
- **Removed** `Control Strategy`: tune behavior directly with *Minimum Position Delta* and
  *Minimum Action Interval (Minutes)*.
- **Removed** `Close Covers At Night` + `Winter Night Position`: replaced by a single
  *Night Position* (set `0` to close at night, the previous default behavior).
- **Replaced** `Contact Sensors` + `Covers For Contact Opening` by **Cover ↔ Contact Sensor
  Links**: define one entry per cover with its own sensors (see the example above).
- **Removed** `Summer Position (Non Sun-Facing)`: in summer heat the non-sun facades now go to
  *Neutral Position* (open) instead of a partial-close position. Tune *Neutral Position* if needed.

Bug fixes included in v2:

- Summer shading no longer leaks into winter (season is now an explicit guard).
- The night position is reachable without configuring an awake entity (safety branches run
  before the awake gate).
- Comfort actions can no longer be blocked indefinitely (the priority helper is gone).
- Thermal modes now **follow the sun**: only the exposed facade is shaded in summer / opened for
  gains in winter, instead of moving every cover. Other facades stay open (summer) or insulated
  (winter).
- Night closing **respects manual override**: opening a cover manually in the evening is no longer
  reverted immediately.

## Troubleshooting

- **No movement**:
  - check selected persons (at least one must be `home`)
  - check `Close Covers When Away` option for away behavior
  - if Awake Entity is set, check awake state (`on` or `home`); if Awake Schedule is set, check `on`; otherwise behavior follows daylight
  - verify optional sensor availability (outdoor/weather, indoor, wind)
- **A cover never moves**: ensure it exposes `current_position` (the blueprint skips covers without it)
- **Unexpected facade selection**: verify facade groups and current `sun.sun` azimuth
- **Position service errors**: ensure the cover integration supports `cover.set_cover_position`
- **Too frequent movements**: increase `Minimum Position Delta` and/or `Minimum Action Interval (Minutes)`, or raise the hysteresis buffer
- **Contact opening does nothing**: verify the cover in the link is part of *All Managed Covers* and that its linked sensors report `on` when open
- **Manual move gets reverted too quickly**: increase `Manual Override Hold (Minutes)`
```
