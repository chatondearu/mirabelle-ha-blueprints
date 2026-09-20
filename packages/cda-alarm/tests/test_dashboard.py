import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cda_alarm.const import DOMAIN
from custom_components.cda_alarm.dashboard import build_dashboard


@pytest.mark.asyncio
async def test_build_dashboard_groups_by_area(hass: HomeAssistant) -> None:
    area = ar.async_get(hass).async_create("Kitchen")
    reg = er.async_get(hass)
    reg.async_get_or_create("binary_sensor", "test", "door", suggested_object_id="door")
    ent = reg.async_get("binary_sensor.door")
    reg.async_update_entity(ent.entity_id, area_id=area.id)
    hass.states.async_set("binary_sensor.door", "on")
    hass.states.async_set("binary_sensor.orphan", "off")

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "CDA Alarm",
            "sensor_assignments": [
                {"entity_id": "binary_sensor.door", "modes": ["away"]},
                {"entity_id": "binary_sensor.orphan", "modes": ["away"]},
            ],
            "cameras": ["camera.kitchen"],
            "sensor_camera_map": {"binary_sensor.door": "camera.kitchen"},
            "access": {"mode": "everyone", "user_ids": []},
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set(
        "alarm_control_panel.cda_alarm",
        "triggered",
        {"open_sensors": {"binary_sensor.door": "on"}},
    )
    hass.states.async_set("camera.kitchen", "idle")

    snap = build_dashboard(hass, entry, "alarm_control_panel.cda_alarm")
    names = {a["name"] for a in snap["areas"]}
    assert "Kitchen" in names
    assert "Unassigned" in names
    assert snap["highlighted_camera"] == "camera.kitchen"
    assert snap["state"] == "triggered"
    assert "can_configure" not in snap
