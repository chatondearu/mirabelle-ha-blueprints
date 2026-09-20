"""Constants for CDA Alarm."""

DOMAIN = "cda_alarm"

CONF_NAME = "name"
CONF_CODES = "codes"
CONF_SENSORS_AWAY = "sensors_away"
CONF_SENSORS_HOME = "sensors_home"
CONF_SENSORS_NIGHT = "sensors_night"
CONF_ENTRY_DELAY = "entry_delay"
CONF_EXIT_DELAY = "exit_delay"
CONF_BLOCK_ARM_IF_OPEN = "block_arm_if_open"
CONF_FRIENT_DEVICE_ID = "frient_device_id"
CONF_ENABLE_KEYPAD_FEEDBACK = "enable_keypad_feedback"
CONF_KEYPAD_ENDPOINT = "keypad_endpoint"

DEFAULT_ENTRY_DELAY = 30
DEFAULT_EXIT_DELAY = 60
DEFAULT_BLOCK_ARM_IF_OPEN = True
DEFAULT_KEYPAD_ENDPOINT = 44

ATTR_OPEN_SENSORS = "open_sensors"
ATTR_ARM_MODE = "arm_mode"
ATTR_ARM_FAILURE = "arm_failure"

EVENT_ARM_FAILED = f"{DOMAIN}_arm_failed"

REASON_OPEN_SENSORS = "open_sensors"
REASON_INVALID_CODE = "invalid_code"
