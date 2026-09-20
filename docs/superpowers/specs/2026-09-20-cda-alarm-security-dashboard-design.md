# CDA Alarm security dashboard & HA UI (design)

**Date:** 2026-09-20  
**Status:** Approved for planning  
**Target version:** 0.4.0  
**Package:** `packages/cda-alarm`

## Goal

Evolve the CDA Alarm sidebar panel into a **security dashboard** (default view) with live alarm state, sensors grouped by Home Assistant areas, configurable cameras, and role-based access for dashboard arm/disarm — while upgrading config forms to native Home Assistant `ha-*` controls.

## Decisions (locked)

| Topic | Choice |
| --- | --- |
| Dashboard host | Single Lit sidebar panel (not Lovelace) |
| Default tab | **Dashboard** |
| Room grouping | Home Assistant **areas** (`area_id`); fallback label **Unassigned** |
| Cameras | Camera list + optional **sensor → camera** map |
| Access | Configurable: `admin` \| `everyone` \| `users` (selected user ids) |
| ACL scope | Dashboard **view + arm/disarm**; **config tabs always admin** |
| Form controls | Prefer HA `ha-*` pickers/fields (light DOM) |

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  CDA Alarm panel (Lit, light DOM)                       │
│  Tabs: Dashboard* | Sensors | General | Response |      │
│        Cameras | Access | Linked                        │
│  * default; visible per ACL                             │
└─────────────┬───────────────────────────┬───────────────┘
              │ hass.states / areas       │ websocket
              ▼                           ▼
     alarm_control_panel          cda_alarm options
     + entity registry            (cameras, map, access)
```

- Panel registration: `require_admin=false` so non-admin users can load the module when ACL allows.
- Frontend hides config tabs for non-admins; backend enforces `update_config` admin-only and dashboard ACL for read/dashboard endpoints.
- Arm/disarm uses standard `alarm_control_panel` services (no custom arm websocket).

## UI

### Dashboard (default)

1. **Alarm header** — current state, `open_sensors`, arm home/away/night + disarm. PIN via `ha-textfield` when codes are required.
2. **Rooms** — sensors from `sensor_assignments`, grouped by HA area name; live open/closed (or on/off) from `hass.states`.
3. **Cameras** — grid of configured camera entities. When panel is `triggered`, highlight the camera from `sensor_camera_map` for the triggering sensor when known.

### Config tabs (admin only)

| Tab | Purpose |
| --- | --- |
| Sensors | Entity pickers + Away/Home/Night (existing) |
| General | Delays, keypads, codes (existing) |
| Response | Sirens / media / TTS (existing) |
| **Cameras** | Multi camera entities + optional sensor→camera map |
| **Access** | Mode admin / everyone / users + user multi-select |
| Linked | Existing linked automations |

Replace native `<select>` / `<input>` with `ha-entity-picker`, `ha-device-picker`, `ha-textfield`, `ha-switch`, and user picker/selector where available. Use **light DOM** (`createRenderRoot() { return this; }`) so HA theme and components behave reliably.

## Data model (config entry options)

```yaml
cameras:
  - camera.living_room
sensor_camera_map:
  binary_sensor.front_door: camera.living_room
access:
  mode: admin          # admin | everyone | users
  user_ids: []         # used when mode == users
```

Defaults: `cameras: []`, `sensor_camera_map: {}`, `access.mode: admin`, `access.user_ids: []`.

Admins are always allowed for dashboard ACL regardless of mode.

Normalize helpers live next to existing `sensors.py` / `response.py` (e.g. `access.py` or extend `sensors.merge_runtime_config`).

## Websocket API

| Command | Auth | Behavior |
| --- | --- | --- |
| `cda_alarm/get_dashboard` | Dashboard ACL | Structured snapshot: panel state, sensors by area, cameras, optional `highlighted_camera` |
| `cda_alarm/get_config` | Admin: full config. Non-admin with ACL: **dashboard-safe** subset only | No secrets beyond what dashboard needs |
| `cda_alarm/update_config` | **Admin only** | Persist options + reload (extend for cameras/access) |
| `cda_alarm/list_linked` | Admin only | Unchanged |

Unauthorized calls return websocket error `unauthorized` (or `not_allowed`).

## Access control details

1. Resolve current user from websocket connection / `hass.user`.
2. `is_admin` → allow dashboard + config.
3. Else if `access.mode == everyone` → dashboard only.
4. Else if `access.mode == users` and `user_id in user_ids` → dashboard only.
5. Else deny.

Panel shell: if denied, show a single “Access denied” view (no config leakage).

## Error handling

- Missing area → **Unassigned** group.
- Missing/unavailable camera or sensor → show unavailable state; do not crash.
- Failed arm/disarm → surface HA failure + existing `arm_failure` attribute.
- Camera display v1: HA camera entity / more-info style state only — **no** custom MJPEG proxy or NVR.

## Testing

- Pytest: access allow/deny matrix; `get_dashboard` area grouping + Unassigned; highlighted camera when triggered + map; options normalization defaults; `update_config` rejected for non-admin.
- Manual: dashboard live updates; arm/disarm with PIN; cameras tab; access mode switch; `ha-*` pickers on Sensors/General/Response.

## Documentation & release

- Update `docs/cda-alarm.md` and package README (Dashboard, Cameras, Access, ACL).
- Bump integration to **0.4.0**.
- After merge: tag `cda-alarm-v0.4.0` for HACS release.

## Out of scope (v1)

- Lovelace dashboard generation / export
- Multi-area alarm panels / multi-site
- Video recording / NVR integration
- Moving phone/Telegram into the panel (remain on `[CDA] Alarm Response`)
- Full frontend build toolchain beyond vendored/CDN Lit + HA globals

## Implementation sketch (for planning)

1. Backend: options schema + normalize; ACL helper; `get_dashboard`; tighten `get_config`/`update_config`; `require_admin=false` on panel.
2. Frontend: light DOM; Dashboard tab default; Cameras + Access tabs; `ha-*` on config forms.
3. Tests + docs + 0.4.0 + HACS tag.
