"""Constants for CDA Alarm."""

DOMAIN = "cda_alarm"
PANEL_URL_PATH = "cda-alarm"
FRONTEND_URL_BASE = f"/{DOMAIN}_static"

CONF_NAME = "name"
CONF_CODES = "codes"
CONF_SENSORS = "sensors"
CONF_SENSOR_ASSIGNMENTS = "sensor_assignments"
CONF_SENSORS_AWAY = "sensors_away"
CONF_SENSORS_HOME = "sensors_home"
CONF_SENSORS_NIGHT = "sensors_night"
CONF_ENTRY_DELAY = "entry_delay"
CONF_EXIT_DELAY = "exit_delay"
CONF_BLOCK_ARM_IF_OPEN = "block_arm_if_open"
CONF_FRIENT_DEVICE_ID = "frient_device_id"
CONF_ENABLE_KEYPAD_FEEDBACK = "enable_keypad_feedback"
CONF_KEYPAD_ENDPOINT = "keypad_endpoint"
CONF_KEYPADS = "keypads"
CONF_RESPONSE = "response"

CONF_KEYPAD_DEVICE_ID = "device_id"
CONF_KEYPAD_IS_DEFAULT = "is_default"
CONF_KEYPAD_FEEDBACK = "feedback"
CONF_KEYPAD_SYNC_ZHA_PANEL = "sync_zha_panel"
CONF_KEYPAD_ENDPOINT_KEY = "endpoint"

CONF_RESP_SIRENS = "sirens"
CONF_RESP_SIREN_DURATION = "siren_duration"
CONF_RESP_SIREN_TONE = "siren_tone"
CONF_RESP_NOISE_PLAYERS = "noise_media_players"
CONF_RESP_SOUND_CONTENT_ID = "alarm_sound_content_id"
CONF_RESP_NOISE_VOLUME = "noise_volume"
CONF_RESP_ENABLE_TTS = "enable_alarm_tts"
CONF_RESP_TTS_MESSAGE = "alarm_tts_message"
CONF_RESP_TTS_PLAYERS = "tts_media_players"

MODE_AWAY = "away"
MODE_HOME = "home"
MODE_NIGHT = "night"
MODE_OPTIONS = (MODE_AWAY, MODE_HOME, MODE_NIGHT)

DEFAULT_ENTRY_DELAY = 30
DEFAULT_EXIT_DELAY = 60
DEFAULT_BLOCK_ARM_IF_OPEN = True
DEFAULT_KEYPAD_ENDPOINT = 44
DEFAULT_MODES = list(MODE_OPTIONS)
DEFAULT_NOISE_VOLUME = 0.9
DEFAULT_TTS_MESSAGE = "Warning: the alarm has been triggered."
DEFAULT_RESPONSE: dict = {
    CONF_RESP_SIRENS: [],
    CONF_RESP_SIREN_DURATION: 0,
    CONF_RESP_SIREN_TONE: "",
    CONF_RESP_NOISE_PLAYERS: [],
    CONF_RESP_SOUND_CONTENT_ID: "",
    CONF_RESP_NOISE_VOLUME: DEFAULT_NOISE_VOLUME,
    CONF_RESP_ENABLE_TTS: False,
    CONF_RESP_TTS_MESSAGE: DEFAULT_TTS_MESSAGE,
    CONF_RESP_TTS_PLAYERS: [],
}

ATTR_OPEN_SENSORS = "open_sensors"
ATTR_ARM_MODE = "arm_mode"
ATTR_ARM_FAILURE = "arm_failure"

EVENT_ARM_FAILED = f"{DOMAIN}_arm_failed"

REASON_OPEN_SENSORS = "open_sensors"
REASON_INVALID_CODE = "invalid_code"

DATA_PANEL_REGISTERED = f"{DOMAIN}_panel_registered"
DATA_WS_REGISTERED = f"{DOMAIN}_ws_registered"
DATA_RESPONSE_RUNNER = "response_runner"

CONF_CAMERAS = "cameras"
CONF_SENSOR_CAMERA_MAP = "sensor_camera_map"
CONF_ACCESS = "access"
CONF_ACCESS_MODE = "mode"
CONF_ACCESS_USER_IDS = "user_ids"
CONF_ACCESS_STATE_NOTIFICATIONS = "state_notifications"

ACCESS_MODE_ADMIN = "admin"
ACCESS_MODE_EVERYONE = "everyone"
ACCESS_MODE_USERS = "users"
ACCESS_MODES = (ACCESS_MODE_ADMIN, ACCESS_MODE_EVERYONE, ACCESS_MODE_USERS)

DEFAULT_ACCESS: dict = {
    CONF_ACCESS_MODE: ACCESS_MODE_ADMIN,
    CONF_ACCESS_USER_IDS: [],
    CONF_ACCESS_STATE_NOTIFICATIONS: True,
}

WS_TYPE_GET_CONFIG = f"{DOMAIN}/get_config"
WS_TYPE_UPDATE_CONFIG = f"{DOMAIN}/update_config"
WS_TYPE_LIST_LINKED = f"{DOMAIN}/list_linked"
WS_TYPE_GET_DASHBOARD = f"{DOMAIN}/get_dashboard"

CDA_BLUEPRINT_MARKERS = (
    "alarm-response",
    "nfc-disarm",
    "frient_keypad_with_alarmo",
    "cda_alarm",
)
