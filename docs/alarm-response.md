# [CDA] 🚨 Alarm Response

Reliable, prioritized response when an alarm panel (e.g. **Alarmo**) is
triggered: sound the siren(s), send a **critical actionable phone
notification** with one-tap **Disarm/Silence**, and send a **Telegram alert
with a camera snapshot** of the room where the triggering sensor is located.
An optional best-effort noise layer can also set speaker volume, play a custom
sound, and speak a dedicated alarm message.

Actions run in priority order and use `continue_on_error`, so a camera or
Telegram failure never prevents the siren or the phone notification. Each siren
is triggered **independently**, so a faulty or unavailable siren can never abort
the rest of the response (notifications, Telegram).

## Why this design

- **Siren first**, then the best-effort media layer, phone, Telegram text,
  photo, and theatrical actions. Sirens always start before speakers.
- The phone notification is **actionable**: a single tap on **Disarm** or
  **Silence** stops sirens and custom media — no more hunting for a way to kill
  a looping sound.
- Unavailable or unknown speakers are skipped. Every speaker action uses
  `continue_on_error`, so media or TTS failure does not abort later actions.
- The "theatrical" hooks (light show, TTS) are **disabled by default** so the
  fun layer can be added later without risking the reliable core.

## Prerequisites

- Home Assistant **2025.5.3** or later.
- An alarm panel that exposes a `triggered` state (Alarmo recommended).
- One or more `siren` entities.
- Optional `media_player` entities for custom sound and TTS.
- The Google Translate TTS entity `tts.google_en_com` when alarm or theatrical
  TTS is enabled.
- Home Assistant Companion app for the actionable notification.
- A configured **Telegram bot** integration (`telegram_bot.*` services) for the
  Telegram alert.
- The snapshot folder must be in `allowlist_external_dirs` (e.g. `/config/www`).

## Installation

[Import this blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fchatondearu%2Fmirabelle-ha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomations%2Falarm-response.yaml)

Or import manually with this URL:

```
https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/blueprints/automations/alarm-response.yaml
```

## Configuration

| Parameter | Description | Default |
| --- | --- | --- |
| Alarm Panel | Panel whose `triggered` state starts the response | `alarm_control_panel.cda_alarm` |
| Disarm Code | Code used by the Disarm action (leave empty if none) | `""` |
| Sirens | Siren entities turned on/off (each triggered independently) | `[]` |
| Siren Duration (seconds) | How long each siren sounds; use a long value so it keeps sounding until disarm. `0` = device default (some Zigbee sirens stop after a short built-in warning). Applied only to sirens that support a duration. | `0` |
| Siren Tone | Tone for sirens that support tones (e.g. Frient: `Burglar`, `Fire`, `Emergency`). Empty = device default. | `""` |
| Noise Media Players | Speakers for custom alarm sound; unavailable/unknown players are skipped | `[]` |
| Alarm Sound Content ID | Media source ID or URL played when the alarm triggers | `""` |
| Noise Volume | Volume set before custom alarm sound playback | `0.9` |
| Enable Alarm Voice Message | Speak the dedicated alarm message on available TTS players | `false` |
| Alarm Voice Message | Dedicated text spoken by the alarm noise layer | alarm warning |
| Mobile Notify Service(s) | One or more, comma-separated, e.g. `notify.pixel_7_pro, notify.pixel_6a` | `""` |
| Notification Tag | Tag to update/clear the alert | `cda_alarm_response` |
| Telegram Chat ID | Target chat/group id | `""` |
| Telegram Thread ID | Topic/thread id (optional) | `""` |
| Send Camera Snapshot | Attach a snapshot to Telegram | `true` |
| Snapshot File Path | Where the snapshot is saved | `/config/www/alarm/last_trigger.jpg` |
| Default Camera | Camera used when no mapping matches | `""` |
| Sensor → Camera Mapping | `sensor: camera` map | `{}` |
| Enable Light Show | Theatrical light flashing (opt-in) | `false` |
| Light Show Lights | Lights to flash | - |
| Enable Voice Message | TTS announcement (opt-in) | `false` |
| TTS Media Players | Speakers for the voice message | `[]` |
| Voice Message | Text to speak | warning message |

### Custom sound and alarm TTS

Set **Noise Media Players** and optionally provide an **Alarm Sound Content
ID**, for example:

```text
media-source://media_source/local/alarm.mp3
```

The automation starts sirens first, then processes each available noise player
independently: set **Noise Volume**, play the custom sound when configured, and
continue even if a player rejects an action. Enable **Alarm Voice Message** to
speak **Alarm Voice Message** on the existing **TTS Media Players** list.
Unavailable and unknown TTS players are removed from the announcement target.

When the panel leaves `triggered` for any state, or when **Silence** is tapped,
the automation turns off every configured siren and sends `media_stop` to every
configured noise or TTS media player.

### Sensor → Camera mapping

The triggering sensor is read from the panel's `open_sensors` attribute
(Alarmo). Provide a mapping so the snapshot uses the right camera:

```yaml
binary_sensor.motion_sensor_hue_001_0df96a41_motion: camera.tapo_c220_001
binary_sensor.secure_contact_sensor_sonoff_snzb_04pr2_001: camera.tapo_c220_004
```

If no mapping matches, the **Default Camera** is used.

### Actionable notification

The notification adds two actions: **Disarm** (`CDA_ALARM_DISARM`) disarms the
panel, while **Silence** (`CDA_ALARM_SILENCE`) turns the sirens off and stops
media on all configured noise and TTS players. Both are handled by the same
automation via the `mobile_app_notification_action` event.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No siren | Confirm the `sirens` entities and that the panel really reaches `triggered`. |
| Siren stops after a few seconds | Set **Siren Duration** to a value at least as long as your response time; some Zigbee sirens stop after a short built-in warning when no duration is sent. |
| One siren breaks the response | Each siren now fires independently with `continue_on_error`; remove any entity that errors (e.g. a camera that does not support a siren). |
| No custom alarm sound | Confirm the player is available and the content ID is reachable from Home Assistant; test `media_player.play_media` in Developer Tools. |
| No alarm TTS | Enable Alarm Voice Message, select TTS Media Players, and verify `tts.google_en_com` exists. |
| No phone alert | Verify the exact `notify.*` service name; test it from Developer Tools → Actions. |
| No Telegram photo | Snapshot folder must be in `allowlist_external_dirs`; the text alert is sent regardless. |
| Wrong camera | Add/adjust the sensor → camera mapping; set a default camera. |
| Disarm button does nothing | Ensure the panel disarms without a code, or set the Disarm Code. |

## Changelog

- Add best-effort custom media noise and alarm TTS on available speakers; stop
  media when silenced or when the panel leaves `triggered`. Default the panel
  to `alarm_control_panel.cda_alarm`.
- Migrate Telegram bot actions from deprecated `target` to `chat_id` (required
  before Home Assistant removes `target`, planned for 2026.9).
- Per-siren triggering with `continue_on_error` (a faulty siren no longer aborts
  notifications), plus configurable **Siren Duration** and **Siren Tone** so the
  siren sounds continuously until disarm.
- Initial version: siren, critical actionable phone notification, Telegram text
  + best-effort snapshot, sensor → camera mapping, opt-in light show and TTS.
