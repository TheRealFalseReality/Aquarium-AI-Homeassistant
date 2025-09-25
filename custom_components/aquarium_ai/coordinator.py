"""DataUpdateCoordinator for the Aquarium AI integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_AQUARIUM_NAME,
    CONF_SENSORS,
    CONF_AQUARIUM_TYPE,
    CONF_UPDATE_FREQUENCY,
    UPDATE_FREQUENCIES,
    DEFAULT_FREQUENCY,
)

_LOGGER = logging.getLogger(__name__)

class AquariumAIDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Aquarium AI data from the AI task."""

    def __init__(self, hass: HomeAssistant, config_entry):
        """Initialize."""
        self.config_entry = config_entry
        self.hass = hass
        
        # Get frequency string from options flow, fallback to initial data
        frequency_key = self.config_entry.options.get(
            CONF_UPDATE_FREQUENCY, self.config_entry.data.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY)
        )
        # Look up the minute value from our dictionary
        update_minutes = UPDATE_FREQUENCIES.get(frequency_key, 360)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_minutes),
        )
        
        # Add a listener for options updates
        self.config_entry.add_update_listener(self.async_options_updated)

    @staticmethod
    async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
        """Handle options update."""
        # This is a placeholder for now, but good practice to have.
        # A more complex integration might reload itself here.
        # For changing the interval, a restart of HA is simplest.
        _LOGGER.info("Aquarium AI options updated. Restart Home Assistant for the new update interval to take effect.")

    async def _async_update_data(self):
        """Fetch data from AI Task."""
        _LOGGER.debug("Starting AI Task data update")
        try:
            aquarium_type = self.config_entry.data[CONF_AQUARIUM_TYPE]
            sensor_entities = self.config_entry.data[CONF_SENSORS]
            _LOGGER.debug("Aquarium type: %s, Sensor entities: %s", aquarium_type, sensor_entities)

            # 1. Build the dynamic prompt
            conditions_list = [f"- Type: {aquarium_type}"]
            for entity_id in sensor_entities:
                state = self.hass.states.get(entity_id)
                if state and state.state not in ["unknown", "unavailable"]:
                    # Try to convert to float, but handle non-numeric values
                    try:
                        value = round(float(state.state), 1)
                        unit = state.attributes.get("unit_of_measurement", "")
                        name = state.attributes.get("friendly_name", entity_id)
                        conditions_list.append(f"- {name}: {value}{unit}")
                        _LOGGER.debug("Added numeric sensor: %s = %s%s", name, value, unit)
                    except (ValueError, TypeError):
                        # Handle non-numeric values like "Normal", "Good", etc.
                        name = state.attributes.get("friendly_name", entity_id)
                        conditions_list.append(f"- {name}: {state.state}")
                        _LOGGER.debug("Added text sensor: %s = %s", name, state.state)
                else:
                    _LOGGER.warning("Sensor %s is unavailable or unknown", entity_id)
            
            instructions = "Based on the current conditions:\n\n" + "\n".join(conditions_list)
            instructions += "\n\nAnalyse my aquarium conditions and make suggestions on how to improve if needed. Each analysis must be a single, complete sentence under 255 characters."
            _LOGGER.debug("Generated instructions: %s", instructions)

            # 2. Build the dynamic structure
            structure = {}
            for entity_id in sensor_entities:
                state = self.hass.states.get(entity_id)
                if state and state.state not in ["unknown", "unavailable"]:
                    name = state.attributes.get("friendly_name", entity_id).lower().replace(" ", "_")
                    structure[f"{name}_analysis"] = {
                        "description": f"An analysis of the aquarium's {state.attributes.get('friendly_name', entity_id)}.",
                        "required": True,
                        "selector": {"text": None}
                    }

            structure["overall_analysis"] = {
                "description": "An analysis of the aquarium's overall conditions with all sensors in mind.",
                "required": True,
                "selector": {"text": None}
            }
            structure["quick_analysis"] = {
                "description": "An analysis of the overall conditions in one or two words (e.g., 'Good', 'Slightly Warm', 'High pH').",
                "required": True,
                "selector": {"text": None}
            }
            
            _LOGGER.debug("Generated structure with %d fields: %s", len(structure), list(structure.keys()))
            
            # 3. Call the service
            service_data = {
                "task_name": "Aquarium AI Analysis",
                "instructions": instructions,
                "structure": structure,
            }
            
            _LOGGER.debug("Calling ai_task.generate_data service")
            response = await self.hass.services.async_call(
                "ai_task",
                "generate_data",
                service_data,
                blocking=True,
                return_response=True,
            )
            
            _LOGGER.debug("AI Task response: %s", response)
            
            # Extract the data from the response
            if response and "data" in response:
                result_data = response["data"]
                _LOGGER.debug("Extracted data from AI response: %s", result_data)
                return result_data
            else:
                _LOGGER.warning("AI Task response missing 'data' field: %s", response)
                return response

        except Exception as err:
            _LOGGER.error("Error communicating with AI Task service: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with AI Task service: {err}")