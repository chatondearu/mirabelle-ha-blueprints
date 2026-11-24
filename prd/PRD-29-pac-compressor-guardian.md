# PRD-29 — PAC compressor-guardian

- **Status**: approved
- **GitHub**: [#29](https://github.com/chatondearu/mirabelle-ha-blueprints/issues/29)
- **Date**: 2026-11-24
- **Tags**: #product #hvac

## Problem

Five indoor Atlantic/Fujitsu splits share **one outdoor PAC**. Each
`[CDA] 🌡️ Reversible Split Thermostat` bang-bang instance decides heat/cool on
its own. Per-split `min_run_time` (live instances all **0**) and cut hysteresis
cannot stop several rooms starting together.

On 2026-11-23 19:56Z, return-home started **four** indoor units in `heat` within
45 s (five at 20:45Z). Whole-home load rose ~0.35→5 kW, then collapsed while HA
kept commanding `heat`. Season Manager only prevents heat+cool at once; it does
not cap concurrent compressor load. Occupancy sensors exist in HA but are not
wired; presence is whole-house (`person.romain`).

## Goals

- [ ] Cap how many indoor units may be in `heat` or `cool` at once on one PAC
      (default 2, blueprint input).
- [ ] Stagger compressor starts (30–90 s, input) so return-home cannot slam four
      units in the same minute.
- [ ] Enforce a **global** minimum interval between compressor state changes
      (start **and** stop), not only per-split min run.
- [ ] Optional per-room occupancy/activity gate so empty rooms stay **off**
      (not eco setpoint; frost excepted), togglable via helper/input.
- [ ] Raise Reversible Split Thermostat **defaults** for `min_run_time` and
      `cut_hysteresis` (cheap, same PR). No new boost math.
- [ ] Ship a product PR only. Live HA import / `update-automations` / re-enable
      of the five thermostat automations is a later human **GO live**.

## Non-goals

- Re-enabling the five live thermostat automations from this work.
- CH2/Palier shared room temperature sensor (keep as-is).
- Season Manager rewrite or heat↔cool policy changes.
- New per-split adaptive-boost / approach-delta formulas.
- Dedicated PAC power clamp or outdoor compressor entity.
- Non-HVAC automations; a full HVAC audit (later issue at most).
- Foam/board bootstrap (open PR #28).

## Users & scenarios

| Persona | Scenario |
| ------- | -------- |
| Household | Return-home on a cold evening: several occupied rooms need heat; at most `max_concurrent` indoor units start, staggered. |
| Household | Empty rooms (Palier/CH2 daytime) stay **off** when the occupancy gate is on (frost excepted). |
| Occupant | Open window or global season `off` still stops a split immediately (existing exception). |
| Occupant | Frost protection may still heat a room even if the cap is full. |
| Maintainer | Merge the product PR; do **not** deploy to live HA until an explicit GO live. |

## Requirements

### Functional

- [ ] **R1 Concurrent cap.** Any indoor split in `heat` or `cool` counts as one
      compressor slot. Default cap **2**, numeric input. Units already running
      keep their slot; new starts wait.
- [ ] **R2 Start stagger.** A new start is delayed until
      `start_stagger_seconds` (default in 30–90, e.g. 45) have elapsed since the
      last granted start on that PAC.
- [ ] **R3 Global change interval.** A shared last-change timestamp (helper)
      gates **on and off** transitions. Window-open and global `off` still stop
      immediately (same as today’s min-run exception).
- [ ] **R4 Occupancy gate (optional).** If a per-room occupancy/activity entity
      is set and the gate helper/input is on, an unoccupied room **idles the
      split (off)** and does not request a slot. Do not only switch to the eco
      setpoint: eco below room temperature would still start heat. Frost still
      applies. Occupied rooms still obey R1–R3.
- [ ] **R5 No fight.** A post-hoc automation that `turn_off`s extras **after**
      thermostats start them is not acceptable: bang-bang `mode: restart` would
      start them again. The grant must sit on the start path (serialized).
- [ ] **R6 Defaults.** Raise Reversible Split Thermostat defaults:
      `min_run_time` **0 → 600** s, `cut_hysteresis` **0.3 → 0.5** °C. Do not
      change boost / approach-delta defaults.
- [ ] **R7 Publish.** English docs and, if a new blueprint/script is added,
      README import URL. Tests: yamllint, `validate_blueprints.py`, pytest.

### Non-functional

- [ ] Home Assistant **2025.5.3+**; `[CDA]` name prefix; kebab-case filenames.
- [ ] Smallest design that satisfies R5: one queued script (or equivalent
      serialized grant) + thermostat hook. Do **not** fold this into Season
      Manager (it does not command indoor units).
- [ ] No secrets, instance URLs, or live tokens in YAML/docs.
- [ ] Implementation PR must not run `pnpm run update-automations` or write
      live helpers.

## Related project memory

- Foam ADRs: **none in this worktree.** Open PR #28 is foam/board scaffold only;
  this issue must not bootstrap `foam/` or touch that PR.
- Existing pair: `[CDA] 🔁 HVAC Season Manager` (one instance, resolved mode)
  + `[CDA] 🌡️ Reversible Split Thermostat` (one instance per split). Documented
  in `docs/reversible-split-thermostat.md`.
- Evidence: 2026-11-24 compressor-stress diagnosis (live HA read-only).

## Open questions

1. Confirm one outdoor compressor (nameplate). HA has no outdoor PAC entity;
   this PRD **assumes yes** from topology (one brand family + Season Manager).
2. Frost vs cap: **recommended** — frost may start even at cap (safety).
   Implementer follows that unless a later comment says otherwise.
3. Occupancy timeout vs raw motion: use the occupancy entity already in HA
   (Hue/Frient occupancy, not a new Bayesian). No extra hold-time math unless
   the entity is instantaneous-only and tests fail the empty-room scenario.

## Success metrics

- A pytest case with four rooms requesting `heat` at once grants at most
  `max_concurrent` starts, with stagger ≥ the configured delay.
- Live GO-live (out of this issue) no longer reproduces a 4-way start within
  45 s after return-home, without re-enabling thermostats in the product PR.

## Implementation pointer

`plans/PLAN-29-pac-compressor-guardian.md`
