"""CDA Alarm integration test fixtures."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ANN001
    """Allow loading cda_alarm from custom_components."""


@pytest.fixture(autouse=True)
def mock_sidebar_panel():
    """Avoid starting the HA HTTP server for sidebar panel registration."""
    with patch(
        "custom_components.cda_alarm.async_setup_panel",
        new_callable=AsyncMock,
    ):
        yield
