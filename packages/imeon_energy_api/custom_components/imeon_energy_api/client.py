"""Minimal HTTP client for Imeon inverters (local LAN)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Tuple

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
        # Use form data with string values (mirrors upstream)
        payload = FormData()
        payload.add_field("do_login", "true")
        payload.add_field("email", username)
        payload.add_field("passwd", password)
        url = self._url("/login")
        headers = {
            "Accept": "application/json",
            "User-Agent": "homeassistant-imeon/1.0",
            "Referer": f"http://{self.host}/",
            "Origin": f"http://{self.host}",
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
                # force-update cookies to be sure they're stored
                self._session.cookie_jar.update_cookies(resp.cookies)
                _LOGGER.debug("Login set cookies: %s", list(resp.cookies.keys()))
                # store creds for auto-relogin
                self._username = username
                self._password = password
                return data

    async def get_data_instant(self, info_type: str = "data", *, allow_retry: bool = True) -> Dict[str, Any]:
        """Fetch instant data (/data | /scan | /imeon-status)."""
        assert info_type in ("data", "scan", "status"), "info_type must be data|scan|status"
        url, fallback = self._instant_urls(info_type)
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
                _LOGGER.debug(
                    "Unexpected content-type on %s: %s (status %s, preview=%s)",
                    url,
                    ctype,
                    resp.status,
                    text_preview,
                )
                # If HTML/session expired, try to relogin once
                if allow_retry and self._username and self._password:
                    _LOGGER.debug("Response type %s, retrying login then fetch", ctype)
                    await self.login(self._username, self._password)
                    # Retry same endpoint once
                    try:
                        return await self.get_data_instant(info_type, allow_retry=False)
                    except ValueError as err:
                        # If still HTML and a fallback exists (scan), try it once
                        if info_type == "data" and fallback and allow_retry is False:
                            _LOGGER.debug("Trying fallback endpoint for data: %s", fallback)
                            return await self._fetch_fallback(fallback, headers)
                        raise err
                # If still not JSON, optionally try fallback for data
                if info_type == "data" and fallback:
                    _LOGGER.debug("Trying fallback endpoint for data: %s", fallback)
                    return await self._fetch_fallback(fallback, headers)
                raise ValueError(f"Unexpected response type {ctype}: {text_preview}")
            return await resp.json()

    async def get_monitor(self, time: str = "hour") -> Dict[str, Any]:
        """Fetch monitoring data from /api/monitor."""
        import json
        url = self._url(f"/api/monitor?time={time}")
        headers = {
            "Accept": "application/json",
            "User-Agent": "homeassistant-imeon/1.0",
            "Referer": f"http://{self.host}/",
            "Origin": f"http://{self.host}",
        }
        async with self._session.get(url, timeout=self._timeout, headers=headers) as resp:
            if resp.status != 200:
                raise ValueError(f"GET monitor failed (status {resp.status})")
            ctype = resp.headers.get("Content-Type", "").lower()
            if "application/json" not in ctype:
                text_preview = (await resp.text())[:200]
                raise ValueError(f"Unexpected response type {ctype}: {text_preview}")
            data = await resp.json()
            # Parse the "result" field which is a JSON string
            if "result" in data and isinstance(data["result"], str):
                try:
                    data["result"] = json.loads(data["result"])
                except json.JSONDecodeError:
                    pass
            return data

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

    def _instant_urls(self, info_type: str) -> Tuple[str, str | None]:
        """Return primary and fallback URLs for instant data."""
        urls = {
            "data": self._url("/data"),
            "scan": self._url("/scan?scan_time=&single=true"),
            "status": self._url("/imeon-status"),
        }
        fallback = self._url("/scan?scan_time=&single=true") if info_type == "data" else None
        return urls[info_type], fallback

    async def _fetch_fallback(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Fetch from a fallback endpoint once (no relogin)."""
        async with self._session.get(url, timeout=self._timeout, headers=headers) as resp:
            ctype = resp.headers.get("Content-Type", "").lower()
            if "application/json" not in ctype:
                text_preview = (await resp.text())[:200]
                raise ValueError(f"Fallback also returned non-JSON ({ctype}): {text_preview}")
            return await resp.json()

