# CDA Alarm state notify + Frient ZHA mirror — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship ACL Companion state notifications (arm/disarm/triggered) and optional one-way CDA → Frient ZHA panel sync.

**Architecture:** New `notifications.py` listens to the CDA panel and notifies `mobile_app` services for ACL users. Extend `keypad.py` to call ZHA `alarm_*` services when `sync_zha_panel` is enabled. Access/UI options persist via existing websocket `update_config`.

**Tech Stack:** Home Assistant custom integration (`cda_alarm`), pytest + `pytest-homeassistant-custom-component`, Lit sidebar panel JS.

**Spec:** `docs/superpowers/specs/2026-09-20-cda-alarm-state-notify-and-frient-mirror-design.md`

## Global Constraints

- Home Assistant **2025.5.3+**; repo English for user-facing docs/strings in docs/
- CDA panel remains sole security truth; notify/mirror are best-effort and never block transitions
- Notify only `armed_*` / `disarmed` / `triggered`; auto Companion via ACL; `state_notifications` default `true`
- ZHA mirror opt-in per keypad (`sync_zha_panel` default `false`); no bidirectional sync
- Version bump to **0.5.0**

## File map

| File | Role |
| --- | --- |
| `const.py` | New access/keypad option keys + defaults |
| `access.py` | Normalize `state_notifications` |
| `notifications.py` | ACL → mobile_app resolve + state listener |
| `sensors.py` | Normalize `sync_zha_panel` on keypads |
| `keypad.py` | One-way ZHA alarm panel mirror on state change |
| `__init__.py` | Wire notifier unload |
| `frontend/cda-alarm-panel.js` | Access + keypad UI toggles |
| `tests/test_access.py`, `test_notifications.py`, `test_keypad.py` | Coverage |
| `docs/cda-alarm.md`, package README, `manifest.json` | Docs + version |

---

### Task 1: Access flag + keypad sync field

- [ ] Add `CONF_ACCESS_STATE_NOTIFICATIONS`, `CONF_KEYPAD_SYNC_ZHA_PANEL` (+ defaults) in `const.py`
- [ ] Extend `normalize_access` / `DEFAULT_ACCESS`; extend `normalize_keypads` / legacy / resolve defaults
- [ ] Update `test_access.py` expectations
- [ ] Commit: `feat(cda-alarm): add state notify and zha sync option fields`

### Task 2: State notifier

- [ ] Add failing tests in `test_notifications.py` (ACL matrix, filter states, critical, disabled)
- [ ] Implement `notifications.py` + `async_setup_state_notifier` in `__init__.py`
- [ ] Tests pass
- [ ] Commit: `feat(cda-alarm): notify ACL companion phones on arm disarm trigger`

### Task 3: ZHA one-way mirror

- [ ] Extend `test_keypad.py` for sync on/off and error tolerance
- [ ] Implement mirror in `keypad.py` (resolve ZHA alarm entity; track state when feedback or sync)
- [ ] Tests pass
- [ ] Commit: `feat(cda-alarm): optionally mirror cda state to frient zha panel`

### Task 4: UI + docs + 0.5.0

- [ ] Access toggle + keypad « Sync ZHA panel » in `cda-alarm-panel.js`
- [ ] Docs + README + changelog 0.5.0 + manifest
- [ ] Commit: `feat(cda-alarm): expose notify and zha sync in panel ui`

### Task 5: Verify

- [ ] `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests -q'`
