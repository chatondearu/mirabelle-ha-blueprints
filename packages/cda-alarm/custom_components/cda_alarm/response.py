"""Alarm response runner (sirens, media noise, TTS)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_RESP_ENABLE_TTS,
    CONF_RESP_NOISE_PLAYERS,
    CONF_RESP_NOISE_VOLUME,
    CONF_RESP_SIREN_DURATION,
    CONF_RESP_SIREN_TONE,
    CONF_RESP_SIRENS,
    CONF_RESP_SOUND_CONTENT_ID,
    CONF_RESP_TTS_MESSAGE,
    CONF_RESP_TTS_PLAYERS,
    CONF_RESPONSE,
    DEFAULT_NOISE_VOLUME,
    DEFAULT_RESPONSE,
    DEFAULT_TTS_MESSAGE,
)

_LOGGER = logging.getLogger(__name__)
_UNAVAILABLE = {"unavailable", "unknown"}


def normalize_response(raw: Any) -> dict[str, Any]:
    """Return a sanitized response config dict."""
    base = dict(DEFAULT_RESPONSE)
    if not isinstance(raw, dict):
        return base
    base[CONF_RESP_SIRENS] = [
        e for e in (raw.get(CONF_RESP_SIRENS) or []) if isinstance(e, str)
    ]
    try:
        base[CONF_RESP_SIREN_DURATION] = int(raw.get(CONF_RESP_SIREN_DURATION, 0) or 0)
    except (TypeError, ValueError):
        base[CONF_RESP_SIREN_DURATION] = 0
    tone = raw.get(CONF_RESP_SIREN_TONE, "")
    base[CONF_RESP_SIREN_TONE] = tone if isinstance(tone, str) else ""
    base[CONF_RESP_NOISE_PLAYERS] = [
        e for e in (raw.get(CONF_RESP_NOISE_PLAYERS) or []) if isinstance(e, str)
    ]
    content = raw.get(CONF_RESP_SOUND_CONTENT_ID, "")
    base[CONF_RESP_SOUND_CONTENT_ID] = content if isinstance(content, str) else ""
    try:
        volume = float(raw.get(CONF_RESP_NOISE_VOLUME, DEFAULT_NOISE_VOLUME))
    except (TypeError, ValueError):
        volume = DEFAULT_NOISE_VOLUME
    base[CONF_RESP_NOISE_VOLUME] = min(max(volume, 0.0), 1.0)
    base[CONF_RESP_ENABLE_TTS] = bool(raw.get(CONF_RESP_ENABLE_TTS, False))
    message = raw.get(CONF_RESP_TTS_MESSAGE, DEFAULT_TTS_MESSAGE)
    base[CONF_RESP_TTS_MESSAGE] = (
        message if isinstance(message, str) and message else DEFAULT_TTS_MESSAGE
    )
    base[CONF_RESP_TTS_PLAYERS] = [
        e for e in (raw.get(CONF_RESP_TTS_PLAYERS) or []) if isinstance(e, str)
    ]
    return base


class CdaAlarmResponseRunner:
    """Start and stop sirens / media when the panel is triggered."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the runner for one config entry."""
        self.hass = hass
        self.entry_id = entry_id
        self._active = False

    def update_config(self, config: dict[str, Any]) -> None:
        """Refresh the cached response options."""
        self._response = normalize_response(config.get(CONF_RESPONSE))

    async def async_start(self) -> None:
        """Sound sirens and optional media noise."""
        if self._active:
            return
        self._active = True
        response = getattr(self, "_response", normalize_response(None))

        for siren in response[CONF_RESP_SIRENS]:
            data: dict[str, Any] = {"entity_id": siren}
            duration = int(response[CONF_RESP_SIREN_DURATION] or 0)
            if duration > 0:
                data["duration"] = duration
            tone = response[CONF_RESP_SIREN_TONE]
            if tone:
                data["tone"] = tone
            try:
                await self.hass.services.async_call(
                    "siren", "turn_on", data, blocking=False
                )
            except Exception:
                _LOGGER.debug("Failed to turn on siren %s", siren, exc_info=True)

        volume = response[CONF_RESP_NOISE_VOLUME]
        content_id = response[CONF_RESP_SOUND_CONTENT_ID]
        for player in response[CONF_RESP_NOISE_PLAYERS]:
            if not self._is_available(player):
                continue
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": player, "volume_level": volume},
                    blocking=False,
                )
            except Exception:
                _LOGGER.debug("Failed volume_set on %s", player, exc_info=True)
            if content_id:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "play_media",
                        {
                            "entity_id": player,
                            "media_content_id": content_id,
                            "media_content_type": "music",
                        },
                        blocking=False,
                    )
                except Exception:
                    _LOGGER.debug("Failed play_media on %s", player, exc_info=True)

        if response[CONF_RESP_ENABLE_TTS]:
            message = response[CONF_RESP_TTS_MESSAGE]
            for player in response[CONF_RESP_TTS_PLAYERS]:
                if not self._is_available(player):
                    continue
                try:
                    await self.hass.services.async_call(
                        "tts",
                        "google_translate_say",
                        {"entity_id": player, "message": message},
                        blocking=False,
                    )
                except Exception:
                    # Fall back to tts.speak if available on newer HA.
                    try:
                        await self.hass.services.async_call(
                            "tts",
                            "speak",
                            {
                                "entity_id": "tts.google_en_com",
                                "media_player_entity_id": player,
                                "message": message,
                            },
                            blocking=False,
                        )
                    except Exception:
                        _LOGGER.debug("Failed TTS on %s", player, exc_info=True)

    async def async_stop(self) -> None:
        """Stop sirens and media players."""
        if not self._active:
            return
        self._active = False
        response = getattr(self, "_response", normalize_response(None))

        for siren in response[CONF_RESP_SIRENS]:
            try:
                await self.hass.services.async_call(
                    "siren",
                    "turn_off",
                    {"entity_id": siren},
                    blocking=False,
                )
            except Exception:
                _LOGGER.debug("Failed to turn off siren %s", siren, exc_info=True)

        players = list(
            dict.fromkeys(
                response[CONF_RESP_NOISE_PLAYERS] + response[CONF_RESP_TTS_PLAYERS]
            )
        )
        for player in players:
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "media_stop",
                    {"entity_id": player},
                    blocking=False,
                )
            except Exception:
                _LOGGER.debug("Failed media_stop on %s", player, exc_info=True)

    def _is_available(self, entity_id: str) -> bool:
        """Return True when the entity exists and is not unavailable."""
        state = self.hass.states.get(entity_id)
        return state is not None and state.state not in _UNAVAILABLE
