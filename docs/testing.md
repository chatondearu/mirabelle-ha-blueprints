# Testing

This repository uses **YAML validation** and **pytest** with Home Assistant’s in-memory test harness (`pytest-homeassistant-custom-component`). There is no Docker E2E suite in CI.

## Before you push

With [Nix + direnv](dev-environment.md), dependencies are provisioned when you enter the repo (`direnv allow` once). Otherwise, from the repository root (after installing dependencies manually):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
pnpm run test:ha
```

Or run the same script directly:

```bash
./scripts/run_tests.sh
```

A **Husky `pre-push` hook** runs `pnpm run test:ha` automatically after `pnpm install` (via the `prepare` script). To skip in an emergency only:

```bash
SKIP_HA_TESTS=1 git push
```

## What runs

| Step | Command |
|------|---------|
| YAML style | `yamllint blueprints/` |
| Blueprint structure | `python scripts/validate_blueprints.py` |
| Pytest | `pytest tests/ packages/cover-manager/tests packages/imeon_energy_api/tests` |

CI uses the same entry point: [`scripts/run_tests.sh`](../scripts/run_tests.sh).

## Fast iteration

While developing a single blueprint or integration:

```bash
pytest -m smoke -q
pytest tests/blueprints/automations/test_presence_based_lighting.py -q
pytest packages/cover-manager/tests/test_config_flow.py -q
```

## Blueprint coverage

| Tier | Blueprints |
|------|------------|
| **Smoke** (load via `use_blueprint`) | All 12 files under `blueprints/` |
| **Behavior** (trigger → assert services) | `presence_based_lighting` (on only), `play_sound_with_volume_control`, `set_cover_position`, `cover_control`, `scheduled_bell_sound`, `create_schedule` |
| **Smoke only (v1)** | `cover_solar_thermal_optimization`, `living-area-adaptive-lighting`, `frient_keypad_with_alarmo`, `cover_state_tracker`, `cover_cover`, `create-living-area-lighting-helpers` |

All blueprints must use the `[CDA]` name prefix and include `blueprint.homeassistant.min_version`.

## Custom integrations

- **cover_manager**: `packages/cover-manager/tests/` — config flow, setup/unload, cover entity
- **imeon_energy_api**: `packages/imeon_energy_api/tests/` — HTTP client, config flow, sensor setup smoke

## Dependency versions

Pin **`pytest-homeassistant-custom-component`** and its bundled **`homeassistant`** together in [`requirements-test.txt`](../requirements-test.txt). Bump both when raising the project minimum HA version (currently **2025.5.3**).

## Adding a new blueprint test

1. Add the file under `blueprints/` and list it in `EXPECTED_BLUEPRINTS` inside [`scripts/validate_blueprints.py`](../scripts/validate_blueprints.py).
2. Add minimal inputs to [`tests/fixtures/blueprint_inputs.py`](../tests/fixtures/blueprint_inputs.py).
3. Smoke coverage is automatic via parametrized tests when the filename is in `AUTOMATION_INPUTS` or `SCRIPT_INPUTS`.
4. For behavior tests, add a dedicated file under `tests/blueprints/` using `@pytest.mark.behavior`.
