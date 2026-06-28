# [CDA] 🏷️ NFC Tag → Disarm Alarm

Disarm an alarm panel (e.g. **Alarmo**) when an **authorized NFC tag** is
scanned with the Home Assistant Companion app (or a fixed NFC reader). It lets
you give **each person their own tag** without configuring multiple keypad
codes — useful when the physical keypad (e.g. Frient via ZHA) only supports a
single code.

## Why use this

- A keypad bridged through ZHA typically supports only **one** code. NFC tags
  add **per-person** disarm without touching the keypad code.
- The automation supplies the disarm code itself, so the tag works as a
  physical **key**.
- Fully decoupled from the keypad: it keeps working even if the keypad is
  offline or out of sync.

> **Security:** a lost tag can disarm the alarm. Revoke it by removing its ID
> from the authorized list.

## Prerequisites

- Home Assistant **2025.5.3** or later, with the **Companion app** (for scanning
  NFC tags) or a fixed NFC reader that registers HA tags.
- An alarm panel that supports `alarm_control_panel.alarm_disarm` (Alarmo
  recommended).
- One or more **NFC tags** registered in HA (see below).

## Step 1 — Register your NFC tag

1. Open the **Companion app** → **Settings → Companion app → Tags** (or
   **Settings → Tags** in the HA sidebar).
2. **Scan/write** your physical NFC tag (NTAG21x stickers work well). The tag is
   added to HA with a unique **tag ID**.
3. Note the **tag ID** (Settings → Tags → the tag → its ID). Repeat for each
   person's tag.

## Step 2 — Install the blueprint

[Import this blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Fnfc-disarm.yaml)

Or import manually with this URL:

```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/nfc-disarm.yaml
```

## Configuration

| Parameter | Description | Default |
| --- | --- | --- |
| Alarm Panel | Panel to disarm | `alarm_control_panel.alarmo` |
| Authorized NFC Tag IDs | Registered tag IDs allowed to disarm, comma-separated | `""` |
| Disarm Code | Code sent when disarming (leave empty if none) | `""` |
| Notify Service(s) | Optional notify service(s), comma-separated, for a disarm confirmation | `""` |

## How it works

The automation listens to the `tag_scanned` event, checks the scanned
`tag_id` against the **authorized list**, and calls
`alarm_control_panel.alarm_disarm` (with the configured code). Any unlisted tag
is ignored.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Nothing happens on scan | Confirm the tag is **registered** (Settings → Tags) and its ID is in the authorized list (exact match). |
| Disarm rejected | The disarm code must be valid for the panel (e.g. a real Alarmo user code). |
| No confirmation notification | Verify the exact `notify.*` service name; the disarm still happens regardless. |

## Changelog

- Initial version: disarm an alarm panel from one or more authorized NFC tags,
  with an optional disarm confirmation notification.
