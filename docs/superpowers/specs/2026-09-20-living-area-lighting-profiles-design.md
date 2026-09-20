# Design: Living Area Adaptive Lighting — morning/evening profiles & cover privacy

**Date:** 2026-09-20  
**Status:** Implemented  
**Scope:** `blueprints/automations/living-area-adaptive-lighting.yaml`, companion helper script, `docs/living-area-adaptive-lighting.md`  
**Live evidence:** `automation.cda_lal_salon` — `night_start: 22:30:00`, `day_start: 06:00:00`, `progressive_transition: true`, `cover_shade_threshold: 75`

## Problem

1. **Privacy / open covers:** When outdoor light drops but covers are still mostly open, turning interior lights on makes curtains ineffective for privacy.
2. **100% brightness spike:** Between sunset (or end of progressive transition) and fixed `night_start` (22:30), `is_night` is false so the **day** profile runs. With closed covers + low lux, `day_brightness_pct` reaches ~100%. Night profile is intentionally reserved for a later “night simulation”, not sunset.
3. **Symmetric morning gap:** Fixed `day_start` (06:00) before/around sunrise can similarly force a harsh day profile; a dedicated morning profile is needed.
4. **Future (out of scope):** selectable shared presets from HA YAML / central hub.

## Goals (phases A then B)

- **A:** Dual lux sensitivity when covers are open (`block` or `cap`); add full **morning** and **evening** profiles (kelvin + brightness min/max); stop using day profile in the sunset→night and night-end→day gaps.
- **B:** Per-transition event source (`sunrise` / `sunset` / `sun_elevation` / `fixed_time`) + postpone/anticipate delay in minutes.
- Keep a **single** blueprint (approach 1); no orchestrator hub yet.

## Non-goals

- Shared preset YAML packs / selectable default profiles library.
- Central automation for sun/presence shared across rooms.
- Changing `presence_based_lighting` (simple on/off blueprint).

## Architecture

State machine in auto mode (one active profile):

```text
morning → day → evening → night → (morning)
```

| Profile | Role | Default trigger (B) |
|---------|------|---------------------|
| morning | Soft post-night / dawn | `day_start` fixed time or sunrise + delay; duration until day |
| day | Full daylight adaptive | Residual between morning end and evening start |
| evening | Dusk until night simulation | Sunset (or elevation / fixed time) + delay → until night start |
| night | Blue starlight + optional ramp | Existing `night_start` (fixed) + delay → until morning |

Manual `input_select` options: `auto | morning | day | evening | night | off`.

Priority when windows could overlap: **night > evening > morning > day**.

Progressive transition (elevation band) remains optional. When active and elevation is inside the band, it may still blend; once below the band and before night start, **evening** applies (not day) — this is the 100% fix for LAL Salon.

### Cover privacy (open covers)

When average cover **open** position ≥ `cover_open_privacy_threshold` (default 50%):

| Policy | Behavior |
|--------|----------|
| `block` | Do not turn lights on for lux-based need (night / forced modes still may) |
| `cap` | Allow lux-based lighting but clamp brightness to `open_covers_brightness_cap` |
| `off` | Legacy behavior (no privacy policy) |

Closed-cover shade threshold (`cover_shade_threshold`) unchanged.

Optional stricter lux thresholds when covers are open (`lux_dark_covers_open` / `lux_bright_covers_open`) — used mainly with `cap`.

### Profile parameters

Morning and evening each expose: kelvin min/max, brightness min/max (same shape as day). Defaults:

- Evening: warmer, lower max brightness (avoid 100% spike).
- Morning: softer than full day.

Day and night profiles keep current inputs.

### Event + delay (B)

For morning, evening, and night:

- `*_trigger`: `sunrise` | `sunset` | `sun_elevation` | `fixed_time`
- `*_delay_minutes`: integer (negative = anticipate)
- Supporting fields: fixed time, elevation threshold as needed
- Morning also has `morning_duration_minutes` (default end of morning window)

Computed each run via templates (same pattern as today’s `is_night`); existing occupancy/lux/cover/sun triggers remain; add time/sun triggers as needed so profile boundaries fire.

## Migration

- Existing inputs keep working; new inputs have safe defaults (`evening`/`morning` enabled).
- Companion script adds `morning` and `evening` to `input_select` options.
- Existing installs: re-run companion script or manually add options; document in troubleshooting.
- Version bump blueprint docs to **1.3.0**.

## Testing

- Smoke load blueprint with new inputs.
- Behavior notes (pytest/templates where feasible): evening after sunset before night_start does not use day max brightness path; open covers + block suppresses lux need; open covers + cap clamps brightness.

## Deferred

- Preset profile library (YAML packages / selectable defaults).
- Central lighting orchestrator sharing sun/presence/default profiles across instances.
