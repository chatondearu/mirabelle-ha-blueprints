"""Helpers to load repo blueprints in pytest with an in-memory Home Assistant instance."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.components import automation, script
from homeassistant.components.blueprint import models
from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import yaml as yaml_util

REPO_ROOT = Path(__file__).resolve().parents[2]
BLUEPRINTS_ROOT = REPO_ROOT / "blueprints"


def _entity_id_for_unique_id(hass: HomeAssistant, domain: str, unique_id: str) -> str:
    """Resolve the entity_id registered for a config unique_id."""
    registry = er.async_get(hass)
    for entry in registry.entities.values():
        if entry.domain == domain and entry.unique_id == unique_id:
            return entry.entity_id
    domain_entries = [e.entity_id for e in registry.entities.values() if e.domain == domain]
    assert domain_entries, f"No {domain} entity registered after blueprint setup"
    return domain_entries[-1]


def blueprint_path(domain: str, filename: str) -> Path:
    """Resolve a blueprint file path from domain and filename."""
    folder = "automations" if domain == "automation" else "scripts"
    return BLUEPRINTS_ROOT / folder / filename


@contextlib.contextmanager
def patch_blueprint(filename: str, domain: str) -> Iterator[None]:
    """Patch blueprint loading so use_blueprint reads from this repository."""
    data_path = blueprint_path(domain, filename)
    if domain == "automation":
        schema = automation.config.AUTOMATION_BLUEPRINT_SCHEMA
    else:
        schema = BLUEPRINT_SCHEMA

    orig_load = models.DomainBlueprints._load_blueprint

    @callback
    def mock_load_blueprint(self: models.DomainBlueprints, path: str) -> models.Blueprint:
        if path != filename:
            pytest.fail(f"Unexpected blueprint path {path!r}, expected {filename!r}")
        return models.Blueprint(
            yaml_util.load_yaml(data_path),
            expected_domain=self.domain,
            path=path,
            schema=schema,
        )

    with patch(
        "homeassistant.components.blueprint.models.DomainBlueprints._load_blueprint",
        mock_load_blueprint,
    ):
        yield


async def async_load_automation_blueprint(
    hass: HomeAssistant,
    filename: str,
    inputs: dict[str, Any],
    *,
    automation_id: str = "test_automation",
) -> str:
    """Load an automation from a repo blueprint and return entity_id."""
    with patch_blueprint(filename, "automation"):
        assert await async_setup_component(
            hass,
            "automation",
            {
                "automation": [
                    {
                        "id": automation_id,
                        "alias": f"Test {automation_id}",
                        "use_blueprint": {
                            "path": filename,
                            "input": inputs,
                        },
                    }
                ]
            },
        )
    await hass.async_block_till_done()
    return _entity_id_for_unique_id(hass, "automation", automation_id)


async def async_load_script_blueprint(
    hass: HomeAssistant,
    filename: str,
    inputs: dict[str, Any],
    *,
    script_id: str = "test_script",
) -> str:
    """Load a script from a repo blueprint and return entity_id."""
    with patch_blueprint(filename, "script"):
        assert await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    script_id: {
                        "use_blueprint": {
                            "path": filename,
                            "input": inputs,
                        }
                    }
                }
            },
        )
    await hass.async_block_till_done()
    return _entity_id_for_unique_id(hass, "script", script_id)
