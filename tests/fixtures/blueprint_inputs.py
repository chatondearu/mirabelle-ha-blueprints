"""Minimal blueprint inputs for smoke and behavior tests."""

from __future__ import annotations

from typing import Any

# Shared entity ids used across tests.
MEDIA_PLAYER = "media_player.test"
LIGHT = "light.test"
BINARY_SENSOR = "binary_sensor.test_motion"
SWITCH = "switch.test_cover"
INPUT_TEXT_POSITION = "input_text.test_cover_position"
INPUT_TEXT_DIRECTION = "input_text.test_cover_direction"
COVER = "cover.test"
PERSON = "person.test"
ALARM = "alarm_control_panel.test"
ALARM_MIRROR = "alarm_control_panel.test_mirror"
CLIMATE = "climate.test_split"
ROOM_TEMPERATURE = "sensor.test_room_temperature"
INPUT_NUMBER_COMFORT = "input_number.test_comfort"
INPUT_NUMBER_ECO = "input_number.test_eco"
INPUT_SELECT_SEASON = "input_select.test_season_mode"
INPUT_SELECT_HVAC = "input_select.test_hvac_active"

AUTOMATION_INPUTS: dict[str, dict[str, Any]] = {
    "alarm-response.yaml": {
        "alarm_entity": ALARM,
        "sirens": ["siren.test"],
        "mobile_notify_service": "notify.mobile_app_test, notify.mobile_app_test2",
        "telegram_chat_id": "-1001234567890",
        "default_camera": "camera.test",
    },
    "nfc-disarm.yaml": {
        "alarm_entity": ALARM,
        "allowed_tag_ids": "test-tag-1, test-tag-2",
        "disarm_code": "1234",
        "notify_service": "notify.mobile_app_test",
    },
    "presence_based_lighting.yaml": {
        "presence_sensor": BINARY_SENSOR,
        "light_entity": LIGHT,
        "delay_off": 5,
    },
    "cover_control.yaml": {
        "cover_name": "Test Cover",
        "cover_switch": SWITCH,
        "travel_time": 5,
        "position": 50,
    },
    "cover_cover.yaml": {
        "cover_name": "Test Cover",
        "switch_entity": SWITCH,
        "position_helper": INPUT_TEXT_POSITION,
        "direction_helper": INPUT_TEXT_DIRECTION,
    },
    "cover_state_tracker.yaml": {
        "cover_name": "Test Cover",
        "switch_entity": SWITCH,
    },
    "scheduled_bell_sound.yaml": {
        "player_input": MEDIA_PLAYER,
        "sound_file_input": "media-source://media_source/local/test.mp3",
        "wait_time_input": 2,
        "volume_announce_input": 0.5,
        "volume_reduction_input": 0,
        "time_triggers": [],
        "sun_triggers": [],
        "custom_triggers": [],
    },
    "hvac-season-manager.yaml": {
        "season_mode_helper": INPUT_SELECT_SEASON,
        "hvac_active_helper": INPUT_SELECT_HVAC,
        "comfort_helper": INPUT_NUMBER_COMFORT,
        "eco_helper": INPUT_NUMBER_ECO,
    },
    "reversible-split-thermostat.yaml": {
        "climate_entity": CLIMATE,
        "room_temperature_sensor": ROOM_TEMPERATURE,
        "hvac_active_helper": INPUT_SELECT_HVAC,
        "comfort_helper": INPUT_NUMBER_COMFORT,
        "eco_helper": INPUT_NUMBER_ECO,
        "schedulers": [],
        "persons": [],
        "windows": [],
        "presence_delay": 0,
    },
}

# Loaded in test_smoke_heavy.py (time listeners).
AUTOMATION_INPUTS_HEAVY: dict[str, dict[str, Any]] = {
    "living-area-adaptive-lighting.yaml": {
        "color_lights": [LIGHT],
        "white_lights": [],
        "occupancy_sensors": [BINARY_SENSOR],
        "presence_persons": [],
        "require_someone_home": False,
        "delay_off": 5,
        "illuminance_sensor": "",
        "covers": [],
        "create_dashboard_helpers": False,
        "control_helper_slug": "living_area_lighting",
    },
    "cover_solar_thermal_optimization.yaml": {
        "covers": [COVER],
        "north_covers": [],
        "east_covers": [],
        "south_covers": [],
        "west_covers": [],
        "presence_persons": [PERSON],
        "cover_contact_links": [],
        "awake_entity": "",
        "awake_schedule": "",
        "outdoor_temperature": "",
        "weather_entity": "",
        "indoor_temperature": "",
        "wind_speed": "",
    },
}

AUTOMATION_INPUTS.update(AUTOMATION_INPUTS_HEAVY)

SCRIPT_INPUTS: dict[str, dict[str, Any]] = {
    "play_sound_with_volume_control.yaml": {
        "player_input": MEDIA_PLAYER,
        "sound_file_input": "media-source://media_source/local/test.mp3",
        "volume_announce_input": 0.5,
        "volume_reduction_input": 0,
        "wait_time_input": 1,
    },
    "set_cover_position.yaml": {
        "cover_switch": SWITCH,
        "position": 50,
        "travel_time": 2,
        "last_state": INPUT_TEXT_POSITION,
    },
    "create_schedule.yaml": {
        "schedule_name": "input_datetime.test_schedule",
        "times": ["08:00:00"],
    },
    "create-living-area-lighting-helpers.yaml": {
        "helper_slug": "living_area_lighting",
        "mode_helper_name": "Living Area Lighting Mode",
        "hold_helper_name": "Living Area Lighting Hold",
        "package_filename": "cda_living_area_lighting_helpers.yaml",
    },
}


def frient_keypad_inputs(device_id: str) -> dict[str, Any]:
    """Inputs for the third-party Frient keypad blueprint."""
    return {
        "keypad": device_id,
        "alarm_panel": ALARM,
        "mirror_alarm_panel": ALARM_MIRROR,
        "default_pin": "1234",
        "mirror_default_pin": "1234",
        "enable_keypad_feedback": False,
        "keypad_endpoint": 1,
    }
