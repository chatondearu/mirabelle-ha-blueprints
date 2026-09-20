# Design: CDA Alarm (Alarmo replacement, Frient-native)

**Date:** 2026-09-20  
**Status:** Approved for planning  
**Scope:** New HACS-style package `packages/cda-alarm/`, Frient keypad binding, blueprint retargeting (`alarm-response`, `nfc-disarm`, Frient keypad), phased presence / house-settling / profile orchestration  
**Related:** `docs/frient-keypad-with-alarmo.md`, `docs/alarm-response.md`, `docs/nfc-disarm.md`

## Problem

Today the house alarm runs on **Alarmo** inside Home Assistant, bridged to a **Frient KEPZB-110** via a mirror automation:

```text
Frient keypad → Alarmo (truth) → sync back to Frient ZHA alarm_control_panel (+ optional LEDs)
```

Pain points:

| Pain | Symptom |
|------|---------|
| Heavy UX | Alarmo config (modes, users, sensors) is heavier than needed |
| Tooling friction | Defaults and docs assume Alarmo; `open_sensors` and codes live in Alarmo’s model |
| Dual panel (B) | Two `alarm_control_panel` entities to keep in sync; fragile and confusing |
| Split codes (C) | PIN/RFID validated in Alarmo; Frient panel may need its own disarm code |
| Flaky keypad arm/disarm (D) | Race / desync when the mirror fails or states diverge |

Alarmo’s “independent of HA” story is irrelevant here: it already runs as a HA custom integration. The real question is ownership of a **single source of truth** aligned with Mirabelle tooling.

## Goals

### v1 — Core panel

- One CDA `alarm_control_panel` as the only source of truth
- Unified code store: PIN, RFID, NFC tag IDs
- Frient keypad as **input only** (`zha_event` → arm/disarm); **do not** arm/disarm the Frient ZHA panel entity
- Configurable sensors per mode; simple entry/exit delays
- Expose standard `alarm_control_panel` services plus an `open_sensors` attribute (dict) for existing `alarm-response`
- Package layout like `cover-manager` / `imeon_energy_api` (HACS sync later)

### v1.5 — Leave-home prompt

- When home becomes empty and panel is `disarmed`, send an **actionable notification** “Arm away?”
- Optional auto-arm is **opt-in**, off by default

### v2 — House settling before arm

- Before completing arm: wait for conditions (e.g. all covers closed, no motion for N minutes)
- Timeout + notify if conditions never converge
- Alarm **orchestrates** via CDA scripts/services; it does not reimplement cover-manager or lighting

### v3 — Forced modes (covers / lights)

- Away/night profiles that call existing systems (cover-manager, living-area lighting, etc.)
- Publish something like `arming_profile` so other automations subscribe rather than being hard-overridden

### Noise layer (speakers + TTS) — response side

- When triggered: play custom alarm media + loud TTS on **available** `media_player` entities
- Lives in **`[CDA] Alarm Response`** (extend), optionally via `script.cda_alarm_noise`
- Independent per target with `continue_on_error`; Silence/Disarm stops sirens and media/TTS
- Priority: hardware sirens → speakers/TTS → notifications (existing design)

## Non-goals

- Feature-complete Alarmo clone (rich UI, MQTT broker mode, every edge case)
- Perfect Frient LED/buzzer/countdown (ZHA IAS ACE central role remains upstream-limited; opt-in best-effort only)
- Embedding Chromecast / media logic inside the panel state machine
- Replacing cover-manager or lighting blueprints with alarm-owned logic
- Committing secrets (PIN codes) in the git repo

## Architecture

```text
Frient KEPZB-110 (ZHA events)
NFC / Companion / dashboards / blueprints
        │
        ▼
┌──────────────────────────────────┐
│  packages/cda-alarm              │
│  alarm_control_panel (truth)     │
│  codes · sensors · delays        │
└────────────────┬─────────────────┘
                 │ state + open_sensors
                 ▼
  alarm-response (sirens, speakers/TTS, phone, Telegram)
  nfc-disarm · UI · future presence / settling hooks
```

**Orchestration rule:** the panel owns security state; response and house systems own effects. The alarm calls scripts/services; it does not become a second cover or media integration.

## Components (v1)

| Piece | Responsibility |
|-------|----------------|
| Config entry UI | Panel name, modes subset (`home` / `away` / `night`), sensors per mode, entry/exit delays, codes, optional Frient device |
| `alarm_control_panel` entity | Standard HA states/services; `open_sensors` on trigger |
| Code validator | Match PIN/RFID/NFC against stored codes |
| Frient binding | Listen `zha_event` for the configured device; validate; change CDA panel only |
| Optional LED feedback | Raw IAS ACE, opt-in, never blocks arm/disarm |

## Frient flow (v1)

1. User enters PIN / presents badge on KEPZB-110  
2. ZHA emits `zha_event`  
3. CDA validates against its code store  
4. On success → `alarm_arm_*` / `alarm_disarm` on **CDA panel only**  
5. No service calls to the Frient ZHA `alarm_control_panel`  
6. LED feedback optional and best-effort  

This removes the dual-panel mirror that causes B and most of D, and unifies C.

## Blueprint impact

| Blueprint | Change |
|-----------|--------|
| `frient_keypad_with_alarmo` | Retarget or replace: input-only binding to CDA panel; drop mirror sync |
| `alarm-response` | Default panel entity → CDA; add available media_players + custom sound + TTS volume force/restore |
| `nfc-disarm` | Default panel → CDA; codes remain in CDA store (automation may pass code or rely on panel policy) |

API stays HA-standard so behavior tests and fixtures keep working with a renamed entity.

## Migration from Alarmo

1. Install/load `cda-alarm`, create panel, copy sensors / delays / codes  
2. Point Frient automation at CDA (no ZHA panel mirror)  
3. Point `alarm-response` and `nfc-disarm` at CDA  
4. Full cycle: arm → trip sensor → response (siren/notify) → disarm  
5. Disable/remove Alarmo  

Parallel run is allowed during cutover.

## Testing

- Integration pytest: state transitions, valid/invalid codes, `open_sensors`, entry/exit timing  
- Blueprint smoke with `alarm_control_panel.cda_*` fixtures  
- No credentials in fixtures beyond dummy codes  

## Success criteria

**v1**

- [ ] Single source of truth (no Alarmo ↔ Frient panel sync)  
- [ ] Unified codes (PIN / RFID / NFC)  
- [ ] Reliable Frient arm/disarm without touching ZHA panel entity  
- [ ] Existing blueprints work against CDA entity with standard services + `open_sensors`  
- [ ] Speaker/TTS noise is designed as Alarm Response work, not panel core  

**Later**

- [ ] v1.5 leave-home actionable prompt (+ optional auto-arm)  
- [ ] v2 settling gates before arm  
- [ ] v3 profile orchestration for covers/lights  

## Open decisions (for implementation plan)

1. Entity / domain naming (`cda_alarm` vs `mirabelle_alarm`) and friendly default entity id  
2. Whether invalid arm with open sensors is hard-block or warn-and-arm  
3. Storage of codes: config entry data vs HA secrets helper  
4. HACS sub-repo sync in the same PR wave as cover-manager, or later  

## References

- Current bridge: `blueprints/automations/frient_keypad_with_alarmo.yaml`  
- Response: `blueprints/automations/alarm-response.yaml`  
- Package precedent: `packages/cover-manager/`  
- ZHA IAS ACE limits: documented in `docs/frient-keypad-with-alarmo.md`  
