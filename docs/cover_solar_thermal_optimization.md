# Smart Cover Solar & Thermal Optimization

This blueprint adjusts cover positions using key positions (`0`, `25`, `50`, `75`, `100`) based on:

- Sun position (`sun.sun` azimuth + daylight)
- Outdoor and indoor temperatures
- Wind speed
- Season mode (auto, summer, winter)
- Presence and awake state
- Facade orientation groups (north/east/south/west)

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
- Covers supporting `cover.set_cover_position` (0-100 position support)
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

### Required Inputs

- **All Managed Covers**: all covers controlled by the automation
- **Persons At Home**: select one or more persons; automation runs if at least one is `home`
- **Awake Entity (Optional)**: primary awake source when set
- **Awake Schedule (Optional)**: used when Awake Entity is empty
- **Fallback awake mode**: if both are empty, daylight is used (`sun.sun` above horizon)
- **Outdoor Temperature Sensor (Optional)**: primary outdoor temperature source
- **Weather Entity (Optional Fallback)**: used when Outdoor Temperature Sensor is empty
- **Indoor Temperature Sensor (Optional)**
- **Wind Speed Sensor (Optional)**: if empty, wind protection is disabled

### Optional Facade Inputs

- **North-Facing Covers**
- **East-Facing Covers**
- **South-Facing Covers**
- **West-Facing Covers**

If no facade group is configured, all covers are treated as one group.

### Season and Thermal Inputs

- **Season Mode**:
  - `auto` = Apr-Sep as summer, Oct-Mar as winter
  - `summer` = force summer behavior
  - `winter` = force winter behavior
- **Summer Close Temperature**: outdoor threshold for summer shading
- **Winter Open Temperature Below**: outdoor threshold to favor winter solar gains
- **Indoor Hot Temperature**: indoor threshold to activate summer shading
- **Winter Indoor Cold Temperature**: indoor threshold to favor winter solar gains
- **Max Wind Speed**: wind safety threshold

Sensor fallback behavior:

- Outdoor temperature priority:
  1. Outdoor Temperature Sensor
  2. Weather forecast temperature (first forecast item)
  3. Weather current temperature attribute
  4. `0` if no source is available
- Indoor temperature: `0` when no indoor sensor is configured
- Wind: disabled when no wind sensor is configured

### Position Inputs

Each value is selected from key positions (`0`, `25`, `50`, `75`, `100`):

- **Position With High Wind**
- **Winter Night Position**
- **Summer Position (Non Sun-Facing)**
- **Summer Position (Sun-Facing Facade)**
- **Winter Day Position (Solar Gains)**
- **Winter Day Position (No Solar Gains Needed)**
- **Neutral Position**

## Behavior Summary

The automation reevaluates on:

- Presence changes
- Awake source changes (entity/schedule) trigger an immediate reevaluation
- Indoor/outdoor/weather temperature changes
- Wind speed changes (if wind sensor configured)
- `sun.sun` state changes
- Every 10 minutes

Decision order:

1. **Wind high**: all managed covers move to `Position With High Wind`
2. **Winter night**: all managed covers move to `Winter Night Position`
3. **Summer hot** (indoor or outdoor threshold reached):
   - all covers move to `Summer Position (Non Sun-Facing)`
   - sun-facing facade moves to `Summer Position (Sun-Facing Facade)`
4. **Winter day and heat gain needed**:
   - all covers move to `Winter Day Position (Solar Gains)`
5. **Fallback**:
   - winter daylight: `Winter Day Position (No Solar Gains Needed)`
   - otherwise: `Neutral Position`

When optional sensors are missing:

- Summer/winter thermal decisions use only available temperature sources
- Wind safety branch is skipped if no wind sensor is configured

Awake gating priority:

1. If **Awake Entity** is set, it is used (`on`/`home` = awake)
2. Else if **Awake Schedule** is set, it is used (`on` = awake)
3. Else daylight is used (`sun.sun` above horizon = awake)

## Orientation Mapping

The sun-facing facade is inferred using `sun.sun` azimuth:

- East: `45° <= azimuth < 135°`
- South: `135° <= azimuth < 225°`
- West: `225° <= azimuth < 315°`
- North: all other azimuth values

## Example Profiles

### North/South House (common setup)

- Configure only `North-Facing Covers` and `South-Facing Covers`
- Leave east/west empty
- Suggested start:
  - Summer non-sun: `75`
  - Summer sun-facing: `25`
  - Winter gains: `100`
  - Winter no gains: `50`

### Aggressive Summer Shading

- Summer non-sun: `50`
- Summer sun-facing: `0` or `25`
- Indoor hot temp: lower value (e.g. `23.5`)

## Troubleshooting

- **No movement**:
  - check selected persons (at least one must be `home`)
  - if Awake Entity is set, check awake state (`on` or `home`)
  - if Awake Schedule is set, check schedule state (`on`)
  - if none is set, behavior follows daylight
  - verify optional sensor availability (outdoor/weather, indoor, wind)
- **Unexpected facade selection**:
  - verify facade groups and current `sun.sun` azimuth
- **Position service errors**:
  - ensure the cover integration supports `cover.set_cover_position`
- **Too frequent movements**:
  - increase thresholds or reduce trigger sensitivity (duplicate sensors can cause many updates)
