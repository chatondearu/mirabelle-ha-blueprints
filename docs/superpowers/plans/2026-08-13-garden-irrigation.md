# Garden Irrigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) or superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `[CDA] 🌿 Garden Irrigation Orchestrator` and `[CDA] 💧 Garden Zone Irrigation` blueprints per `docs/superpowers/specs/2026-08-13-garden-irrigation-design.md`.

**Architecture:** Orchestrator decides (schedules, heat threshold, rain/pause, sequential/parallel) and emits `garden_irrigation.run_zone`. Each zone automation runs one Sonoff valve cycle (volume delta or max duration), emits `garden_irrigation.zone_done`, retries Zigbee on/off, force-closes on pause.

**Tech Stack:** Home Assistant automation blueprints (YAML), pytest HA harness, yamllint / `validate_blueprints.py`.

## Global Constraints

- Home Assistant **2025.5.3** or later (`blueprint.homeassistant.min_version`).
- Blueprint names start with **`[CDA]`**; filenames kebab-case.
- All user-facing docs / descriptions in **English**.
- Conventional Commits with scope (e.g. `feat(blueprints): ...`).
- Do not commit secrets; do not push unless the user asks.
- Prefer `nix develop -c …` for test commands.

## File map

| File | Role |
| ---- | ---- |
| `blueprints/automations/garden-zone-irrigation.yaml` | Per-valve cycle executor |
| `blueprints/automations/garden-irrigation-orchestrator.yaml` | Scheduler / guards / queue |
| `docs/garden-irrigation.md` | User guide (EN) |
| `docs/superpowers/specs/2026-08-13-garden-irrigation-design.md` | Mark approved/implemented |
| `scripts/validate_blueprints.py` | Add both paths to `EXPECTED_BLUEPRINTS` |
| `tests/fixtures/blueprint_inputs.py` | Smoke inputs |
| `README.md` | Import links |
| `docs/superpowers/plans/2026-08-13-garden-irrigation.md` | This plan |

### Event contracts

**`garden_irrigation.run_zone`**
- `zone_id`: string
- `reason`: `schedule_aerial` \| `schedule_soil` \| `heat_aerial` \| `manual`

**`garden_irrigation.zone_done`**
- `zone_id`: string
- `status`: `ok` \| `timeout` \| `failed_open` \| `failed_close` \| `aborted`

---

### Task 1: Zone irrigation blueprint + smoke inputs

**Files:**
- Create: `blueprints/automations/garden-zone-irrigation.yaml`
- Modify: `scripts/validate_blueprints.py` (add path)
- Modify: `tests/fixtures/blueprint_inputs.py`

**Interfaces:**
- Consumes: `garden_irrigation.run_zone` (filter by `zone_id`)
- Produces: `garden_irrigation.zone_done`; valve on/off with retries

- [x] **Step 1: Implement zone blueprint**
- [x] **Step 2: Register validation + smoke inputs**
- [x] **Step 3: Run validation / smoke**
- [x] **Step 4: Commit** (deferred — user must request)

---

### Task 2: Orchestrator blueprint

**Files:**
- Create: `blueprints/automations/garden-irrigation-orchestrator.yaml`
- Modify: `scripts/validate_blueprints.py`, `tests/fixtures/blueprint_inputs.py`

**Interfaces:**
- Consumes: schedule `input_datetime` lists, outdoor temp, rain, pause/master, run mode, zone id CSV lists
- Produces: `garden_irrigation.run_zone`; waits on `garden_irrigation.zone_done` when sequential

- [x] **Step 1: Implement orchestrator**
- [x] **Step 2: Smoke inputs + validate** (heavy smoke — time listeners)
- [x] **Step 3: Run tests**

---

### Task 3: Docs + README + spec status

- [x] **Step 1: Write user docs**
- [x] **Step 2: README links**
- [x] **Step 3: Mark spec implemented**

---

## Spec coverage checklist

| Spec item | Task |
| --------- | ---- |
| Zone blueprint volume+max duration | 1 |
| Orchestrator schedules multi-slot | 2 (input_datetime multiple) |
| Heat aerial + cooldown | 2 |
| Rain + pause | 2 (+ zone force close in 1) |
| Sequential / parallel | 2 |
| Explicit zone_id lists | 2 |
| Zigbee retries / on-time / done event | 1 |
| Docs + README | 3 |
| Duration-only if no volume sensor | 1 |
