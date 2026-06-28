# Find Orphan Entities

## Description

`find-orphan-entities` is a maintenance script that lists Home Assistant entities
which are still **registered** but should no longer exist — typically *ghost*
entities left behind after a device was unpaired or an integration was removed.

It queries a **live** Home Assistant instance and cross-references three sources:

| Source | Transport | Purpose |
| --- | --- | --- |
| `config/entity_registry/list` | WebSocket | All registered entities |
| `config_entries/get` | WebSocket | Valid integration instances |
| `/api/states` | REST | Current states and attributes |

> The entity registry is **not** exposed over the REST API, so this script uses
> the WebSocket API for the registry and config entries.

## Prerequisites

- Home Assistant 2025.5.3 or later, reachable from where you run the script.
- A long-lived access token.
- Node.js 21+ (a native global `WebSocket` is required; the dev shell ships
  Node 22 — see [dev-environment.md](dev-environment.md)).

## Configuration

Copy `.env.example` to `.env` and set:

```env
HA_URL=http://your_ha_instance:8123
HA_TOKEN=your_long_lived_access_token
```

Optional variables:

- `HA_VERIFY_SSL`: set to `false` to accept self-signed certificates (also
  relaxes TLS verification for the WebSocket connection).
- `HA_TIMEOUT`: request/connection timeout in seconds (default: 30).

## Usage

```bash
# Human-readable report (grouped by confidence)
pnpm run find-orphan-entities

# Machine-readable JSON (stdout only; banners/logs go to stderr)
pnpm run find-orphan-entities -- --json > orphans.json
```

## How an entity is flagged

An entity is reported when one of the following is true:

1. **Integration removed (high confidence)** — its `config_entry_id` points to a
   config entry that no longer exists. The integration instance was deleted but
   the entity stayed in the registry.
2. **Restored & unavailable (ghost entities)** — its state is reported with the
   `restored: true` attribute (usually `unavailable`). Home Assistant restored it
   from the registry on startup, but no integration re-created it. This is the
   most common signature of a device/entity that no longer exists.
3. **No live state (likely orphan)** — it is registered, not disabled, yet has no
   state at all in `/api/states`.

Disabled entities (`disabled_by` set) are skipped for heuristics 2 and 3 because
they legitimately have no live state.

## Example output

```text
Registered entities: 2337
Potential orphans:   199

Integration removed (high confidence) (0)
===========================================
  none

Restored & unavailable (ghost entities) (199)
=============================================
  • automation.auto_thermostat_sal
      state "unavailable" with restored=true (not provided by any integration)
  • switch.tapo_c220_004_record_to_sd_card
      state "unavailable" with restored=true (not provided by any integration)
  ...
```

## Cleaning up

This script is **read-only**; it never deletes anything. After reviewing the
list, remove confirmed orphans in Home Assistant via
**Settings → Devices & Services → Entities** (filter by *Unavailable*/*Restored*),
or by deleting the corresponding device.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `WebSocket authentication failed` | Invalid/expired token | Recreate `HA_TOKEN` |
| `WebSocket connection error` | Wrong `HA_URL` or network/SSL issue | Check the URL; set `HA_VERIFY_SSL=false` for self-signed certs |
| `Global WebSocket is unavailable` | Node.js older than 21 | Use the Nix dev shell (Node 22) |
| Many false positives | Devices temporarily offline | Re-run when devices are online; treat *restored/no-state* groups as candidates, not certainties |
| `Command "..." failed: Unknown command` | HA version too old | Upgrade to a supported HA version |
