# PLAN-29 — PAC compressor-guardian

- **Status**: draft
- **PRD**: [[../prd/PRD-29-pac-compressor-guardian|PRD-29]]
- **GitHub**: [#29](https://github.com/chatondearu/mirabelle-ha-blueprints/issues/29)
- **Date**: 2026-11-24

## Summary

Serialize indoor split starts/stops on one outdoor PAC: concurrent cap (default
2), start stagger (30–90 s), global on/off interval, optional occupancy gate.
Raise thermostat `min_run_time` / `cut_hysteresis` defaults in the same PR.
Ship the product PR only — no live HA import, no re-enable of the five
thermostat automations.

## Constraints (from ADRs)

| ADR | Constraint |
| --- | ---------- |
| _(none — `foam/decisions/` is not in this worktree; PR #28 must not be used as a product ADR)_ | Follow repo `AGENTS.md`: `[CDA]` prefix, English docs, HA 2025.5.3+, conventional commits with scope. |

Do not violate accepted ADRs without superseding them.

## Scope

### In scope

- Queued grant (script blueprint) + Reversible Split Thermostat hook (R1–R5).
- Optional occupancy/activity input + helper so empty rooms idle off (R4).
- Default bump: `min_run_time` 600 s, `cut_hysteresis` 0.5 °C (R6).
- Docs + README import link if a new script/blueprint is published (R7).
- Pytest (+ yamllint, `validate_blueprints.py`).

### Out of scope

- Live HA: `update-automations`, helper changes, re-enable thermostats (**GO live** later).
- CH2/Palier shared temperature sensor (keep as-is).
- Season Manager behavior, boost/approach math, PAC clamp, non-HVAC, foam bootstrap.

## Technical approach

**Why not a third automation that turns extras off?** Thermostats use
`mode: restart` and will command `heat`/`cool` again on the next trigger.
**Why not Season Manager?** It only writes the resolved mode helper; it never
starts indoor units, so a hook there cannot serialize the 19:56Z race.

**Smallest that satisfies R5:**

1. **New script blueprint** `[CDA] 🧊 PAC Compressor Slot` (`domain: script`,
   `mode: queued`). Inputs: sibling `climate` list (or the caller’s climate +
   shared last-change `input_datetime`), `max_concurrent` (default 2),
   `start_stagger_seconds` (default 45), `global_change_interval` (seconds).
   Fields: requested climate entity, desired action (`start` with mode +
   temperature, or `stop`). On grant: call `climate.set_temperature` /
   `climate.turn_off` and stamp the last-change helper. On deny (at cap /
   stagger / interval): no climate write (caller stays off / keeps current
   state). Window-open and global off still `turn_off` **in the thermostat**,
   bypassing the interval (existing min-run exception). Frost may `start`
   even at cap.
2. **Thermostat hook.** When compressor-slot inputs are set, the conditioning
   `default` sequence (and frost heat) calls the script instead of
   `climate.set_temperature` directly. Occupancy gate is a thermostat
   `should_idle` input (optional occupancy entity + optional enable helper);
   unoccupied → idle (**off**, not eco setpoint), no slot request. Leave the
   script unused when inputs are empty so single-split installs stay as today.
3. **Defaults** on the thermostat blueprint only (R6). Live instances omit
   these keys today, so the next **human** import picks up 600 s / 0.5 °C.
   This PR does not import.

Helpers the docs must list (create-once, same package style as season helpers):
shared `input_datetime` last compressor change; optional `input_boolean` to
honor occupancy. Do not invent per-room helper forests.

## Tasks

- [ ] **Slot script contract.** Script accepts climate id + start/stop; queued
      so overlapping calls cannot all see concurrent=0. Acceptance: four
      near-simultaneous starts grant ≤ `max_concurrent`; later starts wait.
- [ ] **Stagger + global interval.** Second grant waits ≥ stagger after a
      start; stop also waits on the global interval unless the thermostat
      bypassed (window / season off). Acceptance: pytest timestamps (or
      freeze) show the delays.
- [ ] **Thermostat uses the grant.** Conditioning and frost paths call the
      script when configured; empty compressor inputs keep today’s direct
      climate services. Acceptance: existing thermostat behavior tests still
      pass with compressor inputs unset.
- [ ] **Occupancy gate.** Optional occupancy entity + enable helper: unoccupied
      → idle off (not eco drive); occupied still hits the cap. Acceptance:
      pytest with occupancy `off` does not call start.
- [ ] **Default bump.** `min_run_time` default 600, `cut_hysteresis` default
      0.5. Acceptance: blueprint YAML defaults + any fixture that asserted
      the old defaults updated. No boost/approach default changes.
- [ ] **Docs.** English: new script (if any) + thermostat compressor/occupancy
      inputs, helper table, GO-live warning (“do not re-enable live
      thermostats from this PR; `update-automations` is a later human GO”).
      README import URL if a new blueprint/script is user-facing.
- [ ] **Verify.** `pnpm run test:ha` (yamllint, `validate_blueprints.py`,
      pytest). Product PR; do not merge live config.

## Risks & mitigations

| Risk | Mitigation |
| ---- | ---------- |
| Race: five thermostats all count 0 concurrent and start | Queued script is the only climate writer for starts when configured. |
| Guardian `turn_off` fight with bang-bang | Do not implement a post-hoc killer automation (R5). |
| Occupied rooms wait forever at cap | Document FIFO/keep-running; occupancy-off rooms must not hold slots. |
| Frost skipped at cap | Frost bypasses cap (PRD open question 2). |
| Live 4-way start if someone re-enables early | Plan + docs + issue: ship PR only; GO live is explicit and later. |
| Shared last-change helper missing | Script no-ops grant (or skip compressor rules) when helper unset; docs list it as required for the guard. |

## Test plan

Seams: (1) compressor-slot script public service — grants/denies and climate
calls; (2) reversible-split thermostat public automation — idle vs start vs
frost vs occupancy, with compressor inputs on and off; (3) YAML defaults.

- [ ] Four climates request start together → ≤ cap climate writes, stagger
      between granted starts.
- [ ] Occupancy `off` → no start; occupancy `on` at cap → wait, no extra start.
- [ ] Window / season `off` → immediate `turn_off` (bypass interval).
- [ ] Frost at cap → start still granted.
- [ ] Thermostat without compressor inputs → unchanged climate services
      (existing tests).
- [ ] Default `min_run_time` / `cut_hysteresis` values in the blueprint.

## Recommended implementation order

1. Pytest for the slot script (cap, stagger, interval) — red.
2. Script blueprint — green.
3. Thermostat hook + occupancy — tests.
4. Default bump + fixture updates.
5. Docs / README.
6. Open product PR. **Stop.** No `update-automations`, no HA writes, no
   re-enable.

## Verification

- [ ] Lint / test / build: `pnpm run test:ha`
- [ ] Do **not** update foam / board (PR #28 owns that scaffold)
- [ ] Implementation PR description states: ship only; GO live is separate
