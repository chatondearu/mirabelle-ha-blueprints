# CDA Alarm: ACL state notifications & Frient ZHA one-way mirror

**Date:** 2026-09-20  
**Status:** Approved for implementation (queued after in-flight session work)  
**Package:** `packages/cda-alarm`  
**Related:**  
`docs/superpowers/specs/2026-09-20-cda-alarm-design.md`,  
`docs/superpowers/specs/2026-09-20-cda-alarm-security-dashboard-design.md`,  
`docs/frient-keypad-with-alarmo.md`

## Problem

Two gaps after the security dashboard / input-only Frient binding:

1. **Phone notifications** — Dashboard ACL users (`access.mode` / `user_ids`) see the panel in HA, but do not receive Companion notifications on arm / disarm / trigger. Phone alerts still live only on **[CDA] Alarm Response** with a manual `notify.*` list, which diverges from Access ACL.
2. **Frient stays armed** — Disarm via NFC / UI / app updates `alarm_control_panel.cda_alarm` only. The Frient ZHA `alarm_control_panel` entity and the physical KEPZB-110 can remain armed because CDA never mirrors state onto the ZHA panel (by v1 design).

## Goals

- Notify Companion phones of **dashboard-authorized** users on meaningful panel state changes.
- Optionally mirror CDA panel state **one-way** onto each configured Frient ZHA alarm panel so entity + hardware leave armed when CDA disarms elsewhere.
- Keep **CDA Alarm** as the single security source of truth (PIN / sensors / trigger logic).
- Best-effort side effects: Zigbee or notify failures must never block arm/disarm/trigger.

## Non-goals

- Bidirectional Frient ↔ CDA sync (old Alarmo dual-panel model).
- Telegram or arbitrary notify lists inside CDA (remain on Alarm Response).
- Notifications for `arming` / `pending`.
- Perfect IAS ACE LED/countdown fidelity beyond what ZHA already allows.
- Mapping users without a Companion `mobile_app` entry (no SMS / email fallback).

---

## Feature 1 — ACL state notifications

### Behavior

| Panel state | Notify? | Companion style |
| --- | --- | --- |
| `armed_home` / `armed_away` / `armed_night` | Yes | Normal |
| `disarmed` | Yes | Normal |
| `triggered` | Yes | Critical / time-sensitive (iOS/Android Companion patterns) |
| `arming` / `pending` / other | No | — |

Messages: short English strings, e.g. `CDA Alarm: armed away`, `CDA Alarm: disarmed`, `CDA Alarm: triggered`. Never include PIN / codes / RFID.

### Recipients (auto)

Resolve `notify.mobile_app_*` services whose Home Assistant **user id** is allowed by dashboard ACL:

| `access.mode` | Recipients |
| --- | --- |
| `admin` | Users with admin privileges who have a Companion app |
| `everyone` | All HA users that have at least one `mobile_app` config entry |
| `users` | Listed `access.user_ids` **plus** admins (admins always have dashboard ACL) |

**Discovery rule (implementation):** iterate `mobile_app` config entries; read the owning `user_id` from entry data; map entry → notify service domain/service used by that device (existing HA / Companion naming). Skip entries without a resolvable notify service. Deduplicate services.

### Opt-in

- New option under Access (or nested in `access`): `state_notifications: bool`, default **`true`**.
- When `false`, no state notifications are sent (Alarm Response unchanged).

### Architecture

```text
alarm_control_panel.cda_alarm state change
        │
        ▼
┌───────────────────────────┐
│ CdaAlarmStateNotifier     │
│ filter armed_*/disarmed/  │
│ triggered                 │
│ resolve ACL → mobile_app  │
│ notify.* best-effort      │
└───────────────────────────┘
```

- New module e.g. `notifications.py` (or `state_notify.py`): normalize flag + recipient resolution + send.
- Wire listener in `async_setup_entry` (same lifecycle as keypad listener), tracking the CDA panel entity id.
- Do **not** fold this into `CdaAlarmResponseRunner` (sirens/media stay trigger-only).

### Overlap with Alarm Response

- Alarm Response may still notify a manual list on `triggered`.
- Document: clear duplicate phone targets on Alarm Response if CDA state notifications cover the same phones for `triggered`, or accept double notify until cleaned up.
- No automatic disable of the blueprint.

### UI

- Access tab: boolean « State notifications » (Companion) with short help text: auto-targets phones of users who can open the dashboard.

### Tests

- Recipient matrix: admin / everyone / users (+ admin always included in users mode).
- Only armed_* / disarmed / triggered fire notify; arming/pending do not.
- `state_notifications: false` → no service calls.
- Missing mobile_app / notify failure → no exception to panel transitions.
- Critical payload present for `triggered` only.

---

## Feature 2 — Frient ZHA one-way mirror

### Behavior

When enabled per keypad, every CDA panel state change that maps to a ZHA alarm service is pushed to that keypad’s **ZHA** `alarm_control_panel` entity:

| CDA state | Action on Frient ZHA panel |
| --- | --- |
| `disarmed` | `alarm_disarm` |
| `armed_home` | `alarm_arm_home` |
| `armed_away` | `alarm_arm_away` |
| `armed_night` | `alarm_arm_night` |
| `triggered` | `alarm_trigger` (if supported; else best-effort skip / log) |
| `arming` / `pending` | No ZHA service (optional: keep IAS ACE LED feedback only) |

CDA remains the only panel that validates codes and owns sensors. Keypad **input** stays `zha_event` → CDA services only (unchanged).

### Opt-in

- Per keypad entry: `sync_zha_panel: bool`, default **`false`**.
- Distinct from existing IAS ACE `feedback` (LEDs/buzzer). Recommend enabling **both** when hardware LEDs still lag after ZHA entity sync, but ZHA entity sync is the fix for “entity + physical armed after NFC disarm”.

### Resolving the ZHA panel entity

For each configured keypad `device_id`:

1. Find `alarm_control_panel` entities in the entity registry linked to that device.
2. Prefer the ZHA-domain panel; ignore CDA’s own panel.
3. If none / multiple, log debug and skip (or first match with warning).

### Codes on the ZHA panel

- Prefer calling ZHA arm/disarm **without** a code when the entity does not require one.
- If the ZHA panel requires a code, use a dedicated optional per-keypad `zha_mirror_code` (stored in options, never logged) **or** skip mirror with a warning — decide in implementation plan after checking live KEPZB-110 entity attributes (`code_arm_required`). Prefer empty code first; add `zha_mirror_code` only if required in testing.

### Architecture

```text
NFC / UI / app / keypad zha_event
        │
        ▼
 alarm_control_panel.cda_alarm   ←── sole truth
        │
        ├── StateNotifier (Feature 1)
        ├── IAS ACE feedback (existing, opt-in)
        └── ZHA panel mirror (Feature 2, opt-in)
                 └── alarm_* on Frient ZHA entity
```

Extend `keypad.py` (or small `zha_mirror.py`) so state-change tracking already used for feedback also drives ZHA services when `sync_zha_panel` is true. Failures caught; never raise into the panel state machine.

### Loop / echo guard

- Do **not** listen to Frient ZHA panel state as a command source.
- When CDA arms because of a keypad event, ZHA may already be armed locally; mirror call should be idempotent (same target state → no-op or harmless re-call).
- Deduplicate consecutive identical target states per device (same pattern as `last_status` for feedback).

### UI

- General / keypad row: checkbox « Sync ZHA panel state » with help: mirrors CDA onto the keypad’s ZHA alarm entity (and typically the physical armed state).

### Tests

- Disarm CDA → `alarm_disarm` called on linked ZHA entity when sync enabled.
- Sync disabled → no ZHA alarm service calls.
- ZHA service raises → CDA still disarms; error logged at debug.
- Keypad without ZHA alarm entity → no crash.

---

## Config shape (options)

```yaml
access:
  mode: users          # admin | everyone | users
  user_ids: ["..."]
  state_notifications: true

keypads:
  - device_id: "..."
    is_default: true
    feedback: false          # IAS ACE LEDs (existing)
    sync_zha_panel: false    # Feature 2
    endpoint: 44
    # zha_mirror_code: "...."  # only if proven required
```

Normalize in existing `normalize_access` / `normalize_keypads` paths; persist via current `update_config` websocket.

## Documentation & release

- Update `docs/cda-alarm.md` and package README (Access notifications; keypad ZHA sync).
- Note Alarm Response overlap for `triggered` phones.
- Bump integration version when shipping (likely **0.4.x** or **0.5.0** depending on what the in-flight session already released — set in implementation plan against current `manifest.json`).

## Out of scope

- Re-enabling the old Frient blueprint mirror while native sync is on (document mutual exclusion).
- Per-user notification toggles beyond ACL membership.
- Localizing notification strings (English only, repo standard).

## Implementation order (when unblocking)

1. Feature 1 — state notifier + Access UI + tests + docs.  
2. Feature 2 — ZHA one-way mirror + keypad UI + tests + docs.  
3. Manual HA check: arm → NFC disarm → Frient entity/LEDs clear; ACL user receives arm/disarm/trigger notifies.

## Success criteria

- [ ] ACL Companion users get notifies on arm / disarm / triggered only.  
- [ ] `state_notifications: false` silences Feature 1.  
- [ ] With `sync_zha_panel`, NFC/UI disarm clears Frient ZHA entity (and physical armed when ZHA drives it).  
- [ ] CDA remains sole code/sensor authority; mirror and notify never block transitions.  
- [ ] Pytest covers ACL recipient matrix, notify filter, and ZHA mirror happy/error paths.
