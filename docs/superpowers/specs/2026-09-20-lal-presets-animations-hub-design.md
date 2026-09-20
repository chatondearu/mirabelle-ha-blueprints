# Design: LAL profile presets, animations, and lighting hub

**Date:** 2026-09-20  
**Status:** Implemented and deployed on HA  
**Scope:** Living Area Adaptive Lighting (presets + animations first), then hub blueprint  
**Depends on:** 1.3.0 morning/evening/privacy (`2026-09-20-living-area-lighting-profiles-design.md`)  
**Tests:** Deferred to a later pass (explicit)

## Goals

1. **Profile presets** (UI-editable HA package helpers): selectable packs of morning/day/evening/night profile values only (not schedule/privacy). Examples: blue starlight night, ember red night, soft day.
2. **Pluggable animations**: `animation_type` attachable to any profile; ship `none` + `leaf_cloud` (micro brightness sway). Default attach `leaf_cloud` to night on the starlight preset.
3. **Lighting hub** (after presets): central automation publishes global profile mode; per-room LAL can follow or stay autonomous.

## Non-goals (this phase)

- Behavior pytest suite for LAL (scheduled for later).
- Presets that include schedule/lux/privacy.
- Hub controlling lights directly.

## Phase 1 — Presets + animations

### Package

Companion script writes `/config/packages/cda_lal_profile_presets.yaml` with presets:

| Id | Intent |
|----|--------|
| `starlight_blue` | Current night blue look; anim `leaf_cloud` on night |
| `ember_red` | Red/amber night hue; anim `none` by default |
| `soft_day` | Softer day/morning/evening brightness/kelvin |

Per-preset helpers (prefix `lal_preset_<id>_`):

- Night: hue, sat, bri color/white, ramp fields as needed
- Morning/day/evening: kelvin min/max, brightness min/max
- `input_select` animation type: `none` | `leaf_cloud` (+ future types)
- Anim params: amplitude %, period seconds, optional profile mask (default night-only for leaf_cloud)

### LAL automation input

- **Profile preset**: `local` | `starlight_blue` | `ember_red` | `soft_day`
- `local` = use blueprint inputs (backward compatible)
- Non-local = read helper values for profile fields; schedule/privacy/occupancy stay local

### Animation engine

```text
base profile output → per-lamp animation modifier → light.turn_on
```

| Field | Role |
|-------|------|
| `animation_type` | `none` \| `leaf_cloud` \| … |
| `animation_amplitude_pct` | Max ± brightness delta |
| `animation_period_seconds` | Slow period |
| `animation_profiles` | Which active profiles run anim (default: `night` for leaf_cloud) |

**leaf_cloud:** stable per-`entity_id` phase + slow multi-sine brightness offset; desynced lamps; longer light transition; disabled on hold/override/off/empty zone.

Tighten `time_pattern` when anim active if needed (e.g. every 1–2 min already ok with /5 + longer transition).

## Phase 2 — Hub

New blueprint `[CDA] 🛋️ Living Area Lighting Hub`:

- Computes global `morning|day|evening|night` with same trigger/delay model as LAL schedule
- Writes `input_select.cda_lal_global_profile`
- Optional shared home presence helper
- Does **not** call `light.*`

LAL gains **Follow global profile** (`off` default): when `on` and room mode is `auto`, `active_profile` comes from hub select; presets/anim/lux/covers/occupancy remain per room.

## Migration

- Default preset `local` → no change for existing instances
- Run companion once to create preset package
- Hub optional; rooms keep autonomous schedule until Follow is enabled

## Implementation order

1. Preset package + companion script + LAL preset select + value resolution  
2. Animation engine (`none`, `leaf_cloud`)  
3. Hub blueprint + Follow input  
4. Docs (English)  
5. Deploy to HA instances  
6. **Later:** targeted pytest for profiles/privacy/anim  

## Out of scope until later

- More animation types (`breathe`, `twinkle`) beyond stub extensibility  
- Unlimited user-defined preset slots in UI (start with 3 fixed ids; document how to clone helpers)  
