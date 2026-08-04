# Sync Zigbee Split Occupied Setpoints

Utility script for **Atlantic / Fujitsu `Adapter Zigbee FUJITSU`** splits managed by **ZHA**.

## Why this exists

ZHA exposes a normal `climate` entity, but the split also stores **internal Zigbee setpoints**:

| Zigbee attribute | HA climate attribute | Meaning |
| --- | --- | --- |
| `occupied_cooling_setpoint` (id 17) | `occupied_cooling_setpoint` | Device cooling target while “occupied” |
| `occupied_heating_setpoint` (id 18) | `occupied_heating_setpoint` | Device heating target while “occupied” |

These values are **mandatory on the device**. They **cannot be deleted**, only overwritten.

When they drift from Home Assistant — for example after changing the temperature with the **IR remote** — the split may keep using the old internal value (e.g. 23 °C) even though your CDA thermostat automation sends 24.8 °C.

This script **resets** them by writing the comfort or eco helper to:

1. **both** Zigbee occupied attributes 17 and 18 (so a leftover heating value
   such as 20 °C cannot overwrite cooling ~30 s later)
2. the HA `climate.set_temperature` service

## Installation

Import the blueprint:

- [[CDA] 🔄 Sync Zigbee Split Occupied Setpoints](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fsync-zigbee-split-setpoints.yaml)

Then create **one script** from the blueprint.

## Parameters

| Parameter | Description |
| --- | --- |
| Split climate entities | One or more `climate.*` splits to resync |
| Resolved HVAC mode helper | Same `input_select` as the Season Manager output (`off / heat / cool`) |
| Comfort / Eco setpoint helper | Shared `input_number` helpers |
| Use eco setpoint | Off = write comfort; On = write eco |
| Thermostat automations (optional) | Trigger CDA split automations first (schedules, boost, etc.) |
| Delay after automation trigger | Wait before the Zigbee write (default 2 s) |

## Example instance (Mirabelle)

| Blueprint input | Value |
| --- | --- |
| Split climate entities | All five `climate.split_atlantic_*_thermostat` |
| Resolved HVAC mode helper | `input_select.climate_hvac_active` |
| Comfort / Eco helpers | `input_number.climate_comfort_thermostat` / `input_number.climate_eco_thermostat` |
| Use eco setpoint | Off (or On outside comfort schedule) |
| Thermostat automations | The five `[CDA] 🌡️ Reversible Split Thermostat` automations |

Add the script to the UI (button, dashboard, voice assistant) and run it whenever a split ignores automation after remote use.

## What this script does **not** do

- It does **not** remove `occupied_*` attributes (impossible on Zigbee thermostats).
- It does **not** replace the split thermostat automations for day-to-day control
  (those now sync occupied setpoints automatically when **Sync Zigbee Occupied
  Setpoints** is enabled in the thermostat blueprint).
- It does **not** write `unoccupied_*` setpoints (not reported by the Atlantic adapter here).

For a permanent fix, re-import and update your split thermostat automations from
the latest blueprint. Keep this script as a manual recovery tool after remote use
or when migrating several splits at once.

## Troubleshooting

- **Service fails / device asleep:** wake the split (remote or HA command), then rerun the script.
- **Attribute write succeeds but value reverts to ~20 °C:** the device is re-reporting
  a stale `occupied_heating_setpoint`. Re-run this script (it now writes cooling and
  heating together) and re-import the thermostat blueprint.
- **Non-ZHA splits:** this script only works for devices with a `zha` device identifier.

Verify after running:

```yaml
# Developer tools → Template
{{ state_attr('climate.split_atlantic_bur_thermostat', 'occupied_cooling_setpoint') | int / 100 }}
{{ state_attr('climate.split_atlantic_bur_thermostat', 'temperature') }}
```

Both should match your comfort/eco helper (in the active HVAC mode).
