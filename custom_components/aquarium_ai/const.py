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
CONF_UPDATE_FREQUENCY: Final = "update_frequency"
CONF_AI_TASK: Final = "ai_task"

# Default values
DEFAULT_TANK_NAME: Final = "My Aquarium"
DEFAULT_AQUARIUM_TYPE: Final = "Freshwater"
DEFAULT_FREQUENCY: Final = "1_hour"

# Update frequency options (in minutes)
UPDATE_FREQUENCIES: Final = {
    "1_hour": 60,
    "2_hours": 120,
    "4_hours": 240,
    "6_hours": 360,
    "12_hours": 720,
    "daily": 1440,
}