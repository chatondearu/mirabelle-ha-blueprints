# CDA Alarm

Home Assistant custom integration: a single `alarm_control_panel` source of
truth with unified PIN / RFID / NFC codes, per-mode sensors, entry/exit delays,
Frient KEPZB-110 (ZHA) keypad binding (input-only), and an `open_sensors`
attribute for Mirabelle **[CDA] Alarm Response** blueprints.

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
6. Open the config entry **Configure** for sensors, delays, codes, and optional
   Frient binding

## Manual install

Copy `custom_components/cda_alarm` into your HA
`config/custom_components/cda_alarm`, restart, then add the integration as above.

## Requirements

- Home Assistant **2025.5.3** or later
- Optional: Frient KEPZB-110 on **ZHA**
- Optional: Mirabelle blueprints that target `alarm_control_panel.cda_alarm`

## Features

- Standard `alarm_control_panel` services (`arm_home` / `away` / `night`, disarm)
- Unified codes (PIN, RFID, NFC) in options
- Hard-block arm when sensors are open (configurable)
- Entry / exit delays with `cda_alarm_arm_failed` event on failed arm
- Frient keypad as **input only** (no ZHA panel mirror)
- Optional best-effort keypad LED feedback via IAS ACE
- State restore across reload / restart
- English and French UI strings

## Documentation

Full guide (migration from Alarmo, troubleshooting, codes JSON):

- In the monorepo: [`docs/cda-alarm.md`](https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/docs/cda-alarm.md)
- HACS sync notes: [HACS_SETUP.md](./HACS_SETUP.md)

## Releases

Monorepo tags `cda-alarm-vX.Y.Z` publish GitHub releases on this HACS repository
as `vX.Y.Z`.

## License

See the monorepo [LICENSE](https://github.com/chatondearu/mirabelle-ha-blueprints/blob/main/LICENSE).
