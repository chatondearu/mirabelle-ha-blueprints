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

## Important Review Fix: Panel Entity Isolation

The dashboard handler now ignores the client-supplied `panel_entity_id` and
always resolves the alarm panel registered to the ACL-authorized config entry.

### RED

Command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_panel_api.py::test_get_dashboard_ignores_client_panel_entity_id -q'
```

Result: `1 failed in 0.23s`. The response exposed the state selected by the
client-supplied unrelated entity ID.

### GREEN

Focused command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_dashboard.py packages/cda-alarm/tests/test_panel_api.py -q'
```

Result: `13 passed in 0.35s`.

Full package command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests -q'
```

Result: `60 passed in 1.68s`.
