# HACS Setup for CDA Alarm

## Overview

CDA Alarm is developed in the
[mirabelle-ha-blueprints](https://github.com/chatondearu/mirabelle-ha-blueprints)
monorepo under `packages/cda-alarm/` and automatically synced to
`myrabelle-hacs-cda-alarm` for HACS.

```text
mirabelle-ha-blueprints (monorepo)
└── packages/cda-alarm/
         │
         └── sync-cda-alarm.yml (on push to main)
              │
              └── myrabelle-hacs-cda-alarm (HACS repository)
```

## For users

1. Add custom repository in HACS:
   - **Repository**: `https://github.com/chatondearu/myrabelle-hacs-cda-alarm`
   - **Category**: Integration
2. Search for **CDA Alarm** and download
3. Restart Home Assistant
4. Add the integration under **Settings → Devices & services**

Do **not** install from the monorepo URL in HACS — HACS requires this dedicated
repository.

## For developers

- Edit only `packages/cda-alarm/` in the monorepo
- After merge to `main`, workflow
  [`.github/workflows/sync-cda-alarm.yml`](../../.github/workflows/sync-cda-alarm.yml)
  syncs to the sub-repo
- Manual sync: Actions → **Sync CDA Alarm to Sub-Repository** → Run workflow
- Releases: tag the monorepo `cda-alarm-vX.Y.Z` (see
  [MONOREPO_SYNC.md](../../.github/MONOREPO_SYNC.md))

Never edit `myrabelle-hacs-cda-alarm` directly — it is overwritten by sync.
