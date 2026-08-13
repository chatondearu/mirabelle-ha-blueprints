# Design: Garden irrigation orchestrator + zones

**Date:** 2026-08-13  
**Status:** Implemented  
**Scope:** New blueprints under `blueprints/automations/`, English docs under `docs/`  
**Hardware context:** Sonoff SWV-ZFE (Hydro ONE) on ZHA with Flow quirk — see `docs/sonoff-swv-zfe-zha.md`

## Problem

Garden watering needs a reusable Home Assistant model that:

- Supports **as many valves as needed** (one valve = one zone, fixed type).
- Distinguishes **aerial misting** (plant refresh) from **soil watering** (root hydration, typically evening).
- Centralizes schedule, weather/pause guards, and run mode in one place, while keeping per-valve execution isolated (important for sleepy Zigbee end devices).

## Goals

- One **orchestrator** automation that decides *when* and *which* zones to run.
- One **zone** automation instance per Sonoff valve that executes a single irrigation cycle.
- Stop condition: **target volume OR max duration** (whichever comes first).
- Multi-slot schedules for aerial and soil, editable via **helpers** (no blueprint republish for day-to-day tweaks).
- Aerial also triggers on **outdoor temperature ≥ threshold**, with cooldown.
- Skip / pause: **rain** (recent or forecast) + **manual pause** helper.
- Global run mode: **sequential** or **parallel** (configurable).
- Zigbee-aware open/close with retries, fail-safe awareness, and force-off watchdog.

## Non-goals (v1)

- Soil moisture sensors / adaptive volume from humidity.
- Full Lovelace dashboard pack (may follow later).
- Multi-day weather intelligence beyond a simple rain binary / lookback.
- Sharing one physical valve across both aerial and soil types.
- Native device timer programming as the primary control path (HA remains source of truth; device On-time only as safety floor).

## Approaches considered

| Approach | Pros | Cons |
| -------- | ---- | ---- |
| 1. Single monolithic blueprint | One import | Does not scale; hard to test; poor UX for N valves |
| **2. Orchestrator + per-zone blueprints** | Scales; matches HVAC Season Manager pattern; Zigbee isolation | More initial helper wiring |
| 3. Scripts + helpers only | Flexible locally | Not reusable as `[CDA]` blueprints |

**Chosen:** Approach 2.

## Architecture

```text
Orchestrator (1×)
  triggers: schedule slots | aerial heat threshold
  guards: master enable, pause, rain lookback
  run mode: sequential | parallel
  queue: FIFO; heat aerial can jump ahead when heat_aerial_priority=true
  emits: event garden_irrigation.run_zone { zone_id, reason }

Zone automation (N×, one per valve)
  listens: garden_irrigation.run_zone (filter zone_id)
  cycle: raise device on-time → turn_on + retry → wait volume|timeout → turn_off + retry
  notifies on hard failure; does not block other zones forever
```

**Contract:** orchestrator decides; zone executes. Zones never talk to each other.

**Zone discovery:** the orchestrator does not auto-discover zones. It takes two explicit lists of `zone_id` values (aerial / soil). Each listed id must match a configured zone automation. Adding a valve = create helpers + zone automation + append its `zone_id` to the right list.

### Blueprints

| Blueprint | Domain | Role |
| --------- | ------ | ---- |
| `[CDA] 🌿 Garden Irrigation Orchestrator` | automation | Schedules, guards, queue, emit run events |
| `[CDA] 💧 Garden Zone Irrigation` | automation | One Sonoff valve cycle (volume + max duration) |

Filenames (kebab-case): `garden-irrigation-orchestrator.yaml`, `garden-zone-irrigation.yaml`.

### Event bus

- Event type: `garden_irrigation.run_zone`
- Payload:
  - `zone_id` (string, stable id configured on the zone blueprint)
  - `reason`: `schedule_aerial` | `schedule_soil` | `heat_aerial` | `manual`

Manual dashboard buttons can fire the same event for a single zone.

## Helpers and inputs

### Global (orchestrator-facing)

| Helper / entity | Purpose |
| --------------- | ------- |
| `input_boolean` master enable | No new cycles when off |
| `input_boolean` pause | Manual hold (holidays / maintenance) |
| `input_select` run mode | `sequential` / `parallel` |
| Slot list aerial | Multi time-of-day slots (helper; concrete shape chosen in implementation plan) |
| Slot list soil | Same for soil |
| Aerial `zone_id` list | Explicit ids to run on aerial schedule / heat |
| Soil `zone_id` list | Explicit ids to run on soil schedule |
| `input_number` aerial temp threshold (°C) | Heat refresh trigger |
| Outdoor temperature sensor | Compared to threshold |
| Rain binary / sensor + lookback hours | Skip when recent/forecast rain |
| `input_number` heat aerial cooldown (minutes) | Prevent heat-trigger spam |
| `input_boolean` heat aerial priority | Default `true` — heat jobs ahead of FIFO soil/schedule when sequential |

### Per zone (zone blueprint inputs)

| Input | Purpose |
| ----- | ------- |
| `zone_id` | Must match event payload |
| `irrigation_type` | `aerial` \| `soil` |
| `valve_switch` | Sonoff On/Off entity |
| `volume_sensor` | Optional session/realtime volume; if absent or unavailable, zone runs **duration-only** (max duration) |
| `target_volume_helper` | `input_number` litres (ignored when no usable volume sensor) |
| `max_duration_helper` | `input_number` minutes (hard cap; always enforced) |
| `zone_enabled_helper` | Local enable |
| Optional notify target | Failure alerts |

Day-to-day values (litres, minutes, times, °C) live in helpers; blueprints only wire entities and logic.

## Behaviour flows

### Soil (root watering)

1. Soil schedule slot fires.
2. Guards: master on, not paused, rain clear.
3. Collect enabled zones with `irrigation_type=soil`.
4. Enqueue or start according to run mode.
5. Each zone: open → stop on volume **or** max duration → close.

### Aerial (refresh)

Triggers (either path, same guards + aerial zones only):

- Schedule slot(s), and/or
- Outdoor temperature ≥ threshold **and** cooldown elapsed.

Default sequential priority: heat-triggered aerial jobs may preempt the FIFO queue when `heat_aerial_priority` is true.

### Pause / master off while running

- Default: **force close** active valves when pause or master turns off mid-cycle (blueprint boolean, default on).

## Safety and Zigbee reliability

Aligned with SWV-ZFE constraints (battery end device, ~10 min default fail-safe):

1. Before a long run, ensure device **On time / fail-safe** ≥ configured max duration (document in zone docs; optional service/number set if exposed by quirk).
2. `turn_on` with retries (e.g. up to 3 attempts over ~2–3 minutes) until state is `on` or fail.
3. Wait until volume target reached **or** max duration elapsed.
4. `turn_off` with the same retry pattern.
5. Watchdog: if switch stays `on` longer than max duration + margin → force off + notify.
6. Zone automation `mode: single` to prevent overlapping cycles on the same valve.
7. On hard failure: notify; mark that zone failed for this run; continue queue for other zones.

## Testing expectations

- Blueprint structural validation (`validate_blueprints.py` / `pnpm run test:ha`).
- Smoke: orchestrator with mocked events; zone cycle with simulated switch + volume sensor (where HA test harness allows).
- Docs: installation, helper setup, Sonoff quirk prerequisite, troubleshooting (timeouts, fail-safe, rain skip).

## Documentation deliverables

- `docs/garden-irrigation.md` — user-facing English guide (orchestrator + zone, parameters, examples, troubleshooting).
- README import links when blueprints ship.
- Cross-link `docs/sonoff-swv-zfe-zha.md` for valve setup.

## Open decisions (resolved in this design)

| Topic | Decision |
| ----- | -------- |
| Topology | One valve = one zone + fixed type |
| Stop rule | Volume target + max duration (first wins) |
| Skip | Rain + manual pause (no soil sensors in v1) |
| Concurrency | Configurable sequential / parallel |
| Schedules | Multi-slot + helpers; aerial also on heat threshold |
| Architecture | Orchestrator + zone blueprints + `garden_irrigation.run_zone` event |

## Implementation note

Exact helper shape for multi-slot times (CSV `input_text` vs repeated `input_datetime`) is left to the implementation plan; behaviour must support multiple daily slots per type without republishing the blueprint.
