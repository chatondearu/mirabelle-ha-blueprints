"""Shared pytest fixtures for Mirabelle HA Blueprints."""

from __future__ import annotations

import pytest

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ANN001
    """Enable loading custom integrations from custom_components/."""


@pytest.fixture
def blueprints_root() -> str:
    """Path to blueprints directory."""
    from tests.helpers.blueprint_loader import BLUEPRINTS_ROOT

    return str(BLUEPRINTS_ROOT)
