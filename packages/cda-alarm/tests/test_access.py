# packages/cda-alarm/tests/test_access.py
from custom_components.cda_alarm.access import normalize_access, user_can_use_dashboard
from custom_components.cda_alarm.cameras import (
    normalize_cameras,
    normalize_sensor_camera_map,
)


def test_normalize_access_defaults() -> None:
    assert normalize_access(None) == {"mode": "admin", "user_ids": []}


def test_dashboard_acl_matrix() -> None:
    admin_only = {"mode": "admin", "user_ids": []}
    assert user_can_use_dashboard(admin_only, is_admin=True, user_id="u1")
    assert not user_can_use_dashboard(admin_only, is_admin=False, user_id="u1")

    everyone = {"mode": "everyone", "user_ids": []}
    assert user_can_use_dashboard(everyone, is_admin=False, user_id="u1")

    users = {"mode": "users", "user_ids": ["u2"]}
    assert user_can_use_dashboard(users, is_admin=False, user_id="u2")
    assert not user_can_use_dashboard(users, is_admin=False, user_id="u1")
    assert user_can_use_dashboard(users, is_admin=True, user_id="u1")


def test_normalize_cameras_and_map() -> None:
    assert normalize_cameras(["camera.a", 1, ""]) == ["camera.a"]
    assert normalize_sensor_camera_map(
        {"binary_sensor.door": "camera.a", "bad": 3}
    ) == {"binary_sensor.door": "camera.a"}
