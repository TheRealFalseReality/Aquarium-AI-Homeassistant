"""Constants for the Aquarium AI integration."""
from typing import Final

DOMAIN: Final = "aquarium_ai"

# Configuration constants
CONF_TANK_NAME: Final = "tank_name"
CONF_AQUARIUM_TYPE: Final = "aquarium_type"
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_UPDATE_FREQUENCY: Final = "update_frequency"

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