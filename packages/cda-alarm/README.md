# CDA Alarm

Home Assistant custom integration: a single `alarm_control_panel` source of
truth with unified PIN / RFID / NFC codes, per-mode sensors, entry/exit delays,
Frient KEPZB-110 (ZHA) keypad binding (input-only), integration-owned siren /
media / TTS response, and an `open_sensors` attribute for Mirabelle
**[CDA] Alarm Response** notifications.

## HACS installation

This component lives in the
[mirabelle-ha-blueprints](https://github.com/chatondearu/mirabelle-ha-blueprints)
monorepo and is **synced** to a dedicated repository for HACS.

**Use the dedicated repository in HACS:**

- Repository: `https://github.com/chatondearu/myrabelle-hacs-cda-alarm`
- Category: **Integration**

### Steps

1. HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/chatondearu/myrabelle-hacs-cda-alarm` (Integration)
3. Search for **CDA Alarm** → **Download**
4. Restart Home Assistant
5. **Settings → Devices & services → Add integration → CDA Alarm**
6. Open the **CDA Alarm** sidebar panel to use the security Dashboard and
   configure sensors, keypads, delays, codes, cameras, access, and response

## Manual install

Copy `custom_components/cda_alarm` into your HA
`config/custom_components/cda_alarm`, restart, then add the integration as above.

## Requirements

- Home Assistant **2025.5.3** or later
- Optional: Frient KEPZB-110 on **ZHA**
- Optional: Mirabelle blueprints that target `alarm_control_panel.cda_alarm`

## Features

- Live security Dashboard as the default sidebar tab
- Sensors grouped by Home Assistant area, with an **Unassigned** fallback
- Sidebar configuration (Sensors / General / Response / Cameras / Access / Linked)
- Standard `alarm_control_panel` services (`arm_home` / `away` / `night`, disarm)
- Unified codes (PIN, RFID, NFC)
- Hard-block arm when sensors are open (configurable)
- Entry / exit delays with `cda_alarm_arm_failed` event on failed arm
- Multi-keypad list with default discovery fallback
- Optional one-way sync of CDA state onto the Frient ZHA alarm panel
- Sirens / media noise / TTS when the panel is `triggered`
- Dashboard cameras with optional sensor-to-camera mapping and trigger highlighting
- Dashboard access for administrators, everyone, or selected users
- State restore across reload / restart
- English and French UI strings

## Dashboard, cameras, and access

The Dashboard shows the live alarm state, arm/disarm controls, monitored
sensors grouped by Home Assistant area, and configured camera entities.
Administrators select cameras and optionally map monitored sensors to cameras
in the **Cameras** tab. A mapped camera is highlighted when its sensor triggers
the alarm.

The administrator-only **Access** tab controls who can view and operate the
Dashboard: administrators only (default), every authenticated user, or selected
Home Assistant users. Administrators are always allowed. Configuration tabs and
updates remain restricted to administrators, and non-administrators never
receive alarm codes through the panel API. **State notifications** (default on)
send Companion alerts to phones of authorized users on arm, disarm, and triggered.

## Upgrade to 0.5.0

Restart Home Assistant and refresh the browser. Enable **Sync ZHA panel** on
Frient keypads if disarm outside the keypad should clear the ZHA entity.

## Upgrade to 0.4.0

Restart Home Assistant and refresh the browser after upgrading. Existing alarm
settings are preserved. Cameras and mappings initially remain empty, while
Dashboard access defaults to administrators only.

## Documentation

Full guide (migration from Alarmo, troubleshooting, codes JSON):

- In the monorepo: [`docs/cda-alarm.md`](https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/docs/cda-alarm.md)
- HACS sync notes: [HACS_SETUP.md](./HACS_SETUP.md)

## Releases

Monorepo tags `cda-alarm-vX.Y.Z` publish GitHub releases on this HACS repository
as `vX.Y.Z`.

## Changelog

### 0.4.0

- Added the live Dashboard with area-grouped sensors and alarm controls.
- Added camera configuration, sensor mappings, and triggered-camera highlighting.
- Added administrator/everyone/selected-user Dashboard ACL modes.
- Adopted native Home Assistant form controls and light DOM rendering.

## License

See the monorepo [LICENSE](https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/LICENSE).
