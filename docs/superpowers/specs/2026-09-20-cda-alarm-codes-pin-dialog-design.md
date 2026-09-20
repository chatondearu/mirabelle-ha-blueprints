# CDA Alarm — codes editor + PIN dialog

**Date:** 2026-09-20  
**Status:** Approved (pending implementation plan)  
**Package:** `packages/cda-alarm`  
**Target version:** `0.5.0` (or next patch after current `0.4.1`)

## Problem

Live HA check (`alarm_control_panel.cda_alarm`):

- `codes: []` in config options
- `code_format: null`, `code_arm_required: false`
- `alarm_arm_*` / `alarm_disarm` succeed **without** a code

That matches backend rules: credentials are only required when at least one stored entry has `pin`, `rfid`, or `nfc_tag_id`.

Users could not easily configure codes because the sidebar only offered a raw **Codes (JSON)** textarea under **General**. The Dashboard PIN field was always visible but optional, with no dialog and silent rejection when a code was required but missing/invalid.

## Goals

1. Make PIN / RFID / NFC configuration obvious and editable without hand-writing JSON.
2. When credentials exist, Dashboard arm/disarm must open a **PIN dialog** before calling the service.
3. Surface invalid/empty code failures in the UI (no silent no-op).
4. Keep existing storage shape and validation (`codes` list in config entry options).

## Non-goals

- No advanced JSON editor alongside the form (may return later).
- No change to Frient keypad / ZHA event code delivery.
- No HA more-info dialog redesign (only the CDA sidebar panel).
- No separate “disarm-only code” policy; arm and disarm both require a valid credential when any are configured (current entity behavior).

## Backend (unchanged rules)

`CdaAlarmControlPanel`:

- `_has_credentials` if any entry has `pin` / `rfid` / `nfc_tag_id`
- `_attr_code_arm_required = _has_credentials`
- `_attr_code_format`: `NUMBER` if any pin, else `TEXT` if only rfid/nfc, else `None`
- `_is_valid_code` allows any service call when `not _has_credentials`; otherwise `match_code(...)`

Optional small improvement (if cheap): when a code is required and missing/invalid, raise / return a service error Home Assistant can show to the client, instead of only logging and returning. Prefer a clear user-visible failure from `callService` when possible without breaking keypad callers.

## Frontend — codes editor (General tab)

Replace the Codes JSON `<textarea>` with a structured list:

| Field | Maps to |
| --- | --- |
| Name | `name` (optional) |
| PIN | `pin` (optional string) |
| RFID | `rfid` (optional string) |
| NFC tag id | `nfc_tag_id` (optional string) |

Actions:

- **Add code** — append an empty row
- **Remove** — delete that row
- **Save** — build `codes` array (omit empty optional fields; drop rows with no pin/rfid/nfc_tag_id and no name, or keep name-only rows only if we already allow them — prefer: keep rows that have at least one of pin/rfid/nfc_tag_id; ignore blank rows)

Native `<input>` controls (same pattern as delays) to avoid Lit/`ha-textfield` binding issues.

Remove the JSON textarea from the default UI for this release.

## Frontend — PIN dialog (Dashboard)

### When to show

If the panel entity (or dashboard snapshot) reports a non-null `code_format` / `code_arm_required === true` (credentials configured):

- Clicking **Arm away / home / night** or **Disarm** opens a modal dialog instead of calling the service immediately.

If no credentials:

- Keep current behavior (direct service call, no dialog).

### Dialog contents

- Title: e.g. “Enter PIN”
- Single password/text input (`inputmode="numeric"` when `code_format` is number)
- **OK** / **Cancel**
- On OK: call `alarm_control_panel` service with `code`
- On failure or unchanged armed state when a code was required: show `_error` message (e.g. “Invalid code”)
- Clear dialog PIN after close

Remove reliance on the always-visible Dashboard PIN field as the primary UX (can remove that field once the dialog exists).

### Dashboard payload

Ensure the frontend can decide without loading admin `get_config` codes:

- Use entity attributes already mirrored in `get_dashboard` (`code_format`), and/or add explicit `code_required: bool` derived from the panel entity’s `code_arm_required` / `code_format`.

Do **not** expose the actual code list to non-admin dashboard users.

## Data flow

```text
Admin: General → Add rows (pin/rfid/nfc) → Save → update_config(codes)
  → panel entity refreshes code_format / code_arm_required

User: Dashboard → Arm/Disarm
  → if code_required → dialog → callService(..., code)
  → else → callService without code
```

## Testing

- Unit / contract: panel source includes structured codes editor markers; no Codes JSON textarea as primary editor.
- Panel API / entity: with codes configured, disarm/arm without code does not change state; with valid pin succeeds.
- Frontend contract or light DOM tests: dialog path gated on `code_format` / `code_required`.
- Manual on live HA: add a PIN via General → Save → confirm `code_arm_required=true` → disarm opens dialog and rejects empty/wrong PIN.

## Docs

Update `docs/cda-alarm.md` and package README: replace “Codes (JSON)” instructions with the structured editor; document the PIN dialog on Dashboard.

## Acceptance

- [ ] Admin can add/edit/remove PIN, RFID, and NFC tag entries without writing JSON
- [ ] With at least one credential saved, Dashboard arm/disarm opens a PIN dialog
- [ ] Wrong/empty PIN does not disarm/arm; user sees an error
- [ ] With empty codes list, arm/disarm still works without a dialog (current live behavior)
- [ ] Non-admin dashboard users never receive the codes list from the API
