# `/scan` endpoint — field reference

This document describes JSON fields observed in the `val[]` array returned by **`GET /scan?scan_time=&single=true`** on Imeon OS One (example firmware **1.8.1.4**, **single-phase**: `*_s` / `*_t` fields are often `null`).

Interpretations below are **engineering inference** from naming and typical hybrid inverter semantics. **Official Imeon documentation overrides** this file if anything disagrees.

---

## Record metadata

| Field | Probable meaning |
|--------|------------------|
| `time` | Human-readable local timestamp (`YYYY/MM/DD HH:MM:SS`). |
| `timestamp` | Unix epoch for the sample. |

---

## AC output (backup / loads side, depending on mode)

| Field | Probable meaning |
|--------|------------------|
| `ac_output_voltage` | AC output voltage on the primary path (V). |
| `ac_output_voltage_s`, `ac_output_voltage_t` | Phase S/T voltages — often `null` on single-phase. |
| `ac_output_frequency` | Output frequency (Hz). |
| `ac_output_current` | Output current on the primary path (A). |
| `ac_output_current_s`, `ac_output_current_t` | Phase S/T currents — often `null` on single-phase. |
| `ac_output_power_r` | Active output power on phase **R** (W). |
| `ac_output_active_power_s`, `ac_output_active_power_t` | Active output power phases S/T — often `null` on single-phase. |
| `ac_output_total_active_power` | Sum / total active **output** power (W). |
| `ac_output_apperent_power_r` | **Apparent** output power phase R (VA). API typo: *apperent*. |
| `ac_output_apperent_power_s`, `ac_output_apperent_power_t` | Apparent power S/T — often `null` on single-phase. |
| `ac_output_total_apperent_power` | Total apparent output power (VA). |
| `output_load_percent` | Relative load / usage on output (%), often low when backup load is minimal. |

---

## AC input / grid

| Field | Probable meaning |
|--------|------------------|
| `ac_input_total_active_power` | Total **active power at AC input** (grid / inverter input side) (W). On observed single-phase units this has matched `grid_power_r`. |
| `ac_input_active_power_s`, `ac_input_active_power_t` | AC input active power phases S/T — typically `null` on single-phase. |
| `grid_voltage_r`, `grid_voltage_s`, `grid_voltage_t` | Grid voltage per phase (V). |
| `grid_current_r`, `grid_current_s`, `grid_current_t` | Grid current per phase (A). |
| `grid_frequency` | Grid frequency (Hz). |
| `grid_power_r` | Active power tied to **grid phase R** / AC input leg (W). **Not** a dedicated battery power field; do not treat it as battery DC power. |

---

## External energy meter (“EM”, e.g. Linky)

| Field | Probable meaning |
|--------|------------------|
| `em_power` | Instantaneous power from the **external meter** path (net or measured at PCC) (W). May **differ** from `grid_power_r` / `ac_input_*` depending on wiring and what the inverter exposes. |
| `em_power_from_protocol` | Alternative or raw protocol value — often `null` when unused. |
| `em_status` | Meter state / validity (vendor-specific code). |

---

## Battery

| Field | Probable meaning |
|--------|------------------|
| `battery_soc` | State of charge (%). |
| `battery_power` | **Instantaneous battery power** (W) when the firmware provides it — may be `null`; then derive from current × voltage or another official API if needed. |
| `battery_current` | Battery current (A); sign usually indicates charge vs discharge per vendor convention. |
| `p_battery_voltage` | Measured battery / pack voltage (V). |
| `external_battery_temperature` | External battery temperature if a probe exists (unit per vendor documentation). |

---

## PV / solar

| Field | Probable meaning |
|--------|------------------|
| `pv_input_power1`, `pv_input_power2`, `pv_input_power3` | DC power per MPPT input (W). |
| `pv_input_voltage1`, `pv_input_voltage2`, `pv_input_voltage3` | DC voltage per MPPT input (V). |
| `solar_input_current1`, `solar_input_current2`, `solar_input_current3` | Solar input current per string (A). |

---

## Internal DC / inverter

| Field | Probable meaning |
|--------|------------------|
| `p_bus_voltage` | Internal DC bus voltage when exposed (V). |
| `inverter_power` | Internal aggregate inverter metric — often `null` if not exposed. |

---

## Temperatures and miscellaneous

| Field | Probable meaning |
|--------|------------------|
| `inner_temperature` | Internal device temperature. |
| `max_temperature_detecting_pointers` | Thermal tracking / peak sensor index (vendor-specific). |
| `retrofit_value` | Retrofit / extension configuration value — depends on installation. |

---

## Practical notes for integrations

- Prefer **`battery_power`** from `scan` for instantaneous battery power when it is a **non-null number**.
- If **`battery_power`** is `null`, a common fallback is **`battery_current` × `p_battery_voltage`** (verify **sign convention** against real charge/discharge conditions on your unit).
- **Do not** map **`grid_power_r`** to battery: it aligns with **grid / AC input** quantities (and on sample data has matched `ac_input_total_active_power` on single-phase installs).
- **Use `em_power`** for the **meter** path, not for battery-only power.
- On **three-phase** systems, expect **`_s` / `_t`** fields to be populated in addition to **`_r`**.
