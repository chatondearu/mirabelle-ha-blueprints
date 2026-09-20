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

HACS distribution is planned; for v1 install from this monorepo:

1. Copy the integration folder into your Home Assistant config:

   ```text
   packages/cda-alarm/custom_components/cda_alarm
     → config/custom_components/cda_alarm
   ```

2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **CDA Alarm** and create a panel (name only on first step).
5. Open the config entry **Configure** to set sensors, delays, codes, and
   optional Frient binding.

Package overview: [packages/cda-alarm/README.md](../packages/cda-alarm/README.md).

## Configuration

All settings after the initial name are edited under **Configure** on the CDA
Alarm config entry.

| Option | Description | Default |
| --- | --- | --- |
| Sensors (away) | `binary_sensor` entities monitored in away mode | `[]` |
| Sensors (home) | Sensors monitored in home mode | `[]` |
| Sensors (night) | Sensors monitored in night mode | `[]` |
| Entry delay | Seconds before a tripped sensor triggers the alarm | `0` |
| Exit delay | Seconds after arm before sensors are active | `0` |
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

If no entry defines a `pin`, the panel does not require a code for disarm/arm
via services (keypad still sends codes when configured).

Store real codes only in Home Assistant (config entry options), never in git.

### `open_sensors`

When the alarm triggers, the panel exposes attribute `open_sensors`: a map of
entity id → friendly name for monitored sensors that were open. **[CDA] Alarm
Response** uses this for camera mapping and notifications.

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
| Keypad does nothing | Correct ZHA device, endpoint `44`, codes JSON matches PIN/RFID |
| Double arm/disarm | Disable fallback blueprint when native Frient binding is set |
| Invalid codes JSON | Only `name`, `pin`, `rfid`, `nfc_tag_id`; must be a JSON array |
| Alarm Response silent | Panel entity in blueprint; panel reaches `triggered`; sirens configured |
| No `open_sensors` on trigger | Sensors assigned to the active mode; entities are `binary_sensor` |

## Changelog

### 0.1.0

- Initial v1: `alarm_control_panel`, unified codes, per-mode sensors, delays,
  hard-block arm when open, Frient ZHA input binding, `open_sensors` attribute.
