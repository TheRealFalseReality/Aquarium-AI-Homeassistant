"""Constants for the Aquarium AI integration."""
from typing import Final

DOMAIN: Final = "aquarium_ai"

# Configuration constants
CONF_SENSORS: Final = "sensors"
CONF_AQUARIUM_TYPE: Final = "aquarium_type"
CONF_UPDATE_FREQUENCY: Final = "update_frequency"

# Default values
DEFAULT_FREQUENCY: Final = "Every 6 hours"

# Update frequency options (Label: minutes)
UPDATE_FREQUENCIES: Final = {
    "Every hour": 60,
    "Every 3 hours": 180,
    "Every 6 hours": 360,
    "Every 12 hours": 720,
    "Every 24 hours": 1440,
}