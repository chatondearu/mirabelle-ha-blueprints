"""Minimal HTTP client for Imeon inverters (local LAN)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from aiohttp import ClientSession, ClientError, FormData

_LOGGER = logging.getLogger(__name__)


class ImeonHttpClient:
    """Lightweight client that handles login + data fetch using HA aiohttp session."""

    def __init__(
        self,
        host: str,
        session: ClientSession,
        timeout: int = 15,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        # Expect host without protocol (e.g., 192.168.x.x)
        self.host = host.replace("http://", "").replace("https://", "")
        self._session = session
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._username = username
        self._password = password

    def _url(self, path: str) -> str:
        return f"http://{self.host}{path}"

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate against /login and keep cookies in shared session."""
        # Use simple form payload (bool flag), explicit content-type
        payload = {"do_login": True, "email": username, "passwd": password}
        url = self._url("/login")
        headers = {
            "Accept": "application/json",
            "User-Agent": "homeassistant-imeon/1.0",
            "Referer": f"http://{self.host}/",
            "Origin": f"http://{self.host}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with self._lock:  # avoid concurrent logins
            async with self._session.post(
                url, data=payload, timeout=self._timeout, headers=headers
            ) as resp:
                if resp.status != 200:
                    raise ValueError(f"Login failed (status {resp.status})")
                ctype = resp.headers.get("Content-Type", "").lower()
                if "application/json" not in ctype:
                    text_preview = (await resp.text())[:200]
                    raise ValueError(f"Unexpected login response type {ctype}: {text_preview}")
                data = await resp.json()
                # store creds for auto-relogin
                self._username = username
                self._password = password
                return data

    async def get_data_instant(self, info_type: str = "data", *, allow_retry: bool = True) -> Dict[str, Any]:
        """Fetch instant data (/data | /scan | /imeon-status)."""
        assert info_type in ("data", "scan", "status"), "info_type must be data|scan|status"
        urls = {
            "data": self._url("/data"),
            "scan": self._url("/scan?scan_time=&single=true"),
            "status": self._url("/imeon-status"),
        }
        url = urls[info_type]
        headers = {
            "Accept": "application/json",
            "User-Agent": "homeassistant-imeon/1.0",
            "Referer": f"http://{self.host}/",
            "Origin": f"http://{self.host}",
        }
        async with self._session.get(url, timeout=self._timeout, headers=headers) as resp:
            if resp.status != 200:
                raise ValueError(f"GET {info_type} failed (status {resp.status})")
            ctype = resp.headers.get("Content-Type", "").lower()
            if "application/json" not in ctype:
                text_preview = (await resp.text())[:200]
                # If HTML/session expired, try to relogin once
                if allow_retry and self._username and self._password:
                    _LOGGER.debug("Response type %s, retrying login then fetch", ctype)
                    await self.login(self._username, self._password)
                    return await self.get_data_instant(info_type, allow_retry=False)
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

