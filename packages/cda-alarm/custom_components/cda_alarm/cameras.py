from __future__ import annotations

from typing import Any


def normalize_cameras(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [e for e in raw if isinstance(e, str) and e.startswith("camera.")]


def normalize_sensor_camera_map(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for sensor, camera in raw.items():
        if isinstance(sensor, str) and isinstance(camera, str) and camera.startswith("camera."):
            out[sensor] = camera
    return out
