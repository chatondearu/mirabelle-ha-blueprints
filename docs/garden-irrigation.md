# Garden Irrigation (Orchestrator + Zones)

## Description

Two paired blueprints manage garden watering with Sonoff (or any) valves:

| Blueprint | Role |
| --------- | ---- |
| **[CDA] 🌿 Garden Irrigation Orchestrator** | Schedules, heat trigger, rain/pause guards, sequential or parallel dispatch |
| **[CDA] 💧 Garden Zone Irrigation** | One automation per valve: open → volume or max duration → close |

Events:

- `garden_irrigation.run_zone` — `{ zone_id, reason }`
- `garden_irrigation.zone_done` — `{ zone_id, status }`
- `garden_irrigation.request` — manual run (`type`: `aerial` \| `soil`, optional `zone_id`)

## Prerequisites

- Home Assistant **2025.5.3** or later
- One On/Off switch per valve (Sonoff SWV-ZFE on ZHA: see [sonoff-swv-zfe-zha.md](sonoff-swv-zfe-zha.md))
- Optional volume sensor (litres) for volume-based stop
- Helpers listed below

## Installation

1. Import both blueprints (README quick links or GitHub URLs).
2. Create helpers (Settings → Devices & services → Helpers).
3. Create one **Zone** automation per valve.
4. Create one **Orchestrator** automation and list every `zone_id`.

## Helpers (suggested)

### Global

| Helper | Domain | Notes |
| ------ | ------ | ----- |
| Garden irrigation enabled | `input_boolean` | Master on/off |
| Garden irrigation pause | `input_boolean` | Holidays / maintenance |
| Garden run mode | `input_select` | Options: `sequential`, `parallel` |
| Aerial temp threshold | `input_number` | °C for heat refresh |
| Heat cooldown | `input_number` | Minutes between heat runs |
| Last heat run | `input_datetime` | Date **and** time |
| Aerial slot(s) | `input_datetime` | Time only, one helper per slot |
| Soil slot(s) | `input_datetime` | Time only |

### Per zone

| Helper | Domain | Notes |
| ------ | ------ | ----- |
| Zone enabled | `input_boolean` | Local enable |
| Target volume | `input_number` | Litres (delta from cycle start) |
| Max duration | `input_number` | Minutes hard cap |

## Configuration

### Zone blueprint

| Parameter | Description |
| --------- | ----------- |
| Zone ID | Stable id (e.g. `soil_hedge`, `aerial_potager`) |
| Irrigation type | `aerial` or `soil` (documentation / future use) |
| Valve switch | Sonoff On/Off |
| Volume sensor | Optional; if empty → duration-only |
| Target / max duration helpers | Stop: volume delta **or** max minutes |
| Device irrigation duration | Optional Sonoff **Irrigation duration** number (minutes); raised to max+1 before open |
| Retries / delay | Zigbee open-close reliability |
| Pause / master helpers | Same entities as orchestrator for force-close |

### Orchestrator blueprint

| Parameter | Description |
| --------- | ----------- |
| Master / pause | Global guards |
| Rain sensor + lookback | Skip while wet; after off, skip for lookback hours (0 = wet only) |
| Run mode helper | `sequential` waits for `zone_done`; `parallel` fires all |
| Aerial / soil zone ID lists | Comma-separated ids |
| Schedule helpers | `input_datetime` time triggers |
| Outdoor temp + threshold + cooldown + last heat | Heat-triggered aerial |

## Usage examples

**Evening soil watering:** soil `input_datetime` at `21:00`, zone ids `soil_a,soil_b`, run mode `sequential`.

**Hot-day misting:** aerial threshold `32`, cooldown `90`, outdoor temperature sensor; optional extra slots at `07:00` and `14:00`.

**Manual single zone:**

```yaml
event: garden_irrigation.request
event_data:
  type: soil
  zone_id: soil_hedge
```

## Troubleshooting

| Symptom | Check |
| ------- | ----- |
| Valve never opens | Wake Sonoff (button), Zigbee router, retries; see quirk doc |
| Closes at ~10 min | Raise device On-time / fail-safe above max duration |
| No schedule fire | Use **time** helpers (`input_datetime` time-only) wired in orchestrator |
| Heat never fires | Threshold, cooldown, `last_heat` datetime, outdoor sensor |
| Skipped after restart | Set rain lookback to `0` if rain sensor `last_changed` resets |
| Sequential stuck | Zone must emit `zone_done`; check zone_id spelling |

## Related

- [Sonoff SWV-ZFE on ZHA](sonoff-swv-zfe-zha.md) — quirk, entities, fail-safe and connectivity notes

## Security

- No secrets in blueprint YAML
- Notify service is optional; leave empty if unused

## Changelog

- **1.0.0** — Initial orchestrator + zone blueprints
