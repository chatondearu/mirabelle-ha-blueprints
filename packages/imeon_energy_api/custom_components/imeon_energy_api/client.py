"""Minimal HTTP client for Imeon inverters (local LAN)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from aiohttp import ClientSession, ClientError

_LOGGER = logging.getLogger(__name__)


class ImeonHttpClient:
    """Lightweight client that handles login + data fetch using HA aiohttp session."""

    def __init__(self, host: str, session: ClientSession, timeout: int = 15) -> None:
        # Expect host without protocol (e.g., 192.168.x.x)
        self.host = host.replace("http://", "").replace("https://", "")
        self._session = session
        self._timeout = timeout
        self._lock = asyncio.Lock()

    def _url(self, path: str) -> str:
        return f"http://{self.host}{path}"

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate against /login and keep cookies in shared session."""
        payload = {"do_login": True, "email": username, "passwd": password}
        url = self._url("/login")
        async with self._lock:  # avoid concurrent logins
            async with self._session.post(url, data=payload, timeout=self._timeout) as resp:
                if resp.status != 200:
                    raise ValueError(f"Login failed (status {resp.status})")
                ctype = resp.headers.get("Content-Type", "").lower()
                if "application/json" not in ctype:
                    text_preview = (await resp.text())[:200]
                    raise ValueError(f"Unexpected login response type {ctype}: {text_preview}")
                data = await resp.json()
                return data

    async def get_data_instant(self, info_type: str = "data") -> Dict[str, Any]:
        """Fetch instant data (/data | /scan | /imeon-status)."""
        assert info_type in ("data", "scan", "status"), "info_type must be data|scan|status"
        urls = {
            "data": self._url("/data"),
            "scan": self._url("/scan?scan_time=&single=true"),
            "status": self._url("/imeon-status"),
        }
        url = urls[info_type]
        async with self._session.get(url, timeout=self._timeout) as resp:
            if resp.status != 200:
                raise ValueError(f"GET {info_type} failed (status {resp.status})")
            ctype = resp.headers.get("Content-Type", "").lower()
            if "application/json" not in ctype:
                text_preview = (await resp.text())[:200]
                raise ValueError(f"Unexpected response type {ctype}: {text_preview}")
            return await resp.json()

    async def get_energy(self) -> Dict[str, Any]:
        """Fetch energy aggregates if available."""
        url = self._url("/api/energy")
        async with self._session.get(url, timeout=self._timeout) as resp:
            if resp.status != 200:
                raise ValueError(f"GET energy failed (status {resp.status})")
            ctype = resp.headers.get("Content-Type", "").lower()
            if "application/json" not in ctype:
                text_preview = (await resp.text())[:200]
                raise ValueError(f"Unexpected response type {ctype}: {text_preview}")
            return await resp.json()

