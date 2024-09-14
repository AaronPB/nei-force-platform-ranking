from enum import Enum


class ConfigPaths(Enum):
    # Settings
    CUSTOM_CONFIG_PATH = "settings.custom_config_path"

    RECORD_INTERVAL_MS = "settings.recording.data_interval_ms"
    RECORD_TARE_AMOUNT = "settings.recording.tare_data_amount"

    # Sensors
    SENSOR_GROUPS_SECTION = "sensor_groups"
    SENSORS_SECTION = "sensors"
