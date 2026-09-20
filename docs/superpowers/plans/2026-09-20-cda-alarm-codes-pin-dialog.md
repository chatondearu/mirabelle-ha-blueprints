# CDA Alarm Codes Editor + PIN Dialog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship CDA Alarm **0.5.1** with a structured PIN/RFID/NFC codes editor and a Dashboard PIN dialog when credentials are configured.

**Architecture:** Keep codes in config entry options. Replace the General-tab JSON textarea with editable rows. Expose `code_required` on the dashboard snapshot from the panel entity attributes. Gate Dashboard arm/disarm behind a Lit modal when `code_required` is true. Raise `HomeAssistantError` on invalid codes so `callService` fails visibly; catch that in the keypad path so Frient feedback still runs.

**Tech Stack:** Home Assistant custom integration (Python 3.12), Lit ES module panel, pytest-homeassistant-custom-component.

**Spec:** `docs/superpowers/specs/2026-09-20-cda-alarm-codes-pin-dialog-design.md`

## Global Constraints

- Target HA version: **2025.5.3+**
- Integration version bump: **0.5.1** (0.5.0 already tagged)
- User-facing docs: **English**
- Conventional Commits with scope `cda-alarm` (or `docs`)
- No secrets in committed files
- Out of scope: advanced JSON editor, Frient input changes, Lovelace more-info redesign

## File map

| File | Responsibility |
| --- | --- |
| `packages/cda-alarm/custom_components/cda_alarm/alarm_control_panel.py` | Raise on invalid code |
| `packages/cda-alarm/custom_components/cda_alarm/keypad.py` | Catch invalid-code service errors |
| `packages/cda-alarm/custom_components/cda_alarm/dashboard.py` | Add `code_required` to snapshot |
| `packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js` | Codes rows + PIN dialog |
| `packages/cda-alarm/custom_components/cda_alarm/manifest.json` | Version `0.5.1` |
| `packages/cda-alarm/tests/test_alarm_control_panel.py` | Invalid code raises |
| `packages/cda-alarm/tests/test_dashboard.py` | `code_required` field |
| `packages/cda-alarm/tests/test_frontend_contract.py` | UI contract markers |
| `packages/cda-alarm/tests/test_keypad.py` | Keypad still handles bad code |
| `docs/cda-alarm.md`, `packages/cda-alarm/README.md` | Docs + changelog |

---

### Task 1: Raise on invalid alarm code + keypad resilience

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/alarm_control_panel.py`
- Modify: `packages/cda-alarm/custom_components/cda_alarm/keypad.py`
- Test: `packages/cda-alarm/tests/test_alarm_control_panel.py`
- Test: `packages/cda-alarm/tests/test_keypad.py` (existing bad-code tests must still pass)

**Interfaces:**
- Produces: `async_alarm_disarm` / `_async_arm` raise `HomeAssistantError("Invalid code")` when `_has_credentials` and code does not match
- Consumes: keypad `_async_execute_keypad_action` must not abort feedback when the service raises

- [ ] **Step 1: Write failing tests**

Append to `packages/cda-alarm/tests/test_alarm_control_panel.py`:

```python
from homeassistant.exceptions import HomeAssistantError


@pytest.mark.asyncio
async def test_disarm_without_code_raises_when_codes_configured(
    hass: HomeAssistant,
) -> None:
    entity_id = await _setup_panel(hass)
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id, ATTR_CODE: "1234"},
        blocking=True,
    )
    with pytest.raises(HomeAssistantError, match="Invalid code"):
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_DISARM,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    assert hass.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY


@pytest.mark.asyncio
async def test_disarm_without_code_ok_when_no_codes(hass: HomeAssistant) -> None:
    entity_id = await _setup_panel(hass, codes=[])
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ALARM_DISARMED
```

Update `test_reject_bad_code` to expect `HomeAssistantError` (arm with `"0000"`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_alarm_control_panel.py::test_disarm_without_code_raises_when_codes_configured packages/cda-alarm/tests/test_alarm_control_panel.py::test_reject_bad_code -v'`

Expected: FAIL (no raise yet / state still disarmed silently).

- [ ] **Step 3: Implement raise + keypad catch**

In `alarm_control_panel.py`:

```python
from homeassistant.exceptions import HomeAssistantError

# in async_alarm_disarm:
if not self._is_valid_code(code):
    _LOGGER.warning("Rejected CDA Alarm disarm request with invalid code")
    raise HomeAssistantError("Invalid code")

# in _async_arm after invalid code check (keep arm_failure report, then raise):
if not self._is_valid_code(code):
    _LOGGER.warning("Rejected CDA Alarm arm request with invalid code")
    self._async_report_arm_failure(REASON_INVALID_CODE, target_state)
    raise HomeAssistantError("Invalid code")
```

In `keypad.py` `_async_execute_keypad_action`:

```python
from homeassistant.exceptions import HomeAssistantError

try:
    await hass.services.async_call(ALARM_DOMAIN, service, data, blocking=True)
except HomeAssistantError:
    _LOGGER.debug("Keypad action rejected by panel", exc_info=True)
await hass.async_block_till_done()
panel_state = hass.states.get(panel_entity_id)
await push_status(_panel_status(panel_state.state if panel_state else None))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_alarm_control_panel.py packages/cda-alarm/tests/test_keypad.py -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/cda-alarm/custom_components/cda_alarm/alarm_control_panel.py \
  packages/cda-alarm/custom_components/cda_alarm/keypad.py \
  packages/cda-alarm/tests/test_alarm_control_panel.py
git commit -m "fix(cda-alarm): raise HomeAssistantError on invalid alarm code"
```

---

### Task 2: Dashboard `code_required` flag

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/dashboard.py`
- Test: `packages/cda-alarm/tests/test_dashboard.py`

**Interfaces:**
- Produces: `build_dashboard(...)["code_required"] -> bool`
- Derives from panel entity attributes: `True` when `code_format` is set OR `code_arm_required` is true

- [ ] **Step 1: Write failing test**

```python
async def test_build_dashboard_exposes_code_required(hass: HomeAssistant) -> None:
    # setup entry + panel with codes like other dashboard tests, or set state attrs
    snap = build_dashboard(hass, entry, "alarm_control_panel.cda_alarm")
    assert "code_required" in snap
    assert snap["code_required"] is True  # when codes configured
```

Add a second case with empty codes → `code_required is False`. Follow existing `test_build_dashboard_groups_by_area` setup patterns in the same file.

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_dashboard.py::test_build_dashboard_exposes_code_required -v'`

Expected: FAIL (`code_required` missing)

- [ ] **Step 3: Implement**

In `dashboard.py` `build_dashboard` return dict, add:

```python
code_format = panel_attributes.get("code_format")
code_arm_required = (
    panel_state.attributes.get("code_arm_required")
    if panel_state is not None
    else False
)
code_required = bool(code_format) or bool(code_arm_required)
```

Include `"code_required": code_required` in the returned snapshot. Also add `"code_arm_required"` to `_PANEL_ATTRIBUTE_KEYS` if useful for the dialog inputmode (optional); `code_format` is already included.

- [ ] **Step 4: Run tests**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_dashboard.py -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/cda-alarm/custom_components/cda_alarm/dashboard.py \
  packages/cda-alarm/tests/test_dashboard.py
git commit -m "feat(cda-alarm): expose code_required on dashboard snapshot"
```

---

### Task 3: Structured codes editor in General tab

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js`
- Test: `packages/cda-alarm/tests/test_frontend_contract.py`

**Interfaces:**
- Replaces `_codesJson` string state with `_codes` array of `{name, pin, rfid, nfc_tag_id}`
- Save sends `codes` array (same WS payload key)
- Blank rows (no pin/rfid/nfc_tag_id) are dropped on save

- [ ] **Step 1: Write failing contract tests**

Replace/extend `test_codes_editor_uses_native_textarea` in `test_frontend_contract.py`:

```python
def test_codes_editor_uses_structured_rows() -> None:
    assert 'aria-label="Code name"' in PANEL_SOURCE
    assert 'aria-label="PIN"' in PANEL_SOURCE
    assert 'aria-label="RFID"' in PANEL_SOURCE
    assert 'aria-label="NFC tag id"' in PANEL_SOURCE
    assert "Add code" in PANEL_SOURCE
    assert "Codes (JSON)" not in PANEL_SOURCE
    assert "_codesJson" not in PANEL_SOURCE
```

- [ ] **Step 2: Run to verify fail**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_frontend_contract.py::test_codes_editor_uses_structured_rows -v'`

Expected: FAIL

- [ ] **Step 3: Implement editor**

In `cda-alarm-panel.js`:

1. Replace `_codesJson` property with `_codes: { state: true }` default `[]`.
2. On config load: `this._codes = (this._config.codes || []).map((c) => ({ name: c.name || "", pin: c.pin || "", rfid: c.rfid || "", nfc_tag_id: c.nfc_tag_id || "" }))`.
3. Helpers:

```javascript
_addCodeRow() {
  this._codes = [...this._codes, { name: "", pin: "", rfid: "", nfc_tag_id: "" }];
}
_updateCodeRow(index, patch) {
  this._codes = this._codes.map((row, i) =>
    i === index ? { ...row, ...patch } : row
  );
}
_removeCodeRow(index) {
  this._codes = this._codes.filter((_, i) => i !== index);
}
_codesForSave() {
  return this._codes
    .map((row) => {
      const out = {};
      if (row.name) out.name = String(row.name);
      if (row.pin) out.pin = String(row.pin);
      if (row.rfid) out.rfid = String(row.rfid);
      if (row.nfc_tag_id) out.nfc_tag_id = String(row.nfc_tag_id);
      return out;
    })
    .filter((row) => row.pin || row.rfid || row.nfc_tag_id);
}
```

4. In `_save`, replace JSON.parse path with `codes: this._codesForSave()`.
5. Replace General codes card HTML with rows of four native inputs + Remove + **Add code** button. Title: **Codes**. Help text: optional fields `name`, `pin`, `rfid`, `nfc_tag_id`.

Use `@input` + `_eventValue` (not `.value=` fighting) — property binding `.value=${row.pin}` is OK with `@input` updating state like delays.

- [ ] **Step 4: Run contract tests**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_frontend_contract.py -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js \
  packages/cda-alarm/tests/test_frontend_contract.py
git commit -m "feat(cda-alarm): replace codes JSON with structured editor"
```

---

### Task 4: Dashboard PIN dialog

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js`
- Test: `packages/cda-alarm/tests/test_frontend_contract.py`

**Interfaces:**
- Consumes: `this._dashboard.code_required` (bool), `this._dashboard.attributes.code_format`
- Produces: modal on arm/disarm when `code_required`; calls `_controlAlarm(service, pin)`

- [ ] **Step 1: Write failing contract tests**

```python
def test_dashboard_pin_dialog_markers() -> None:
    assert "_pinDialogOpen" in PANEL_SOURCE
    assert "_pendingService" in PANEL_SOURCE
    assert "Enter PIN" in PANEL_SOURCE
    assert "code_required" in PANEL_SOURCE
```

- [ ] **Step 2: Run to verify fail**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/test_frontend_contract.py::test_dashboard_pin_dialog_markers -v'`

Expected: FAIL

- [ ] **Step 3: Implement dialog**

State:

```javascript
_pinDialogOpen: { state: true },
_pendingService: { state: true },
_dialogPin: { state: true },
```

Constructor defaults: `false`, `null`, `""`.

Flow:

```javascript
_requestAlarm(service) {
  if (this._dashboard?.code_required) {
    this._pendingService = service;
    this._dialogPin = "";
    this._pinDialogOpen = true;
    this._error = "";
    return;
  }
  return this._controlAlarm(service);
}

async _confirmPinDialog() {
  const service = this._pendingService;
  const pin = this._dialogPin;
  this._pinDialogOpen = false;
  this._pendingService = null;
  this._dialogPin = "";
  await this._controlAlarm(service, pin);
}

_cancelPinDialog() {
  this._pinDialogOpen = false;
  this._pendingService = null;
  this._dialogPin = "";
}

async _controlAlarm(service, pin) {
  // use pin argument; do not fall back to always-visible field
  await this.hass.callService("alarm_control_panel", service, {
    entity_id: this._dashboard.panel_entity_id,
    ...(pin ? { code: pin } : {}),
  });
  ...
}
```

Wire arm/disarm buttons to `_requestAlarm(...)`.

Render overlay when `_pinDialogOpen`:

```html
<div class="pin-dialog-backdrop" @click=${this._cancelPinDialog}>
  <div class="pin-dialog card" @click=${(e) => e.stopPropagation()}>
    <h3>Enter PIN</h3>
    <input type="password" inputmode="numeric" autocomplete="off"
      .value=${this._dialogPin}
      @input=${(e) => { this._dialogPin = this._eventValue(e); }}
      @keydown=${(e) => { if (e.key === "Enter") this._confirmPinDialog(); }} />
    <div class="actions">
      <button class="primary" @click=${this._confirmPinDialog}>OK</button>
      <button class="secondary" @click=${this._cancelPinDialog}>Cancel</button>
    </div>
  </div>
</div>
```

Add minimal CSS for backdrop (fixed inset, centered dialog).

Remove the always-visible Dashboard PIN field from `_renderDashboard`.

- [ ] **Step 4: Run contract + package tests**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/ -v'`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/cda-alarm/custom_components/cda_alarm/frontend/cda-alarm-panel.js \
  packages/cda-alarm/tests/test_frontend_contract.py
git commit -m "feat(cda-alarm): prompt for PIN on arm and disarm"
```

---

### Task 5: Docs + version 0.5.1

**Files:**
- Modify: `packages/cda-alarm/custom_components/cda_alarm/manifest.json` → `"version": "0.5.1"`
- Modify: `docs/cda-alarm.md`
- Modify: `packages/cda-alarm/README.md`

- [ ] **Step 1: Update docs**

In `docs/cda-alarm.md`:

- General tab: “structured codes editor” instead of “codes JSON”
- Dashboard: PIN dialog when codes configured
- Rename section **Codes JSON format** → **Codes** (describe form fields; keep key table)
- Changelog `### 0.5.1` with editor + dialog + invalid-code error
- Mention 0.5.0 items already shipped if missing from changelog

Mirror short notes in `packages/cda-alarm/README.md`.

- [ ] **Step 2: Bump manifest to 0.5.1**

- [ ] **Step 3: Run full package tests**

Run: `nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm .venv/bin/python -m pytest packages/cda-alarm/tests/ -v'`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add packages/cda-alarm/custom_components/cda_alarm/manifest.json \
  docs/cda-alarm.md packages/cda-alarm/README.md
git commit -m "docs(cda-alarm): document codes editor and PIN dialog for 0.5.1"
```

---

## Spec coverage checklist

| Spec requirement | Task |
| --- | --- |
| Structured codes editor | 3 |
| PIN dialog when credentials exist | 4 |
| Visible invalid-code failure | 1 + 4 |
| Empty codes → no dialog / free arm-disarm | 1 + 4 |
| Non-admin never gets codes list | unchanged (existing ACL) |
| Docs update | 5 |
| Version bump | 5 (`0.5.1`) |

## Manual verification (after HACS tag)

1. Update integration to 0.5.1, restart HA, hard-refresh browser.
2. General → Add code with PIN `1234` → Save.
3. Confirm entity `code_arm_required=true`.
4. Arm away → dialog → enter `1234`.
5. Disarm without dialog OK → cancel; Disarm with wrong PIN → error, stays armed; Disarm with `1234` → disarmed.
