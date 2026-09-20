# Living Area Lighting Profiles Implementation Plan

> **For agentic workers:** Implement task-by-task. Steps use checkbox syntax.

**Goal:** Add morning/evening profiles, cover-open privacy (block/cap), and event+delay triggers to `living-area-adaptive-lighting`, fixing the post-sunset 100% day brightness spike.

**Architecture:** Single blueprint; template-computed `active_profile` with priority night > evening > morning > day; optional progressive transition unchanged when elevation band active.

**Tech Stack:** Home Assistant automation blueprints (YAML), companion script, pytest smoke, English docs.

## Global Constraints

- HA min_version 2025.5.3; blueprint name keeps `[CDA]` prefix; docs English; conventional commits with scope; no secrets in YAML.

## File map

| File | Responsibility |
|------|----------------|
| `blueprints/automations/living-area-adaptive-lighting.yaml` | Inputs, `active_profile`, privacy, morning/evening apply |
| `blueprints/scripts/create-living-area-lighting-helpers.yaml` | Mode options include morning/evening |
| `docs/living-area-adaptive-lighting.md` | User docs + changelog 1.3.0 |
| `docs/superpowers/specs/2026-09-20-living-area-lighting-profiles-design.md` | Design (done) |
| `tests/fixtures/blueprint_inputs.py` | Defaults for new required-ish inputs if smoke needs them |

---

### Task 1: Blueprint inputs + profile selection logic

- [ ] Add cover privacy inputs, morning/evening profile sections, schedule trigger/delay inputs
- [ ] Replace binary `is_night` consumer path with `active_profile`
- [ ] Wire evening/morning brightness+kelvin; fix day-gap 100% path
- [ ] Privacy block/cap in `need_artificial_light` / brightness clamp

### Task 2: Actions + helpers + docs + tests

- [ ] Action `choose` branches for morning/evening (and forced modes)
- [ ] Update companion helper options
- [ ] Update docs changelog 1.3.0
- [ ] Run `pnpm run test:ha` / smoke
