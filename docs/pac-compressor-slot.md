# PAC Compressor Slot

Queued grant script for indoor reversible splits that share **one outdoor heat
pump (PAC)**. It is the only climate writer for starts when each Reversible Split
Thermostat points at the same script instance, so a return-home cannot start four
indoor units in the same minute.

## Why this exists

Per-split `min_run_time` and cut hysteresis cannot stop several rooms starting
together. Season Manager only writes the resolved heat/cool/off helper; it never
starts indoor units. A post-hoc automation that `turn_off`s extras fights
bang-bang (`mode: restart`) and would start them again.

This script is `mode: queued`: overlapping calls cannot all see concurrent=0.

## Prerequisites

- Home Assistant **2025.5.3** or later.
- Indoor `climate` entities on the same outdoor PAC.
- The shared helper below.

## Required helper

Create **once** per outdoor unit (Settings → Devices & Services → Helpers), or
paste into a package file and restart.

| Helper | Type | Purpose |
| --- | --- | --- |
| `input_datetime.climate_pac_last_change` | Date and time | Stamped on every granted start or stop. Required for the cap, start stagger, and global interval. |

```yaml
# Example package: config/packages/cda_pac_compressor_helpers.yaml
input_datetime:
  climate_pac_last_change:
    name: PAC Last Compressor Change
    has_date: true
    has_time: true
    icon: mdi:heat-pump
```

Do not invent per-room helper forests. Occupancy uses existing room
occupancy/activity sensors plus one optional `input_boolean` on each thermostat
instance (see [Reversible Split Thermostat](reversible-split-thermostat.md)).

If the last-change helper is left empty on the script, compressor rules are
skipped and every request is granted.

## Installation

Import the blueprint:

- [[CDA] 🧊 PAC Compressor Slot](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscripts%2Fpac-compressor-slot.yaml)

Then create **one script** from the blueprint per outdoor PAC. Point every
Reversible Split Thermostat on that PAC at this script.

## Parameters

| Parameter | Default | Description |
| --- | --- | --- |
| Indoor splits on this PAC | — | All `climate` entities that share the compressor, including every split that will call this script. |
| Last compressor change | — | Shared `input_datetime`. Empty = skip compressor rules. |
| Max concurrent indoor units | 2 | Splits currently in `heat` or `cool`. Units already running keep their slot; new starts are denied at the cap. |
| Start stagger | 45 s | Minimum seconds between granted starts (0–90). |
| Global change interval | 30 s | Minimum seconds between any granted start or stop. |

### Call fields (from the thermostat)

| Field | Description |
| --- | --- |
| `climate_id` | Indoor unit requesting the grant. |
| `request` | `start` (mode + temperature) or `stop`. |
| `hvac_mode` / `temperature` | Used on start. |
| `frost` | When true, start is granted even if the cap is full. |

## Behaviour

- **Cap:** a new start is denied when `max_concurrent` indoor units are already
  in `heat` or `cool`. Occupied rooms wait for a free slot on the next
  thermostat run; they are not started by turning extras off. Occupancy-off rooms
  must not hold slots (the thermostat idles them off without requesting a slot).
- **Stagger:** a granted start waits until `start_stagger_seconds` have elapsed
  since the last granted change.
- **Interval:** start and stop both wait on `global_change_interval`, except when
  the thermostat bypasses this script (open window or global season `off`).
- **Frost:** may start even at cap (safety).
- **FIFO:** `mode: queued` runs requests in order.

## GO live (not this product PR)

Ship the blueprint only. **Do not** re-enable live thermostat automations from
this change, and **do not** run `update-automations` until an explicit human
**GO live**. Importing this script and wiring helpers on a live Home Assistant
instance is a later step.

## Troubleshooting

- **Every room still starts at once:** the last-change helper is empty, or
  thermostats still have an empty Compressor Slot Script input.
- **A room never starts:** the PAC is at cap (units already running keep their
  slot). Check occupancy-off rooms are actually off so they release slots.
- **Stops feel delayed:** target-reached idle goes through the global interval.
  Window-open and season `off` skip it.
