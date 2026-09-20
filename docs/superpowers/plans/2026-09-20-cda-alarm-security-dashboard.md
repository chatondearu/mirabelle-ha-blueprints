# CDA Alarm Security Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship CDA Alarm 0.4.0 with a default security Dashboard (live alarm + sensors by HA area + cameras), configurable dashboard ACL, Cameras/Access config tabs, and HA `ha-*` form controls.

**Architecture:** Keep one Lit sidebar panel. Store `cameras`, `sensor_camera_map`, and `access` in config entry options. Enforce ACL in websocket handlers; hide config tabs in the UI for non-admins. Dashboard reads live state from `hass`; arm/disarm uses standard alarm services.

**Tech Stack:** Home Assistant custom integration (Python 3.12), Lit ES module, HA `ha-*` web components, pytest-homeassistant-custom-component.

**Spec:** `docs/superpowers/specs/2026-09-20-cda-alarm-security-dashboard-design.md`

## Global Constraints

- Target HA version: **2025.5.3+**
- Integration version bump: **0.4.0**
- Blueprint/UI user-facing docs: **English**
- Conventional Commits with scope `cda-alarm` (or `docs`)
- No secrets in committed YAML
- Out of scope: Lovelace export, NVR, phone/Telegram in panel

## File map

| File | Responsibility |
| --- | --- |
| `packages/cda-alarm/custom_components/cda_alarm/const.py` | New CONF_/WS_/DEFAULT_ACCESS constants |
| `packages/cda-alarm/custom_components/cda_alarm/access.py` | Normalize access + `user_can_use_dashboard` |
| `packages/cda-alarm/custom_components/cda_alarm/cameras.py` | Normalize cameras + sensor_camera_map |
| `packages/cda-alarm/custom_components/cda_alarm/dashboard.py` | Build dashboard snapshot (areas grouping) |
| `packages/cda-alarm/custom_components/cda_alarm/sensors.py` | Merge cameras/access into runtime config |
| `packages/cda-alarm/custom_components/cda_alarm/websocket_api.py` | ACL, get_dashboard, gated get/update |
| `packages/cda-alarm/custom_components/cda_alarm/panel.py` | `require_admin=False` |
| `packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js` | Dashboard + Cameras + Access + ha-* |
| `packages/cda-alarm/tests/test_access.py` | ACL unit tests |
| `packages/cda-alarm/tests/test_dashboard.py` | Dashboard snapshot + WS ACL tests |
| `docs/cda-alarm.md`, `packages/cda-alarm/README.md` | User docs |
| `manifest.json` | Version 0.4.0 |

---

### Task 1: Access + cameras normalize helpers

**Files:**
- Create: `packages/cda-alarm/custom_components/cda_alarm/access.py`
- Create: `packages/cda-alarm/custom_components/cda_alarm/cameras.py`
- Modify: `packages/cda-alarm/custom_components/cda_alarm/const.py`
- Test: `packages/cda-alarm/tests/test_access.py`

**Interfaces:**
- Produces: `normalize_access(raw) -> dict`, `user_can_use_dashboard(access, *, is_admin, user_id) -> bool`
- Produces: `normalize_cameras(raw) -> list[str]`, `normalize_sensor_camera_map(raw) -> dict[str, str]`

- [ ] **Step 1: Write failing tests**

```python
# packages/cda-alarm/tests/test_access.py
from custom_components.cda_alarm.access import normalize_access, user_can_use_dashboard
from custom_components.cda_alarm.cameras import (
    normalize_cameras,
    normalize_sensor_camera_map,
)


def test_normalize_access_defaults() -> None:
    assert normalize_access(None) == {"mode": "admin", "user_ids": []}


def test_dashboard_acl_matrix() -> None:
    admin_only = {"mode": "admin", "user_ids": []}
    assert user_can_use_dashboard(admin_only, is_admin=True, user_id="u1")
    assert not user_can_use_dashboard(admin_only, is_admin=False, user_id="u1")

    everyone = {"mode": "everyone", "user_ids": []}
    assert user_can_use_dashboard(everyone, is_admin=False, user_id="u1")

    users = {"mode": "users", "user_ids": ["u2"]}
    assert user_can_use_dashboard(users, is_admin=False, user_id="u2")
    assert not user_can_use_dashboard(users, is_admin=False, user_id="u1")
    assert user_can_use_dashboard(users, is_admin=True, user_id="u1")


def test_normalize_cameras_and_map() -> None:
    assert normalize_cameras(["camera.a", 1, ""]) == ["camera.a"]
    assert normalize_sensor_camera_map(
        {"binary_sensor.door": "camera.a", "bad": 3}
    ) == {"binary_sensor.door": "camera.a"}
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd /hdd/dev/chatondearu/mirabelle-ha-blueprints
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_access.py -q'
```

Expected: `ModuleNotFoundError` or import errors for `access` / `cameras`.

- [ ] **Step 3: Add constants**

Append to `const.py`:

```python
CONF_CAMERAS = "cameras"
CONF_SENSOR_CAMERA_MAP = "sensor_camera_map"
CONF_ACCESS = "access"
CONF_ACCESS_MODE = "mode"
CONF_ACCESS_USER_IDS = "user_ids"

ACCESS_MODE_ADMIN = "admin"
ACCESS_MODE_EVERYONE = "everyone"
ACCESS_MODE_USERS = "users"
ACCESS_MODES = (ACCESS_MODE_ADMIN, ACCESS_MODE_EVERYONE, ACCESS_MODE_USERS)

DEFAULT_ACCESS: dict = {
    CONF_ACCESS_MODE: ACCESS_MODE_ADMIN,
    CONF_ACCESS_USER_IDS: [],
}

WS_TYPE_GET_DASHBOARD = f"{DOMAIN}/get_dashboard"
```

- [ ] **Step 4: Implement helpers**

```python
# access.py
from __future__ import annotations
from typing import Any
from .const import (
    ACCESS_MODE_ADMIN,
    ACCESS_MODE_EVERYONE,
    ACCESS_MODE_USERS,
    ACCESS_MODES,
    CONF_ACCESS_MODE,
    CONF_ACCESS_USER_IDS,
    DEFAULT_ACCESS,
)

def normalize_access(raw: Any) -> dict[str, Any]:
    base = {
        CONF_ACCESS_MODE: DEFAULT_ACCESS[CONF_ACCESS_MODE],
        CONF_ACCESS_USER_IDS: [],
    }
    if not isinstance(raw, dict):
        return base
    mode = raw.get(CONF_ACCESS_MODE, ACCESS_MODE_ADMIN)
    if mode not in ACCESS_MODES:
        mode = ACCESS_MODE_ADMIN
    user_ids = [
        uid for uid in (raw.get(CONF_ACCESS_USER_IDS) or []) if isinstance(uid, str) and uid
    ]
    return {CONF_ACCESS_MODE: mode, CONF_ACCESS_USER_IDS: user_ids}


def user_can_use_dashboard(
    access: dict[str, Any],
    *,
    is_admin: bool,
    user_id: str | None,
) -> bool:
    if is_admin:
        return True
    mode = access.get(CONF_ACCESS_MODE, ACCESS_MODE_ADMIN)
    if mode == ACCESS_MODE_EVERYONE:
        return True
    if mode == ACCESS_MODE_USERS:
        return bool(user_id) and user_id in (access.get(CONF_ACCESS_USER_IDS) or [])
    return False
```

```python
# cameras.py
from __future__ import annotations
from typing import Any

def normalize_cameras(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [e for e in raw if isinstance(e, str) and e.startswith("camera.")]


def normalize_sensor_camera_map(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for sensor, camera in raw.items():
        if isinstance(sensor, str) and isinstance(camera, str) and camera.startswith("camera."):
            out[sensor] = camera
    return out
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_access.py -q'
```

Expected: all passed.

- [ ] **Step 6: Commit**

```bash
git add packages/cda-alarm/custom_components/cda_alarm/const.py \
  packages/cda-alarm/custom_components/cda_alarm/access.py \
  packages/cda-alarm/custom_components/cda_alarm/cameras.py \
  packages/cda-alarm/tests/test_access.py
git commit -m "feat(cda-alarm): add access and camera option normalizers"
```

---

### Task 2: Merge runtime config + panel require_admin=false

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/sensors.py`
- Modify: `packages/cda-alarm/custom_components/cda_alarm/panel.py`
- Modify: `packages/cda-alarm/custom_components/cda_alarm/config_flow.py` (user create defaults)
- Test: extend `packages/cda-alarm/tests/test_sensors.py`

**Interfaces:**
- Consumes: `normalize_access`, `normalize_cameras`, `normalize_sensor_camera_map`
- Produces: `merge_runtime_config` includes `cameras`, `sensor_camera_map`, `access`

- [ ] **Step 1: Failing test in `test_sensors.py`**

```python
from custom_components.cda_alarm.const import CONF_ACCESS, CONF_CAMERAS, CONF_SENSOR_CAMERA_MAP
from custom_components.cda_alarm.sensors import merge_runtime_config

def test_merge_runtime_config_includes_cameras_and_access() -> None:
    merged = merge_runtime_config({})
    assert merged[CONF_CAMERAS] == []
    assert merged[CONF_SENSOR_CAMERA_MAP] == {}
    assert merged[CONF_ACCESS]["mode"] == "admin"
```

- [ ] **Step 2: Run — expect FAIL** (KeyError)

- [ ] **Step 3: Update `merge_runtime_config`**

At end of `merge_runtime_config`, before `return merged`:

```python
from .access import normalize_access
from .cameras import normalize_cameras, normalize_sensor_camera_map
from .const import CONF_ACCESS, CONF_CAMERAS, CONF_SENSOR_CAMERA_MAP

# inside merge_runtime_config:
merged[CONF_CAMERAS] = normalize_cameras(merged.get(CONF_CAMERAS))
merged[CONF_SENSOR_CAMERA_MAP] = normalize_sensor_camera_map(
    merged.get(CONF_SENSOR_CAMERA_MAP)
)
merged[CONF_ACCESS] = normalize_access(merged.get(CONF_ACCESS))
```

In `config_flow.py` user create `data={...}` add:

```python
CONF_CAMERAS: [],
CONF_SENSOR_CAMERA_MAP: {},
CONF_ACCESS: normalize_access(None),
```

In `panel.py` set `require_admin=False`.

- [ ] **Step 4: Run sensors + access tests — PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(cda-alarm): merge camera/access options and open panel to ACL users"
```

---

### Task 3: Dashboard snapshot builder

**Files:**
- Create: `packages/cda-alarm/custom_components/cda_alarm/dashboard.py`
- Test: `packages/cda-alarm/tests/test_dashboard.py`

**Interfaces:**
- Produces: `build_dashboard(hass, entry, panel_entity_id: str) -> dict`

Snapshot shape:

```python
{
  "entry_id": str,
  "panel_entity_id": str,
  "state": str | None,
  "attributes": dict,  # open_sensors, arm_failure, arm_mode, code_format hints
  "areas": [
    {"area_id": str | None, "name": str, "sensors": [
      {"entity_id": str, "name": str, "state": str, "open": bool}
    ]}
  ],
  "cameras": [{"entity_id": str, "name": str, "state": str}],
  "highlighted_camera": str | None,
  "access": {"mode": str},  # no need to expose full user_ids to non-admin UI beyond mode
  "can_configure": bool,
}
```

- [ ] **Step 1: Write failing tests**

```python
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import DOMAIN
from custom_components.cda_alarm.dashboard import build_dashboard


@pytest.mark.asyncio
async def test_build_dashboard_groups_by_area(hass: HomeAssistant) -> None:
    area = ar.async_get(hass).async_create("Kitchen")
    hass.states.async_set("binary_sensor.door", "on")
    hass.states.async_set("binary_sensor.orphan", "off")
    reg = er.async_get(hass)
    reg.async_get_or_create("binary_sensor", "test", "door", suggested_object_id="door")
    ent = reg.async_get("binary_sensor.door")
    reg.async_update_entity(ent.entity_id, area_id=area.id)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "CDA Alarm",
            "sensor_assignments": [
                {"entity_id": "binary_sensor.door", "modes": ["away"]},
                {"entity_id": "binary_sensor.orphan", "modes": ["away"]},
            ],
            "cameras": ["camera.kitchen"],
            "sensor_camera_map": {"binary_sensor.door": "camera.kitchen"},
            "access": {"mode": "everyone", "user_ids": []},
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set(
        "alarm_control_panel.cda_alarm",
        "triggered",
        {"open_sensors": {"binary_sensor.door": "on"}},
    )
    hass.states.async_set("camera.kitchen", "idle")

    snap = build_dashboard(hass, entry, "alarm_control_panel.cda_alarm")
    names = {a["name"] for a in snap["areas"]}
    assert "Kitchen" in names
    assert "Unassigned" in names
    assert snap["highlighted_camera"] == "camera.kitchen"
    assert snap["state"] == "triggered"
```

- [ ] **Step 2: Run — expect FAIL** (missing module)

- [ ] **Step 3: Implement `dashboard.py`**

Logic:
1. `merge_runtime_config` from entry data/options.
2. Collect entity ids from assignments.
3. Resolve area via `entity_registry` → `area_registry` (name); else Unassigned.
4. `open` if state in `{"on", "open"}`.
5. `highlighted_camera`: if panel state is `triggered`, pick first key in `open_sensors` attributes mapped via `sensor_camera_map`, else None.
6. Include configured cameras with current states.

- [ ] **Step 4: Tests PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(cda-alarm): build dashboard snapshot grouped by area"
```

---

### Task 4: Websocket ACL + get_dashboard

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/websocket_api.py`
- Modify: `packages/cda-alarm/tests/test_dashboard.py` (or `test_panel_api.py`)

**Interfaces:**
- Consumes: `user_can_use_dashboard`, `build_dashboard`, `normalize_*`
- Produces: WS command `cda_alarm/get_dashboard`
- Changes: `get_config` / `update_config` / `list_linked` auth behavior per spec

Auth helpers:

```python
def _connection_user(connection) -> tuple[bool, str | None]:
    user = getattr(connection, "user", None)
    if user is None:
        return False, None
    return bool(getattr(user, "is_admin", False)), getattr(user, "id", None)


def _require_dashboard_acl(hass, connection, entry) -> bool:
    merged = merge_runtime_config({**entry.data, **entry.options})
    is_admin, user_id = _connection_user(connection)
    return user_can_use_dashboard(
        merged.get(CONF_ACCESS) or normalize_access(None),
        is_admin=is_admin,
        user_id=user_id,
    )
```

- [ ] **Step 1: Failing tests**

```python
@pytest.mark.asyncio
async def test_get_dashboard_denied_for_non_acl_user(hass):
    # setup entry access.mode=admin
    # mock connection user is_admin=False
    # call ws_get_dashboard.__wrapped__ unwrap helper
    # expect connection.send_error(..., "unauthorized", ...)


@pytest.mark.asyncio
async def test_update_config_denied_for_non_admin(hass):
    # access.mode=everyone, user non-admin
    # update_config -> unauthorized


@pytest.mark.asyncio
async def test_get_dashboard_ok_for_everyone(hass):
    # access.mode=everyone, non-admin
    # send_result with areas key
```

Reuse `_ws_handler` unwrap from `test_panel_api.py` (move to conftest if useful).

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement WS changes**

1. Register `ws_get_dashboard`.
2. Remove `@websocket_api.require_admin` from `get_config` and `get_dashboard`; keep it on `update_config` and `list_linked` **or** manually check admin (prefer explicit checks for clearer errors).
3. `get_config`: if not admin and not dashboard ACL → unauthorized; if dashboard ACL non-admin → return dashboard-safe subset (`entry_id`, `panel_entity_id`, assignments, cameras, map, access.mode, delays read-only optional — **omit codes**).
4. `update_config`: persist `CONF_CAMERAS`, `CONF_SENSOR_CAMERA_MAP`, `CONF_ACCESS` via normalizers; admin only.
5. `get_dashboard`: ACL check then `build_dashboard`.

- [ ] **Step 4: Full package tests PASS**

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests -q'
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(cda-alarm): add get_dashboard websocket with ACL gates"
```

---

### Task 5: Frontend Dashboard tab (default) + light DOM

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js`

**Interfaces:**
- Consumes: `cda_alarm/get_dashboard`, alarm services
- Produces: default `_tab = "dashboard"`; Access denied view

- [ ] **Step 1: Switch to light DOM**

```js
createRenderRoot() {
  return this;
}
```

Keep styles injectable via a `<style>` in render or adopt HA CSS variables on host.

- [ ] **Step 2: Add dashboard state + load**

Properties: `_dashboard`, `_isAdmin`, `_denied`, `_pin`.

On hass update:
1. Call `cda_alarm/get_dashboard` (and if admin, `get_config` for config tabs).
2. On unauthorized → `_denied = true`.

- [ ] **Step 3: Render Dashboard**

- Header with state badge + arm/disarm buttons calling:

```js
await this.hass.callService("alarm_control_panel", "alarm_arm_away", {
  entity_id: this._dashboard.panel_entity_id,
  code: this._pin || undefined,
});
```

- Areas sections from `_dashboard.areas`
- Camera tiles; add CSS class when `entity_id === highlighted_camera`
- Tabs list: if `_isAdmin` show config tabs; always show Dashboard when not denied

- [ ] **Step 4: Manual smoke checklist in commit message / docs note**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(cda-alarm): add live security dashboard as default panel tab"
```

---

### Task 6: Cameras + Access tabs + ha-* pickers on config

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js`

- [ ] **Step 1: Cameras tab UI**

- `ha-entity-picker` `.includeDomains=${['camera']}` `.hass=${this.hass}` multi via repeated add
- Map rows: sensor picker (from assignments) + camera picker
- Save via existing `update_config` payload fields `cameras`, `sensor_camera_map`

- [ ] **Step 2: Access tab UI**

- Mode: `ha-select` or radio: admin / everyone / users
- When users: multi user picker — prefer `ha-user-picker` if present, else select from `Object.values(this.hass.users || {})` / `hass.user` list via `hass.connection.sendMessagePromise({type: "config/auth/list"})` best-effort; store `user_ids`

- [ ] **Step 3: Replace native controls on Sensors/General/Response**

| Field | Component |
| --- | --- |
| Add sensor | `ha-entity-picker` |
| Delays | `ha-textfield` type number |
| Block arm | `ha-switch` |
| Keypad device | `ha-device-picker` (or keep select over zha_devices if picker flaky) |
| Sirens / media / TTS players | `ha-entity-picker` domain-filtered |
| Codes JSON | `ha-textfield` multiline |

Wire `@value-changed` / `@change` per HA component conventions (`.value` + `e.detail.value`).

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(cda-alarm): add cameras/access tabs and ha-* form controls"
```

---

### Task 7: Docs, version 0.4.0, full test suite, HACS tag

**Files:**
- Modify: `docs/cda-alarm.md`, `packages/cda-alarm/README.md`
- Modify: `packages/cda-alarm/custom_components/cda_alarm/manifest.json` → `"version": "0.4.0"`
- Modify: `packages/cda-alarm/tests/test_config_flow.py` assert version `0.4.0`

- [ ] **Step 1: Docs sections** — Dashboard, Cameras, Access ACL, upgrade note 0.4.0, changelog entry

- [ ] **Step 2: Bump version + fix test assertion**

- [ ] **Step 3: Run full package tests**

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests -q'
```

Expected: all passed.

- [ ] **Step 4: Commit + push PR**

```bash
git add docs/cda-alarm.md packages/cda-alarm/README.md \
  packages/cda-alarm/custom_components/cda_alarm/manifest.json \
  packages/cda-alarm/tests/test_config_flow.py
git commit -m "docs(cda-alarm): document security dashboard and bump 0.4.0"
git push -u origin HEAD
gh pr create --title "feat(cda-alarm): security dashboard and ACL" --body "..."
```

- [ ] **Step 5: After merge** — tag `cda-alarm-v0.4.0` and confirm HACS release workflow success.

---

## Spec coverage check

| Spec requirement | Task |
| --- | --- |
| Dashboard default tab | 5 |
| Sensors by HA area + Unassigned | 3, 5 |
| Cameras list + sensor map | 1, 2, 4, 6 |
| Access modes admin/everyone/users | 1, 4, 6 |
| ACL: dashboard+arm; config admin | 4, 5 |
| ha-* controls + light DOM | 5, 6 |
| get_dashboard WS | 4 |
| Tests ACL + dashboard | 1, 3, 4 |
| Docs + 0.4.0 + HACS tag | 7 |
| Out of scope respected | Global constraints |

## Placeholder scan

No TBD/TODO left in task steps; concrete APIs and commands included.
