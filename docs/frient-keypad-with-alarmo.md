# [CDA] 🔢 Frient Keypad Fallback for Alarm Panels

Forward commands from a **Frient KEPZB-110** Zigbee keypad (integrated via
**ZHA**) to **CDA Alarm** or another `alarm_control_panel`.

> **Prefer the CDA Alarm integration binding.** Configure `frient_device_id`
> in the CDA Alarm options to let the integration own the keypad. Use this
> blueprint only as a fallback when that binding is not configured. Never use
> both for the same keypad, because each command would be processed twice.

> Originally based on a community blueprint by **Darktoinon** (Home Assistant
> forum), now adapted and maintained in this repository under the `[CDA]`
> naming convention.

## How it works

```
Frient keypad ──(zha_event)──▶ CDA Alarm or another target panel
                                      └──(optional)──▶ Frient keypad LEDs
```

- The keypad **only forwards** its arm mode and code; the target panel validates
  the PIN or RFID badge.
- The blueprint **never arms or disarms the Frient ZHA alarm panel**.
- Optionally, the keypad **LEDs/buzzer** are updated (best-effort, experimental).

## Prerequisites

- Home Assistant **2025.5.3** or later.
- A **Frient KEPZB-110** keypad paired through **ZHA** (Zigbee2MQTT is not
  supported by this blueprint).
- **CDA Alarm** or another `alarm_control_panel` configured with your PIN codes
  and RFID badges.
- The native CDA Alarm Frient binding must be left unconfigured when this
  fallback blueprint is active.

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
| Target Alarm Panel | Single source of truth | `alarm_control_panel.cda_alarm` |
| Default Code for Target Alarm | Fallback code when the keypad sends none | `""` |
| Enable Keypad LED/Buzzer Feedback | Push status back to the keypad (experimental) | `false` |
| Keypad IAS ACE Endpoint | Zigbee endpoint of the IAS ACE cluster (44 on the KEPZB-110) | `44` |

## Migrating from Alarmo or the former mirror blueprint

1. Install and configure CDA Alarm.
2. Move PIN and RFID entries to **Settings → Devices & services → CDA Alarm →
   Configure**. Codes now live in the CDA Alarm options.
3. Prefer configuring the Frient device there, then remove the automation
   created from this blueprint.
4. If the native binding cannot be used, keep `frient_device_id` unconfigured,
   use this fallback blueprint, and select `alarm_control_panel.cda_alarm` as
   the target.
5. Do not target or synchronize the Frient ZHA `alarm_control_panel` entity.

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
| Command runs twice | Disable this blueprint or clear `frient_device_id`; only one keypad owner may be active. |
| Code rejected | For CDA Alarm, verify that the code exists in the integration options. |
| Frient ZHA panel does not change | Expected: this blueprint intentionally never synchronizes that entity. |
| LEDs wrong / no feedback | Expected ZHA limitation; verify the IAS ACE endpoint, or disable the feedback option and rely on the HA app / dashboard. |

## Changelog

- **CDA Alarm retarget**: CDA Alarm is now the default target, the Frient ZHA
  panel mirror was removed, and the blueprint is documented as a fallback to
  the native CDA Alarm Frient binding.
- **Adapted version**: hardened `zha_event` parsing and added optional
  best-effort keypad LED/buzzer feedback.
