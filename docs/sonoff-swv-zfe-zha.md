# Sonoff SWV-ZFE (Hydro ONE / DO1BSP) on ZHA

## Problem

Home Assistant ZHA pairs the **SONOFF SWV-ZFE** but only exposes:

- `switch.*` (valve on/off)
- battery / identify / firmware update entities

Missing water volume, duration, leak/shortage sensors, and timer controls live on the manufacturer cluster **`0xFC11`**. Upstream quirks for this model are still open PRs, so stock ZHA does not apply a handler (`quirk_applied: false`).

Commands to a sleeping end device often **time out** until the device checks in (or you wake it with the physical button) and bindings/reporting are reconfigured.

## Recommended fix: custom ZHA quirk

Use the Flow-edition quirk from [zha-device-handlers PR #4927](https://github.com/zigpy/zha-device-handlers/pull/4927) (vendored in this repo).

### 1. Copy the quirk into Home Assistant

Create `/config/zha_quirks/` (name is arbitrary) and copy **only**:

[`contrib/zha_quirks/sonoff_swv_zfe.py`](../contrib/zha_quirks/sonoff_swv_zfe.py)

Do **not** also install `alternatives/sonoff_swv1c_swv2c_official.py` at the same time — both register `SWV-ZFE`.

You can use **Studio Code Server**, **File editor**, or **Terminal & SSH** on Home Assistant OS.

### 2. Point ZHA at the folder

In `configuration.yaml`:

```yaml
zha:
  enable_quirks: true
  custom_quirks_path: /config/zha_quirks/
  zigpy_config:
    ota:
      extra_providers:
        - type: z2m
```

The `z2m` OTA provider helps fetch Sonoff firmware updates (device firmware shows as `0x00001007` / “unknown” until OTA metadata is available).

### 3. Restart Home Assistant

Restart Core after saving the YAML and quirk file.

### 4. Wake the valve, then reconfigure

1. Press the physical button on the SWV-ZFE so it stays awake briefly.
2. Open the ZHA device page → **Reconfigure device** (or remove and re-pair if reconfigure fails).
3. Confirm diagnostics / device info shows a quirk applied (not plain `zigpy.device.Device`).

### 5. After quirk: useful entities

Expect entities such as:

| Entity (examples) | Purpose |
| ----------------- | ------- |
| Switch (OnOff) | Open / close valve |
| On time / Off wait time | Timed on (device uses seconds; quirk converts ZCL deciseconds) |
| Real-time irrigation duration / volume | Current run stats |
| Daily / hourly duration & volume | Usage counters |
| Water shortage / leakage / fail safe | Alarms (firmware 1.0.7 may not report abnormal state reliably — see Zigbee2MQTT notes) |
| Child lock | Disable physical button |

**Important:** default fail-safe / timed behaviour can close the valve after ~10 minutes. Raise **On time** (or equivalent fail-safe settings) before long irrigation runs.

## Connectivity checklist (remote watering)

The valve is a **battery end device**. ZHA must queue On/Off until the next poll.

- Place a **Zigbee router** closer to the garden if RSSI is weak (around −75 dBm is marginal).
- Before testing toggle: press the device button, then immediately turn the switch on in HA.
- For holidays, prefer automations that retry On for a few minutes, or schedules that run when the device is known to check in.

## Alternative quirk

[`contrib/zha_quirks/alternatives/sonoff_swv1c_swv2c_official.py`](../contrib/zha_quirks/alternatives/sonoff_swv1c_swv2c_official.py) mirrors Sonoff’s simpler SWV1C/SWV2C mapping (volume `0x501B`, duration `0x501C`, leak/shortage bits). Use only if the Flow quirk fails to load on your HA/zigpy version.

## References

- Device (Zigbee2MQTT): https://www.zigbee2mqtt.io/devices/SWV-ZFE.html
- Sonoff help (Hydro ONE): https://help.sonoff.tech/docs/SWVZFU-SWVZFE
- Quirk PR (recommended): https://github.com/zigpy/zha-device-handlers/pull/4927
- Quirk PR (official Sonoff family): https://github.com/zigpy/zha-device-handlers/pull/4993
- Community thread: https://community.home-assistant.io/t/sonoff-hydro-one-zigbee-ble/998682
- Garden irrigation blueprints: [garden-irrigation.md](garden-irrigation.md)

## Verified on this project’s HA instance

| Field | Value |
| ----- | ----- |
| Model | `SWV-ZFE` |
| Manufacturer | `SONOFF` |
| IEEE | `a4:c1:38:15:6d:60:ff:ff` |
| Firmware | `0x00001007` |
| Area | Jardin |
| Quirk applied (before fix) | `false` |
| Input clusters | `0x0000`, `0x0001`, `0x0003`, `0x0006`, `0x0020`, `0xFC11`, `0xFC57` |
