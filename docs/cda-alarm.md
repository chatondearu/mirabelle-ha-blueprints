# CDA Alarm

Home Assistant custom integration that replaces **Alarmo** with a single
`alarm_control_panel` as the source of truth: unified PIN / RFID / NFC codes,
per-mode sensors, entry and exit delays, and an `open_sensors` attribute for
**[CDA] Alarm Response**.

Frient **KEPZB-110** keypads (ZHA) bind in the sidebar **General** tab
(input-only — the Frient ZHA panel entity is never armed or disarmed).

## Prerequisites

- Home Assistant **2025.5.3** or later.
- Binary sensors for doors, windows, and motion as needed.
- Optional: Frient KEPZB-110 on **ZHA** for keypad arm/disarm.
- Optional: **[CDA] Alarm Response**, **[CDA] NFC Tag → Disarm**, and related
  blueprints (defaults target `alarm_control_panel.cda_alarm`).

## Installation

### HACS (recommended)

1. HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/chatondearu/myrabelle-hacs-cda-alarm` as **Integration**
3. Search for **CDA Alarm** → **Download**
4. Restart Home Assistant
5. **Settings → Devices & services → Add integration → CDA Alarm**
6. Open the **CDA Alarm** sidebar panel to use the security Dashboard and
   configure sensors, keypads, delays, codes, cameras, access, and response

The HACS repository is synced from this monorepo (`packages/cda-alarm/`). See
[packages/cda-alarm/HACS_SETUP.md](../packages/cda-alarm/HACS_SETUP.md).

### Manual install

1. Copy the integration folder into your Home Assistant config:

   ```text
   packages/cda-alarm/custom_components/cda_alarm
     → config/custom_components/cda_alarm
   ```

2. Restart Home Assistant, then add **CDA Alarm** as above.

Package overview: [packages/cda-alarm/README.md](../packages/cda-alarm/README.md).

## Configuration

After adding the integration, open the **CDA Alarm** item in the Home Assistant
sidebar. Administrators can configure the integration; other users can open the
Dashboard when allowed by the configured access policy. The options flow under
**Configure** only points you to that panel.

### Sidebar tabs

| Tab | Contents |
| --- | --- |
| **Dashboard** | Live alarm state and controls, sensors grouped by area, and configured cameras |
| **Sensors** | Multi-select entities (any domain) and Away / Home / Night per entity |
| **General** | Entry/exit delays, block-arm-if-open, codes JSON, keypad list with default |
| **Response** | Sirens, noise media players, TTS (owned by the integration) |
| **Cameras** | Camera entities and optional sensor-to-camera mappings |
| **Access** | Dashboard access policy for administrators, everyone, or selected users |
| **Linked** | Automations that reference the panel or known CDA blueprints |

The **Dashboard** is the default tab. It shows arm/disarm controls, the current
alarm state, and monitored sensors grouped by their Home Assistant area.
Entities without an area appear under **Unassigned**. States update live while
the panel is open. If codes are configured, enter a valid PIN before using an
arm or disarm control.

### Cameras

In the administrator-only **Cameras** tab, select the `camera` entities to show
on the Dashboard. You can optionally map each monitored sensor to one of those
cameras. When the alarm is triggered, the Dashboard highlights the camera
mapped to the first open triggering sensor. Missing or unavailable cameras are
shown as unavailable; CDA Alarm does not provide video recording or an NVR
proxy.

### Dashboard access

Administrators configure access in the **Access** tab:

| Mode | Dashboard access |
| --- | --- |
| **Administrators only** | Administrators only (default) |
| **Everyone** | Every authenticated Home Assistant user |
| **Selected users** | Administrators and the selected Home Assistant users |

The policy covers Dashboard viewing and its standard arm/disarm controls.
Configuration tabs and configuration updates always remain administrator-only.
Authorized non-administrators do not receive alarm codes or other
administrator-only configuration through the panel API.

| Setting | Description | Default |
| --- | --- | --- |
| Sensors | Entities monitored by the alarm (any domain) | `[]` |
| Sensor modes | Away / Home / Night checkboxes per sensor | all modes |
| Entry delay | Seconds before a tripped sensor triggers the alarm | `30` |
| Exit delay | Seconds after arm before sensors are active | `60` |
| Block arm if open | Refuse arm when a monitored sensor is open | `true` |
| Keypads | List of ZHA devices; mark one as **default** | discovered KEPZB-110 if empty |
| Keypad feedback | Best-effort LED/buzzer sync via ZHA (per keypad) | `false` |
| Keypad endpoint | IAS ACE endpoint (44 on KEPZB-110) | `44` |
| Codes (JSON) | PIN, RFID, and NFC tag entries (see below) | `[]` |
| Response | Sirens, media noise, optional TTS when `triggered` | empty |

The panel entity id is derived from the panel name (e.g. `cda_alarm`).

### Frient keypad binding

1. Pair the KEPZB-110 with **ZHA**.
2. In the sidebar **General** tab, add the keypad and mark it as **default**.
3. If no keypad is selected, the integration uses the first discovered Frient
   KEPZB-110 (or similar) on ZHA.
4. Add matching PIN and RFID values in **Codes (JSON)**.
5. Do **not** arm/disarm the Frient ZHA `alarm_control_panel` entity, and do
   **not** run the Frient mirror blueprint while this binding is active.

Prefer this native binding over
**[CDA] Frient Keypad Fallback** (`docs/frient-keypad-with-alarmo.md`).

Keypad arm modes map to CDA services: disarm, arm home, arm night, arm away.

### Alarm response (integration)

When the panel enters `triggered`, CDA Alarm runs **Response** actions in order:
sirens → media noise → optional TTS. Actions stop when the panel leaves
`triggered` (including disarm).

Phone and Telegram notifications stay on **[CDA] Alarm Response** for now (see
the **Linked** tab). After upgrading to **0.3.0**, clear sirens / noise inputs
on that blueprint if you configure the sidebar **Response** tab, to avoid
double sound.

### Codes JSON format

Enter a JSON **array** of objects. Each object may include:

| Key | Description |
| --- | --- |
| `name` | Optional label for your reference |
| `pin` | Numeric PIN string for keypad or UI disarm |
| `rfid` | RFID badge id from ZHA events |
| `nfc_tag_id` | NFC tag id (Companion / automations) |

Only these keys are allowed. Values must be strings (or omitted).

Example:

```json
[
  {
    "name": "Main user",
    "pin": "1234",
    "rfid": "00:11:22:33",
    "nfc_tag_id": "abc-def-tag-id"
  },
  {
    "name": "Guest PIN",
    "pin": "5678"
  }
]
```

A code supplied to `alarm_arm_*` / `alarm_disarm` (or sent by the keypad) is
matched against `pin`, then `rfid`, then `nfc_tag_id`. A badge that a keypad
reports in its code field therefore works without a PIN entry.

If no entry defines a `pin`, an `rfid`, or an `nfc_tag_id`, the panel does not
require a code for disarm/arm via services (keypad still sends codes when
configured).

Store real codes only in Home Assistant (config entry options), never in git.

### `open_sensors`

When the alarm triggers, the panel exposes attribute `open_sensors`: a map of
entity id → friendly name for monitored sensors that were open. **[CDA] Alarm
Response** uses this for camera mapping and notifications.

### Arm failures

Arming can be refused because the code is invalid or because a monitored sensor
is open — including at the *end* of the exit delay, where the service call has
already returned successfully. Both are reported:

- Event `cda_alarm_arm_failed` on the Home Assistant bus, with data
  `entity_id`, `reason` (`invalid_code` or `open_sensors`), `mode` (the
  requested state, e.g. `armed_away`), and `open_sensors`.
- Attribute `arm_failure` on the panel holding the same payload. It is cleared
  on the next successful arm and on disarm.

Example automation trigger:

```yaml
triggers:
  - trigger: event
    event_type: cda_alarm_arm_failed
    event_data:
      reason: open_sensors
```

### State restore

The panel inherits `RestoreEntity`: `arming`, `armed_home`, `armed_night`,
`armed_away`, `pending`, and `triggered` survive an integration reload or a
Home Assistant restart. After restoring, monitored sensors are re-evaluated, so
a door opened while Home Assistant was down still starts the entry delay.

## Related blueprints

| Blueprint | Role |
| --- | --- |
| [Alarm Response](alarm-response.md) | Phone / Telegram (and legacy sirens if Response tab unused) |
| [NFC Tag → Disarm](nfc-disarm.md) | Disarm on authorized NFC scan |
| [Frient Keypad Fallback](frient-keypad-with-alarmo.md) | Optional if native Frient binding is not used |

## Migration from Alarmo

1. Install/load **CDA Alarm**, create the panel, and copy sensors, delays, and
   codes into the **CDA Alarm** sidebar panel.
2. Point the Frient keypad at CDA (sidebar **General** keypads or the fallback
   blueprint) and **remove** any Alarmo ↔ Frient ZHA panel mirror automation.
3. Point **[CDA] Alarm Response** and **[CDA] NFC Tag → Disarm** at the CDA panel
   entity (defaults already use `alarm_control_panel.cda_alarm`).
4. Configure sirens/media in the sidebar **Response** tab (or leave them on
   Alarm Response — not both).
5. Run a full cycle: arm → trip a sensor → verify response (siren / notify) →
   disarm.
6. Disable or remove Alarmo when satisfied.

A parallel run during cutover is fine; avoid two panels both driving sirens or
the same keypad.

## Upgrading to 0.4.0

After installing 0.4.0, restart Home Assistant and refresh the browser so the
new sidebar frontend is loaded. Existing alarm settings remain valid. Camera
selection and sensor mappings start empty, and Dashboard access defaults to
administrators only until changed in the new **Access** tab.

## Troubleshooting

| Issue | Things to check |
| --- | --- |
| Cannot arm | **Block arm if open** and open monitored sensors; review logs |
| Arm silently failed | Listen to `cda_alarm_arm_failed` or read the `arm_failure` attribute |
| Keypad does nothing | Correct ZHA device, endpoint `44`, codes JSON matches PIN/RFID; default keypad |
| Double arm/disarm | Disable fallback blueprint when native Frient binding is set |
| Invalid codes JSON | Only `name`, `pin`, `rfid`, `nfc_tag_id`; must be a JSON array |
| Double sirens / noise | Clear blueprint sirens if Response tab is configured |
| Alarm Response silent | Panel entity in blueprint; panel reaches `triggered`; notify targets set |
| No sidebar panel | Restart after install; refresh the browser; verify the CDA Alarm integration is loaded and the custom panel is registered |
| No `open_sensors` on trigger | Sensors assigned to the active mode; entities report open/`on` |

## Changelog

### 0.4.0

- Added a live security Dashboard as the default sidebar tab, with alarm
  controls and sensors grouped by Home Assistant area.
- Added camera selection and optional sensor-to-camera mapping, including
  triggered-camera highlighting.
- Added Dashboard access modes for administrators, everyone, or selected users;
  configuration remains administrator-only.
- Updated panel forms to native Home Assistant controls and light DOM rendering.

### 0.3.0

- Dedicated **CDA Alarm** sidebar panel (Sensors, General, Response, Linked).
- Websocket API for get/update config and listing linked automations.
- Multi-keypad list with **default** resolution (falls back to discovered KEPZB).
- Integration-owned response runner (sirens, media noise, TTS) on `triggered`.
- Options flow reduced to a redirect toward the sidebar panel.

### 0.2.0

- Per-entity Away / Home / Night sensor assignments in options.
- Improved Frient keypad options and feedback.

### 0.1.0

- Initial v1: `alarm_control_panel`, unified codes, per-mode sensors, delays,
  hard-block arm when open, Frient ZHA input binding, `open_sensors` attribute.
- State restore across reload/restart with sensor re-evaluation.
- PIN, RFID, and NFC tag ids accepted on the same code field.
- `cda_alarm_arm_failed` event and `arm_failure` attribute.
- Keypad LED feedback derived from the real panel state.
- English and French translations.
