from __future__ import annotations

from typing import Any

from .const import (
    ACCESS_MODE_ADMIN,
    ACCESS_MODE_EVERYONE,
    ACCESS_MODE_USERS,
    ACCESS_MODES,
    CONF_ACCESS_MODE,
    CONF_ACCESS_STATE_NOTIFICATIONS,
    CONF_ACCESS_USER_IDS,
    DEFAULT_ACCESS,
)


def normalize_access(raw: Any) -> dict[str, Any]:
    base = {
        CONF_ACCESS_MODE: DEFAULT_ACCESS[CONF_ACCESS_MODE],
        CONF_ACCESS_USER_IDS: [],
        CONF_ACCESS_STATE_NOTIFICATIONS: DEFAULT_ACCESS[
            CONF_ACCESS_STATE_NOTIFICATIONS
        ],
    }
    if not isinstance(raw, dict):
        return base
    mode = raw.get(CONF_ACCESS_MODE, ACCESS_MODE_ADMIN)
    if mode not in ACCESS_MODES:
        mode = ACCESS_MODE_ADMIN
    user_ids = [
        uid for uid in (raw.get(CONF_ACCESS_USER_IDS) or []) if isinstance(uid, str) and uid
    ]
    if CONF_ACCESS_STATE_NOTIFICATIONS in raw:
        state_notifications = bool(raw.get(CONF_ACCESS_STATE_NOTIFICATIONS))
    else:
        state_notifications = DEFAULT_ACCESS[CONF_ACCESS_STATE_NOTIFICATIONS]
    return {
        CONF_ACCESS_MODE: mode,
        CONF_ACCESS_USER_IDS: user_ids,
        CONF_ACCESS_STATE_NOTIFICATIONS: state_notifications,
    }


def user_can_use_dashboard(
    access: dict[str, Any],
    *,
    is_admin: bool,
    user_id: str | None,
) -> bool:
    if is_admin:
        return True
    mode = access.get(CONF_ACCESS_MODE, ACCESS_MODE_ADMIN)
    if mode == ACCESS_MODE_EVERYONE:
        return True
    if mode == ACCESS_MODE_USERS:
        return bool(user_id) and user_id in (access.get(CONF_ACCESS_USER_IDS) or [])
    return False
