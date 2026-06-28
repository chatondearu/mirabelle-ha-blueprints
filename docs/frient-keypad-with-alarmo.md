# Keypad Frient (KEPZB-110) for Alarmo

Bridge a **Frient KEPZB-110** Zigbee keypad (integrated via **ZHA**) with an
**Alarmo** central — or any other `alarm_control_panel` — used as the single
source of truth.

> Originally based on a community blueprint by **Darktoinon** (Home Assistant
> forum), now adapted and maintained in this repository under the `[CDA]`
> naming convention.

## How it works

```
Frient keypad ──(zha_event)──▶ Alarmo (source of truth) ──(state change)──▶ Frient alarm panel
                                                          └──(optional)────▶ Frient keypad LEDs
```

- The keypad **only forwards** the typed code; **Alarmo validates** the PIN /
  RFID badge. Manage all your codes in Alarmo.
- When Alarmo changes state, the **Frient alarm panel** is synchronized.
- Optionally, the keypad **LEDs/buzzer** are updated (best-effort, experimental).

## Prerequisites

- Home Assistant **2025.5.3** or later.
- A **Frient KEPZB-110** keypad paired through **ZHA** (Zigbee2MQTT is not
  supported by this blueprint).
- An **Alarmo** instance (or another `alarm_control_panel`) configured with your
  PIN codes / RFID badges.

## Installation

[Import this blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Ffrient_keypad_with_alarmo.yaml)

Or import manually with this URL:

```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/frient_keypad_with_alarmo.yaml
```

## Configuration

| Parameter | Description | Default |
| --- | --- | --- |
| Frient Keypad | The KEPZB-110 ZHA device | - |
| Frient Alarm Panel | The ZHA `alarm_control_panel` to control | - |
| Alarm Panel to Mirror | Source of truth (Alarmo) | `alarm_control_panel.alarmo` |
| Frient Panel Disarm Code | Code sent to the Frient panel (leave empty if none) | `""` |
| Default Code for Mirrored Alarm | Fallback code for Alarmo when the keypad sends none | `""` |
| Enable Keypad LED/Buzzer Feedback | Push status back to the keypad (experimental) | `false` |
| Keypad IAS ACE Endpoint | Zigbee endpoint of the IAS ACE cluster | `1` |

### Finding the IAS ACE endpoint

The keypad feedback option sends a raw IAS ACE command to a specific Zigbee
endpoint. To find it:

1. Go to **Settings → Devices & Services → Devices** and open your keypad.
2. Open **ZHA device info → Manage Zigbee device → Clusters**.
3. Locate the **IAS_ACE** cluster (`0x0501`) and note its endpoint (usually `1`).

## Keypad LED/buzzer feedback (experimental)

This feature is **disabled by default** and is **best-effort**. ZHA does not yet
fully implement the IAS ACE "central" (Control and Indicating Equipment) role,
so LED states, beeping patterns and exit/entry countdowns may not be accurate.

- Tracking issue (LED state bug):
  <https://github.com/zigpy/zha-device-handlers/issues/4365>
- Native exit/entry delay support is being added upstream in ZHA
  (<https://github.com/zigpy/zha/pull/664>). Once released, the keypad should
  expose a proper native `alarm_control_panel` with reliable timer handling,
  which is the recommended long-term path.

The command call uses `continue_on_error`, so a Zigbee failure never blocks
arming or disarming.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Keypad does nothing | Confirm the `zha_event` fires (Developer Tools → Events, listen to `zha_event`) and that the correct keypad device is selected. |
| Code rejected | The code must exist in **Alarmo**, not in this blueprint. |
| Frient panel not syncing | Verify the *Alarm Panel to Mirror* entity and the *Frient Panel Disarm Code*. |
| LEDs wrong / no feedback | Expected ZHA limitation; verify the IAS ACE endpoint, or disable the feedback option and rely on the HA app / dashboard. |

## Changelog

- **Adapted version**: Alarmo set as single source of truth (PIN/RFID handled by
  Alarmo), removed unused PIN/RFID inputs, hardened `zha_event` parsing, added a
  redundancy guard on the panel sync, and added optional (opt-in) best-effort
  keypad LED/buzzer feedback.
