"""Imeon Energy API integration test fixtures."""

from __future__ import annotations

import pytest

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ANN001
    """Allow loading imeon_energy_api from custom_components."""


@pytest.fixture(autouse=True)
def expected_lingering_threads() -> bool:
    """Avoid flaky thread teardown failures from aiohttp mocks."""
    return True


