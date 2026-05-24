"""Cover Manager integration test fixtures."""

from __future__ import annotations

import pytest

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ANN001
    """Allow loading cover_manager from custom_components."""
