"""Unit tests for ImeonHttpClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientSession

from custom_components.imeon_energy_api.client import ImeonHttpClient


def _mock_json_response(payload: dict) -> AsyncMock:
    response = AsyncMock()
    response.status = 200
    response.headers = {"Content-Type": "application/json"}
    response.json = AsyncMock(return_value=payload)
    response.cookies = {}
    response.text = AsyncMock(return_value="")
    return response


@pytest.mark.asyncio
async def test_login_success() -> None:
    """Login should accept JSON response and return parsed data."""
    session = AsyncMock(spec=ClientSession)
    session.post.return_value.__aenter__.return_value = _mock_json_response({"status": "ok"})
    client = ImeonHttpClient("192.168.1.10", session)
    data = await client.login("user@local", "secret")
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_get_data_instant_success() -> None:
    """get_data_instant should return JSON payload from /data."""
    session = AsyncMock(spec=ClientSession)
    session.get.return_value.__aenter__.return_value = _mock_json_response({"Power": 1200})
    client = ImeonHttpClient("192.168.1.10", session)
    data = await client.get_data_instant("data")
    assert data["Power"] == 1200


@pytest.mark.asyncio
async def test_url_strips_protocol() -> None:
    """Host should be normalized without http prefix."""
    session = MagicMock(spec=ClientSession)
    client = ImeonHttpClient("http://192.168.1.20", session)
    assert client.host == "192.168.1.20"
    assert client._url("/data") == "http://192.168.1.20/data"
