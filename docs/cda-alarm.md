# CDA Alarm

Home Assistant custom integration that replaces **Alarmo** with a single
`alarm_control_panel` as the source of truth: unified PIN / RFID / NFC codes,
per-mode sensors, entry and exit delays, and an `open_sensors` attribute for
**[CDA] Alarm Response**.

Frient **KEPZB-110** keypads (ZHA) can bind directly in the integration options
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
6. Open the config entry **Configure** to set sensors, delays, codes, and
   optional Frient binding

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

All settings after the initial name are edited under **Configure** on the CDA
Alarm config entry.

| Option | Description | Default |
| --- | --- | --- |
| Sensors (away) | `binary_sensor` entities monitored in away mode | `[]` |
| Sensors (home) | Sensors monitored in home mode | `[]` |
| Sensors (night) | Sensors monitored in night mode | `[]` |
| Entry delay | Seconds before a tripped sensor triggers the alarm | `30` |
| Exit delay | Seconds after arm before sensors are active | `60` |
| Block arm if open | Refuse arm when a monitored sensor is open | `true` |
| Frient device | ZHA device for KEPZB-110 keypad (optional) | none |
| Enable keypad feedback | Best-effort LED/buzzer sync via ZHA (experimental) | `false` |
| Keypad IAS ACE endpoint | Endpoint for IAS ACE feedback (44 on KEPZB-110) | `44` |
| Codes (JSON) | PIN, RFID, and NFC tag entries (see below) | `[]` |

The panel entity id is derived from the panel name (e.g. `cda_alarm`).

### Frient keypad binding

1. Pair the KEPZB-110 with **ZHA**.
2. In CDA Alarm **Configure**, select the keypad under **Frient device**.
3. Add matching PIN and RFID values in **Codes (JSON)**.
4. Do **not** arm/disarm the Frient ZHA `alarm_control_panel` entity, and do
   **not** run the Frient mirror blueprint while this binding is active.

Prefer this native binding over
**[CDA] Frient Keypad Fallback** (`docs/frient-keypad-with-alarmo.md`).

Keypad arm modes map to CDA services: disarm, arm home, arm night, arm away.

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
| [Alarm Response](alarm-response.md) | Sirens, phone, Telegram, optional speaker/TTS on trigger |
| [NFC Tag → Disarm](nfc-disarm.md) | Disarm on authorized NFC scan |
| [Frient Keypad Fallback](frient-keypad-with-alarmo.md) | Optional if native Frient binding is not used |

## Migration from Alarmo

1. Install/load **CDA Alarm**, create the panel, and copy sensors, delays, and
   codes from Alarmo into the config entry **Configure** options.
2. Point the Frient keypad at CDA (integration **Frient device** or the fallback
   blueprint) and **remove** any Alarmo ↔ Frient ZHA panel mirror automation.
3. Point **[CDA] Alarm Response** and **[CDA] NFC Tag → Disarm** at the CDA panel
   entity (defaults already use `alarm_control_panel.cda_alarm`).
4. Run a full cycle: arm → trip a sensor → verify response (siren / notify) →
   disarm.
5. Disable or remove Alarmo when satisfied.

A parallel run during cutover is fine; avoid two panels both driving sirens or
the same keypad.

## Troubleshooting

| Issue | Things to check |
| --- | --- |
| Cannot arm | **Block arm if open** and open monitored sensors; review logs |
| Arm silently failed | Listen to `cda_alarm_arm_failed` or read the `arm_failure` attribute |
| Keypad does nothing | Correct ZHA device, endpoint `44`, codes JSON matches PIN/RFID |
| Double arm/disarm | Disable fallback blueprint when native Frient binding is set |
| Invalid codes JSON | Only `name`, `pin`, `rfid`, `nfc_tag_id`; must be a JSON array |
| Alarm Response silent | Panel entity in blueprint; panel reaches `triggered`; sirens configured |
| No `open_sensors` on trigger | Sensors assigned to the active mode; entities are `binary_sensor` |

## Changelog

### 0.1.0

- Initial v1: `alarm_control_panel`, unified codes, per-mode sensors, delays,
  hard-block arm when open, Frient ZHA input binding, `open_sensors` attribute.
- State restore across reload/restart with sensor re-evaluation.
- PIN, RFID, and NFC tag ids accepted on the same code field.
- `cda_alarm_arm_failed` event and `arm_failure` attribute.
- Keypad LED feedback derived from the real panel state.
- English and French translations.
