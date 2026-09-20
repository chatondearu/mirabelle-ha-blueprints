# Task 4 Report: Websocket ACL and Dashboard API

## Status

Implemented the `cda_alarm/get_dashboard` websocket command, dashboard ACL
checks, explicit administrator gates, dashboard-safe non-admin configuration
reads, and normalized camera/map/access persistence.

## TDD Evidence

### RED

Command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_panel_api.py -q'
```

Result: `6 failed, 4 passed`. Failures confirmed the missing dashboard handler,
missing explicit ACL/admin checks, exposed non-admin codes, and absent
camera/map/access persistence.

### GREEN

Focused command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_panel_api.py -q'
```

Result after implementation: `10 passed in 0.24s`.

Full package command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests -q'
```

Result: `59 passed in 1.74s`.

## Files

- `packages/cda-alarm/custom_components/cda_alarm/websocket_api.py`
- `packages/cda-alarm/tests/test_panel_api.py`
