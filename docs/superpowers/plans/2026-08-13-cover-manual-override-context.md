# Cover Manager Command Context Propagation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Propagate the HA service/event context across Cover Manager position updates so blueprint manual-override detection stops false-positive on automation moves.

**Architecture:** Capture `Context` when a cover command or wall-switch event starts movement; re-apply it before every `async_write_ha_state` during travel; clear it after the final idle write. Blueprint logic stays unchanged (option B: night respects real manual override).

**Tech Stack:** Home Assistant custom component (`cover_manager`), pytest + `pytest-homeassistant-custom-component`, pnpm/`nix develop` test runner.

## Global Constraints

- Target Home Assistant **2025.5.3** or later.
- Repository docs and user-facing text in **English**.
- Conventional Commits with required scope (e.g. `feat(cover-manager): ...`).
- Do not commit secrets; do not push unless explicitly requested.
- Prefer `nix develop -c …` for project commands when using the flake shell.

## File map

| File | Role |
| ---- | ---- |
| `packages/cover-manager/custom_components/cover_manager/cover.py` | Capture / apply / clear command context; use on all state writes during movement |
| `packages/cover-manager/tests/test_cover.py` | Regression tests for parent_id retention vs switch path |
| `packages/cover-manager/custom_components/cover_manager/manifest.json` | Bump version `1.0.0` → `1.0.1` |
| `packages/cover-manager/package.json` | Align package version to `1.0.1` |
| `docs/cover_solar_thermal_optimization.md` | Troubleshooting note about Cover Manager ≥ 1.0.1 |
| `docs/superpowers/specs/2026-08-13-cover-manual-override-context-design.md` | Mark status implemented when done |

---

### Task 1: Failing tests for context propagation

**Files:**
- Modify: `packages/cover-manager/tests/test_cover.py`
- Test: `packages/cover-manager/tests/test_cover.py`

**Interfaces:**
- Consumes: existing cover setup via `MockConfigEntry` + `DOMAIN`
- Produces: `test_set_position_preserves_service_parent_context`, `test_switch_driven_move_has_no_parent_context`

- [x] **Step 1: Write the failing tests**

Append to `packages/cover-manager/tests/test_cover.py`:

```python
import asyncio
from homeassistant.core import Context
from homeassistant.components.cover import SERVICE_SET_COVER_POSITION, ATTR_POSITION
from homeassistant.const import ATTR_ENTITY_ID


async def _setup_cover(hass: HomeAssistant, travel_time: int = 2) -> str:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Ctx Cover",
            "switch_entity": "switch.ctx_cover",
            "travel_time": travel_time,
            "initial_position": 50,
            "pulse_gap": 0.05,
            "acceleration_duration": 0,
        },
        title="Ctx Cover",
    )
    entry.add_to_hass(hass)
    hass.states.async_set("switch.ctx_cover", "off", {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entities = [
        e for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == COVER_DOMAIN
    ]
    return entities[0].entity_id


@pytest.mark.asyncio
async def test_set_position_preserves_service_parent_context(hass: HomeAssistant) -> None:
    """Position ticks during set_cover_position must keep the service parent_id."""
    entity_id = await _setup_cover(hass, travel_time=2)
    parent = Context()
    child = Context(parent_id=parent.id)

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 100},
        blocking=False,
        context=child,
    )
    await asyncio.sleep(0.5)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.context.parent_id == parent.id


@pytest.mark.asyncio
async def test_switch_driven_move_has_no_parent_context(hass: HomeAssistant) -> None:
    """Wall-switch moves must not inherit a fabricated automation parent_id."""
    entity_id = await _setup_cover(hass, travel_time=2)
    hass.states.async_set("switch.ctx_cover", "on", {}, context=Context())
    await asyncio.sleep(0.5)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state in ("opening", "closing", "open", "closed")
    assert state.context.parent_id is None
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
nix develop -c bash -c 'cd packages/cover-manager && python -m pytest tests/test_cover.py::test_set_position_preserves_service_parent_context tests/test_cover.py::test_switch_driven_move_has_no_parent_context -v'
```

Expected: FAIL on `parent_id` assertion for the service-context test (current ticks use `parent_id is None`).

- [x] **Step 3: Commit tests only (optional if user requested commits)**

```bash
git add packages/cover-manager/tests/test_cover.py
git commit -m "$(cat <<'EOF'
test(cover-manager): add context propagation regression tests

EOF
)"
```

---

### Task 2: Implement command context capture/apply/clear

**Files:**
- Modify: `packages/cover-manager/custom_components/cover_manager/cover.py`

**Interfaces:**
- Consumes: `homeassistant.core.Context`; entity `self._context` / `async_set_context`
- Produces: `_command_context`, `_capture_command_context()`, `_write_ha_state()`, clear-on-idle in `_update_and_notify`

- [ ] **Step 1: Add imports and instance field**

In `cover.py`:

```python
from homeassistant.core import Context, HomeAssistant, callback
```

In `__init__`, after `_acceleration_entity`:

```python
self._command_context: Context | None = None
```

- [ ] **Step 2: Add helpers and route writes**

```python
def _capture_command_context(self, context: Context | None = None) -> None:
    """Remember context for all state writes of the current command/move."""
    self._command_context = context if context is not None else self._context

def _write_ha_state(self) -> None:
    """Write state, re-applying the active command context when present."""
    if self._command_context is not None:
        self.async_set_context(self._command_context)
    self.async_write_ha_state()

def _update_and_notify(self, notify_sub_entities: bool = True) -> None:
    """Update HA state and optionally notify dynamic sub-entities."""
    self._write_ha_state()
    if notify_sub_entities:
        self._notify_dynamic_entities()
    if self._direction == DIRECTION_IDLE:
        self._command_context = None
```

Replace bare `self.async_write_ha_state()` inside `_movement_loop` and `_start_targeted_movement` / `_move_with_target` with `self._write_ha_state()`.

- [ ] **Step 3: Capture on service entry points**

At the start of `async_open_cover`, `async_close_cover`, `async_stop_cover`, `async_set_cover_position` (before early returns that still mean “no move”, capture only when a move will proceed — simplest correct approach: capture immediately after the early-return guards that skip work):

```python
async def async_open_cover(self, **kwargs: Any) -> None:
    if self.current_cover_position >= int(POSITION_MAX) and self._direction == DIRECTION_IDLE:
        return
    self._capture_command_context()
    await self._go_direction(DIRECTION_OPENING)
```

Same pattern for close/stop/set_position (for set_position, capture after the `target == current` early return).

- [ ] **Step 4: Capture wall-switch event context**

At the top of `_handle_switch_event`, after validating `new_state.state == "on"` and pass ignore/limit guards that return early, before mutating movement:

```python
self._capture_command_context(event.context)
```

This keeps `parent_id=None` for physical presses and clears any stale automation context.

- [ ] **Step 5: Re-run the new tests**

```bash
nix develop -c bash -c 'cd packages/cover-manager && python -m pytest tests/test_cover.py -v'
```

Expected: PASS for both new tests and existing cover tests.

- [ ] **Step 6: Commit**

```bash
git add packages/cover-manager/custom_components/cover_manager/cover.py packages/cover-manager/tests/test_cover.py
git commit -m "$(cat <<'EOF'
fix(cover-manager): preserve command context during cover travel

EOF
)"
```

---

### Task 3: Version bump and docs

**Files:**
- Modify: `packages/cover-manager/custom_components/cover_manager/manifest.json`
- Modify: `packages/cover-manager/package.json`
- Modify: `docs/cover_solar_thermal_optimization.md` (Troubleshooting)
- Modify: `docs/superpowers/specs/2026-08-13-cover-manual-override-context-design.md` (status)

**Interfaces:**
- Produces: Cover Manager version **1.0.1**

- [ ] **Step 1: Bump versions to 1.0.1**

`manifest.json` and `package.json`: `"version": "1.0.1"`.

- [ ] **Step 2: Troubleshooting note**

In `docs/cover_solar_thermal_optimization.md` Troubleshooting, add:

```markdown
- **Night close skipped after an automation move**: Cover Manager must be **1.0.1+** so
  automation `context.parent_id` is preserved during travel. Older versions mis-detect
  automation moves as manual override for up to Manual Override Hold minutes.
```

- [ ] **Step 3: Mark design status**

In the design spec header: `Status: Implemented`.

- [ ] **Step 4: Run cover-manager tests once more**

```bash
nix develop -c bash -c 'cd packages/cover-manager && python -m pytest tests/ -v'
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/cover-manager/custom_components/cover_manager/manifest.json packages/cover-manager/package.json docs/cover_solar_thermal_optimization.md docs/superpowers/specs/2026-08-13-cover-manual-override-context-design.md docs/superpowers/plans/2026-08-13-cover-manual-override-context.md
git commit -m "$(cat <<'EOF'
docs(cover-manager): note 1.0.1 context fix for manual override

EOF
)"
```

---

## Spec coverage check

| Spec requirement | Task |
| ---------------- | ---- |
| Propagate service context during movement | Task 2 |
| Wall switch remains parent_id none | Task 1 + Task 2 step 4 |
| Blueprint logic unchanged (B) | No blueprint code task |
| Tests for both paths | Task 1 |
| Version / troubleshooting | Task 3 |
| No reset-timer feature | Omitted intentionally |

## Placeholder scan

No TBD / “implement later” steps; commands and code are concrete.
