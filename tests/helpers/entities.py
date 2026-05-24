"""Entity seeding helpers for Home Assistant tests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def seed_entities(hass: Any, entities: Mapping[str, tuple[str, dict[str, Any] | None]]) -> None:
    """Set entity states for tests (state, attributes)."""
    for entity_id, (state, attributes) in entities.items():
        hass.states.async_set(entity_id, state, attributes or {})
