# Reversible Split Thermostat (PAC)

A lightweight pair of blueprints to manage several reversible splits connected to
a single heat pump (PAC), for both winter heating and summer cooling. It is a
focused alternative to large heating blueprints: it keeps only the features that
matter for a multi-split PAC and adds first-class cooling support.

It is built around **two global setpoint helpers** (comfort and eco) that drive
every split, exactly like a whole-house thermostat.

## Why two blueprints?

A reversible PAC **cannot heat one room while cooling another** at the same time.
To guarantee this, the heat/cool/off decision is centralized:

| Blueprint | Instances | Role |
| --- | --- | --- |
| **[CDA] 🔁 HVAC Season Manager** | 1 | Owns the single global mode. Resolves `off / heat / cool / auto` into one shared "resolved mode" helper. |
| **[CDA] 🌡️ Reversible Split Thermostat** | 1 per split | Applies the resolved mode to its split and computes the room target. Never decides heat vs cool. |

Because every split reads the **same** resolved-mode helper, they always run the
same mode. No split can ever be in `heat` while another is in `cool`.

```
 input_select.climate_season_mode  (you set: off / heat / cool / auto)
                 │
        [CDA] HVAC Season Manager      ── resets comfort/eco on season change
                 │  writes
                 ▼
 input_select.climate_hvac_active  (off / heat / cool)
                 │  read by every split
   ┌─────────────┼─────────────┬─────────────┬─────────────┐
   ▼             ▼             ▼             ▼             ▼
 split A       split B       split C       split D       split E
 (one [CDA] Reversible Split Thermostat automation each)
```

## Prerequisites

- Home Assistant **2025.5.3** or later.
- Reversible `climate` entities (one per split) exposing `heat` and `cool`.
- A per-room temperature sensor for each split.
- The helpers listed below.

## Required helpers

Create these once (Settings → Devices & Services → Helpers), or paste the YAML
package below into `configuration.yaml` (or a package file) and restart.

| Helper | Type | Options / value | Purpose |
| --- | --- | --- | --- |
| `input_select.climate_season_mode` | Dropdown | `off`, `heat`, `cool`, `auto` | The mode you set. Replaces a winter on/off boolean. |
| `input_select.climate_hvac_active` | Dropdown | `off`, `heat`, `cool` | Resolved mode, written by the Season Manager. |
| `input_number.climate_comfort_thermostat` | Number | min 5, max 32, step 0.5 | Comfort setpoint (shared). |
| `input_number.climate_eco_thermostat` | Number | min 5, max 32, step 0.5 | Eco setpoint (shared). |
| `input_number.climate_night_thermostat` | Number | min 5, max 32, step 0.5 | Optional night setpoint for bedrooms (shared). |

```yaml
# Example package: config/packages/cda_climate_helpers.yaml
input_select:
  climate_season_mode:
    name: Climate Season Mode
    options:
      - "off"
      - heat
      - cool
      - auto
    icon: mdi:hvac
  climate_hvac_active:
    name: Climate HVAC Active
    options:
      - "off"
      - heat
      - cool
    icon: mdi:thermostat-auto

input_number:
  climate_comfort_thermostat:
    name: Comfort Thermostat
    min: 5
    max: 32
    step: 0.5
    unit_of_measurement: "°C"
    icon: mdi:sofa
  climate_eco_thermostat:
    name: Eco Thermostat
    min: 5
    max: 32
    step: 0.5
    unit_of_measurement: "°C"
    icon: mdi:leaf
  climate_night_thermostat:
    name: Night Thermostat
    min: 5
    max: 32
    step: 0.5
    unit_of_measurement: "°C"
    icon: mdi:bed
```

> The comfort and eco helpers are shared between seasons. Their meaning follows
> the active mode: in heat, eco is **lower** than comfort; in cool, eco is
> **higher**. The Season Manager rewrites their values on each season change (see
> "Seasonal setpoint defaults").

## Installation

Import both blueprints:

- [[CDA] 🔁 HVAC Season Manager](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fhvac-season-manager.yaml)
- [[CDA] 🌡️ Reversible Split Thermostat](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Freversible-split-thermostat.yaml)

Then:

1. Create **one** automation from the HVAC Season Manager.
2. Create **one automation per split** from the Reversible Split Thermostat.

## HVAC Season Manager parameters

| Parameter | Default | Description |
| --- | --- | --- |
| Season Mode Helper (user) | — | `input_select` with `off / heat / cool / auto`. |
| Resolved Mode Helper (output) | — | `input_select` with `off / heat / cool`, written by this automation. |
| Outdoor Temperature Sensor | — | Used only in `auto`. Empty = keep current mode in auto. |
| Auto Heat Below | 16 °C | In `auto`, switch to heat at/below this outdoor temperature. |
| Auto Cool Above | 24 °C | In `auto`, switch to cool at/above this outdoor temperature. |
| Comfort Setpoint Helper | — | `input_number` rewritten on season change. |
| Eco Setpoint Helper | — | `input_number` rewritten on season change. |
| Apply Seasonal Defaults | true | Reset comfort/eco on each heat ↔ cool transition. |
| Night Setpoint Helper | — | Optional `input_number` for bedrooms, also reset on season change. |
| Heat — Comfort / Eco Default | 19 / 17.5 °C | Values written when switching to heat. |
| Cool — Comfort / Eco Default | 25 / 27 °C | Values written when switching to cool. |
| Heat / Cool — Night Default | 17 / 21 °C | Night helper values written on each transition. |

**Auto with hysteresis:** between *Auto Heat Below* and *Auto Cool Above* the
resolved mode is unchanged, which prevents the PAC from flapping between heat and
cool around a single threshold. Keep a wide gap between the two values.

## Reversible Split Thermostat parameters

| Parameter | Default | Description |
| --- | --- | --- |
| Split (climate) | — | The reversible split for this room. |
| Room Temperature Sensor | — | Sensor used to evaluate this room. |
| Resolved Mode Helper | — | Same `input_select.climate_hvac_active` for every split. |
| Comfort / Eco Setpoint Helper | — | The two shared `input_number` helpers. |
| Comfort Schedules | [] | Comfort while any schedule is on, otherwise eco. Empty = always comfort. |
| Persons | [] | When set and nobody home, the away offset is applied. |
| Vacation / Away Toggle | — | Optional `input_boolean`; on = apply away offset. |
| Away Offset | 3 °C | Subtracted from target in heat, added in cool. |
| Presence Delay | 120 s | Stability delay before reacting to presence changes. |
| Night Schedule | [] | While any is on, the night setpoint overrides comfort/eco. |
| Night Setpoint Helper | — | `input_number` for the night target (preferred; seasonal via the Season Manager). |
| Night Setpoint (fixed fallback) | 0 | Fixed night target when no helper is set. 0 disables. |
| Window / Door Sensors | [] | While any is open, the split is turned off. |
| Room Sensor Control (bang-bang) | true | Trust the room sensor: drive the split beyond the target to heat/cool hard, then fully stop it once the room reaches the target. Off = the split self-regulates at the plain target. |
| Boost Offset | 2 °C | Degrees added (heat) / subtracted (cool) to the split target while conditioning, to overcome an inaccurate internal sensor. 0 = drive at target. |
| Cut Hysteresis | 0.3 °C | Deadband to avoid rapid on/off (protects the PAC). Restart only after dropping this far below target (heat) or rising above (cool). |
| Frost Protection (heat) | 7 °C | In heat, keep this minimum instead of full off when idle. 0 disables. |
| Outdoor Temperature Sensor | — | Optional, for the seasonal idle thresholds below. |
| Heat — Outdoor Above Idle | 20 °C | In heat, do not heat at/above this outdoor temperature. |
| Cool — Outdoor Below Idle | 18 °C | In cool, do not cool at/below this outdoor temperature. |
| Minimum Run Time | 0 s | Keep the split on at least this long after starting before stopping it on target reached (anti short-cycle). 0 disables. Window open / global Off still stop it immediately. |
| Adaptive Boost | true | Reduce the boost as the room approaches the target (soft landing, less overshoot). |
| Adaptive Boost Span | 2 °C | Distance from target over which the boost ramps from full to zero. |

## How the target is computed

1. **Night override** (optional): while a night schedule is on and a night
   setpoint is configured, the night setpoint is used and takes priority over
   comfort/eco. Otherwise, **comfort or eco**: comfort while a schedule is active
   (or always if no schedule), otherwise eco.
2. **Away offset**: when nobody is home (or vacation is on), the target is
   lowered in heat and raised in cool by the away offset.
3. **Idle (off)**: if a window is open, or the outdoor temperature makes
   conditioning useless, or (with Room Sensor Control on) the room reached the
   target, the split is turned off — with heat frost protection kept if
   configured.
4. Otherwise the split is set to the global mode. With **Room Sensor Control**
   on, the setpoint is pushed beyond the target by the **Boost Offset** to force
   full-power operation (the room sensor, not the split internal sensor, decides
   when to stop). With it off, the plain target is used and the split regulates
   itself. The setpoint is clamped to the split `min_temp` / `max_temp`.

### Bang-bang control (Room Sensor Control)

This reproduces the behavior of advanced heating blueprints for splits whose
internal sensor is unreliable (it sits inside the unit and reads the blown air):

- **Heat**: while the room sensor is below target, the split runs at
  `target + boost` so it heats hard; it is turned fully off once the room sensor
  reaches the target, and restarts only after dropping `cut_hysteresis` below it.
- **Cool**: symmetric — the split runs at `target - boost` while the room is
  above target, and stops once the room sensor reaches the target.

Set **Boost Offset** to 0 to keep the exact target while still cutting on the
room sensor, or disable **Room Sensor Control** to let the split self-regulate.

### Compressor protection

- **Adaptive Boost** (on by default): the boost shrinks linearly as the room
  gets within **Adaptive Boost Span** of the target. Far from target the split
  runs at `target ± boost`; near the target it drives close to the plain target,
  so it slows down before stopping instead of overshooting.
- **Minimum Run Time**: after the split starts, it stays on at least this long
  before it can be stopped because the target is reached. This avoids rapid
  on/off cycles that wear the compressor. While held on near the target, the
  adaptive boost is already near zero, so the room does not overshoot much. An
  open window or a global Off still stop the split immediately. Re-evaluation
  happens on sensor/helper changes, so the actual stop occurs at the first update
  after the minimum run time has elapsed.

### Bedroom recipe (night setpoint)

To get "eco during the day, a dedicated night temperature in the evening/night"
in a bedroom (e.g. 21 °C in summer, 17 °C in winter at night):

1. Create the optional `input_number.climate_night_thermostat` helper and assign
   it as the **Night Setpoint Helper** in the HVAC Season Manager (heat night 17,
   cool night 21 by default).
2. In the bedroom thermostat instance, set:
   - **Night Schedule** = your bedtime schedule (e.g. `schedule.period_active_bedtime`).
   - **Night Setpoint Helper** = `input_number.climate_night_thermostat`.
   - **Comfort Schedules** = the same bedtime schedule (so the daytime base is
     eco; the night override replaces it during bedtime anyway).

Result: during the day the bedroom follows eco; during the bedtime schedule it
targets the seasonal night value. Living areas leave the night fields empty and
keep their comfort/eco behavior.

## Example: a 5-split house

One Season Manager plus five thermostat automations, all sharing
`input_select.climate_hvac_active` and the two setpoint helpers:

| Room | Split (climate) | Room sensor | Windows |
| --- | --- | --- | --- |
| Living room | `climate.split_atlantic_sal_thermostat` | living-room sensor | door/window contacts |
| Landing | `climate.split_atlantic_pal_thermostat` | landing sensor | — |
| Office | `climate.split_atlantic_bur_thermostat` | office sensor | — |
| Bedroom 1 | `climate.split_atlantic_ch1_thermostat` | bedroom 1 sensor | — |
| Bedroom 2 | `climate.split_atlantic_ch2_thermostat` | bedroom 2 sensor | — |

## Troubleshooting

- **A split stays in the wrong mode**: check that every thermostat uses the exact
  same *Resolved Mode Helper* and that the Season Manager is enabled.
- **Modes flap in auto**: widen the gap between *Auto Heat Below* and *Auto Cool
  Above*.
- **My comfort/eco values reset on their own**: that is the seasonal reset on a
  heat ↔ cool transition. Disable *Apply Seasonal Defaults* to keep manual values.
- **A split never turns on**: it may be idling because the target is reached or
  the outdoor threshold blocks it; verify the room sensor and thresholds.
- **Nothing happens at all**: make sure `input_select.climate_season_mode` is not
  `off` and that the resolved helper has the expected options.

## Migrating from a heating-only blueprint

This pair replaces a heating-only multi-feature blueprint while keeping the same
comfort/eco helpers, per-room sensors, schedules, presence, window-off and frost
protection. TRV-specific features (valve calibration, calibration delta/timeout)
are intentionally omitted because splits manage their own regulation.
