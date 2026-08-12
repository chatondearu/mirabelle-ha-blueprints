# Design: Reliable cover manual-override detection

**Date:** 2026-08-13  
**Status:** Implemented  
**Scope:** `packages/cover-manager` (primary), blueprint docs touch-up if needed  
**Related incident:** 2026-08-12 — north shutters skipped night close after an automation-driven open at 20:29

## Problem

The Smart Cover blueprint treats a cover as “manually overridden” when:

- it changed recently (Manual Override Hold, default 60 minutes), and
- `cover.context` is present, and
- `cover.context.parent_id` is `none`.

Cover Manager updates position during travel with `async_write_ha_state()` **after** the originating service call has returned. Those writes get a fresh context with `parent_id=None` / `user_id=None`, even when the move was started by an automation.

Result: **automation moves are misclassified as manual**, so night closing (which correctly respects real manual override) is blocked for up to 60 minutes.

Evidence from the live instance:

- No cover change that evening had a `user_id` (nobody used the UI as a user).
- North covers opened at 20:29 because the solar automation itself raised them 25% → 100%.
- After moves, live state still shows `parent_id: null`.
- Sunset closed south only; north closed at 21:30 when the false override window expired.

## Goal (option B)

Keep behavior **B**:

- A **real** manual action (wall switch or UI) starts the override timer and may delay night closing.
- Automation-driven moves must **not** start that timer.
- No “reset timer on manual close” for this change: if the cover is already at night position, the automation is a no-op (`delta == 0`).

## Non-goals

- Changing night vs comfort `forced_move` rules (night already respects override; docs already say so).
- Reworking contact-link vs group-cover configuration (separate issue).
- Detecting override via new helpers / `input_text` maps.

## Approaches considered

| Approach | Pros | Cons |
| -------- | ---- | ---- |
| **1. Propagate command context in Cover Manager** | Fixes root cause; blueprint heuristic stays valid; wall switch still looks “manual” | Requires integration change + HACS sync |
| 2. Blueprint: `user_id` only | Tiny YAML change | Misses wall-switch presses |
| 3. Blueprint: “last automation command” helper | No integration change | Heavy, multi-cover, groups fragile |

**Chosen:** Approach 1.

## Design

### Cover Manager

When a cover command is accepted from HA (`async_open_cover`, `async_close_cover`, `async_stop_cover`, `async_set_cover_position`):

1. Capture the entity’s current HA context at command entry (the service-call context, including `parent_id` when an automation called the service).
2. Store it as an active command context for the duration of that movement.
3. Before every state write during that movement (`async_write_ha_state` / `_update_and_notify`), restore that context on the entity so position ticks keep `parent_id` / `user_id`.
4. Clear the stored context when movement becomes idle (stop, target reached, or cancelled).

Wall-switch path (`_handle_switch_event` → movement without a cover service parent):

- Do **not** invent an automation parent.
- Writes keep a context with `parent_id=None` → blueprint correctly treats them as manual.

### Blueprint

- No logic change required for option B once Cover Manager preserves context.
- Keep: night respects manual override; away/wind/contact remain forced.
- Docs already describe night + override correctly; add a short troubleshooting note that Cover Manager ≥ fixed version is required for reliable detection (version bump in manifest when shipping).

### Tests

Cover Manager:

- After `cover.set_cover_position` invoked under a context with `parent_id` set, intermediate and final cover states retain that `parent_id`.
- After a simulated switch-driven move (no service parent), states keep `parent_id is None`.

Blueprint (optional smoke):

- Existing tests already disable override (`manual_override_minutes: 0`); no mandatory change if Cover Manager tests cover the root cause.

### Rollout

1. Implement + test in monorepo `packages/cover-manager`.
2. Bump integration version / changelog.
3. Sync to HACS sub-repo via existing workflow.
4. Update HA instance; verify after an automation move that `cover.*` state context still has `parent_id`.

## Success criteria

- Automation opens/closes a Cover Manager cover → for the whole travel, `context.parent_id` remains the automation run (or at least non-`none`).
- Wall-switch move → `parent_id` stays `none` → override timer applies (including delaying night close).
- Scenario of 2026-08-12 cannot recur: automation comfort open shortly before sunset must not block night close.

## Out of scope follow-ups

- Align `cover_contact_links` with managed group entities (`shutters_north` / `shutters_south`) so contact opening works on the entities the automation actually controls.
- Optional later: clear override early when position already matches the automation target.
