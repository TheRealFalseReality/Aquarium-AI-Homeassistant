"""Constants for the Aquarium AI integration."""
from typing import Final

DOMAIN: Final = "aquarium_ai"

# Configuration constants
CONF_TANK_NAME: Final = "tank_name"
CONF_AQUARIUM_TYPE: Final = "aquarium_type"
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_PH_SENSOR: Final = "ph_sensor"
CONF_SALINITY_SENSOR: Final = "salinity_sensor"
CONF_DISSOLVED_OXYGEN_SENSOR: Final = "dissolved_oxygen_sensor"
CONF_WATER_LEVEL_SENSOR: Final = "water_level_sensor"
CONF_ORP_SENSOR: Final = "orp_sensor"
CONF_CAMERA: Final = "camera"
CONF_UPDATE_FREQUENCY: Final = "update_frequency"
CONF_AI_TASK: Final = "ai_task"
CONF_AUTO_NOTIFICATIONS: Final = "auto_notifications"
CONF_NOTIFICATION_FORMAT: Final = "notification_format"

# Default values
DEFAULT_TANK_NAME: Final = "My Aquarium"
DEFAULT_AQUARIUM_TYPE: Final = "Freshwater"
DEFAULT_FREQUENCY: Final = "1_hour"
DEFAULT_AUTO_NOTIFICATIONS: Final = True
DEFAULT_NOTIFICATION_FORMAT: Final = "detailed"

# Update frequency options (in minutes)
UPDATE_FREQUENCIES: Final = {
    "1_hour": 60,
    "2_hours": 120,
    "4_hours": 240,
    "6_hours": 360,
    "12_hours": 720,
    "daily": 1440,
    "never": None,  # Manual analysis only
}

# Notification format options
NOTIFICATION_FORMATS: Final = {
    "detailed": "Full and detailed evaluation",
    "condensed": "Condensed version with brief analysis", 
    "minimal": "Minimal with parameters and overall analysis only"
}