# Task 3 Report: Dashboard Snapshot Builder

## Status

Implemented `build_dashboard(hass, entry, panel_entity_id)` with runtime config
merging, area-based sensor grouping, panel attributes, camera snapshots,
triggered-camera highlighting, dashboard-safe access mode, and configuration
capability metadata.

## TDD Evidence

### RED

Command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_dashboard.py'
```

Result: collection failed as expected with
`ModuleNotFoundError: No module named 'custom_components.cda_alarm.dashboard'`.

### GREEN

The brief's fixture order caused Home Assistant to reserve
`binary_sensor.door` before entity registration, producing
`binary_sensor.door_2`. The state setup was moved after registry setup while
preserving the scenario and assertions.

Focused command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests/test_dashboard.py'
```

Result: `1 passed`.

Full package command:

```bash
nix develop -c bash -c 'PYTHONPATH=packages/cda-alarm python -m pytest packages/cda-alarm/tests -q'
```

Result: `53 passed in 1.66s`.

## Files

- `packages/cda-alarm/custom_components/cda_alarm/dashboard.py`
- `packages/cda-alarm/tests/test_dashboard.py`
