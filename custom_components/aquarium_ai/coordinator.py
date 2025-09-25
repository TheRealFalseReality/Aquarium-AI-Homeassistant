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
        _LOGGER.info("Aquarium AI options updated, reloading integration")
        # Reload the integration to apply changes
        await hass.config_entries.async_reload(entry.entry_id)

    async def _async_update_data(self):
        """Fetch data from AI Task."""
        _LOGGER.debug("Starting AI Task data update")
        try:
            aquarium_type = self.config_entry.data[CONF_AQUARIUM_TYPE]
            temperature_sensor = self.config_entry.data[CONF_TEMPERATURE_SENSOR]
            _LOGGER.debug("Aquarium type: %s, Temperature sensor: %s", aquarium_type, temperature_sensor)

            # 1. Get temperature data
            temp_state = self.hass.states.get(temperature_sensor)
            temperature_info = "Temperature: Unknown"
            
            if temp_state and temp_state.state not in ["unknown", "unavailable"]:
                try:
                    temp_value = round(float(temp_state.state), 1)
                    temp_unit = temp_state.attributes.get("unit_of_measurement", "°C")
                    temp_name = temp_state.attributes.get("friendly_name", "Temperature")
                    temperature_info = f"{temp_name}: {temp_value}{temp_unit}"
                    _LOGGER.debug("Temperature data: %s", temperature_info)
                except (ValueError, TypeError):
                    temp_name = temp_state.attributes.get("friendly_name", "Temperature")
                    temperature_info = f"{temp_name}: {temp_state.state}"
                    _LOGGER.debug("Non-numeric temperature: %s", temperature_info)
            else:
                _LOGGER.warning("Temperature sensor %s is unavailable", temperature_sensor)

            # 2. Build the prompt for temperature analysis
            instructions = f"""Based on the current aquarium conditions:
- Type: {aquarium_type}
- {temperature_info}

Analyze the temperature conditions for this {aquarium_type.lower()} aquarium. Consider if the temperature is appropriate for the aquarium type, any potential issues, and provide recommendations. Keep each analysis under 255 characters."""

            # 3. Build the structure for AI response
            structure = {
                "temperature_analysis": {
                    "description": "An analysis of the aquarium's temperature conditions and any recommendations.",
                    "required": True,
                    "selector": {"text": None}
                },
                "overall_analysis": {
                    "description": "An overall assessment of the aquarium's current state based on temperature.",
                    "required": True,
                    "selector": {"text": None}
                },
                "quick_analysis": {
                    "description": "A quick status in 1-2 words (e.g., 'Good', 'Too Warm', 'Too Cold').",
                    "required": True,
                    "selector": {"text": None}
                }
            }
            
            _LOGGER.debug("Generated structure with %d fields: %s", len(structure), list(structure.keys()))
            
            # 4. Call the AI service
            service_data = {
                "task_name": "Aquarium Temperature Analysis",
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
                
                # Ensure all expected keys have some value to prevent None states
                expected_keys = list(structure.keys())
                for key in expected_keys:
                    if key not in result_data or result_data[key] is None:
                        result_data[key] = "No analysis available"
                        _LOGGER.warning("Missing or None value for key %s, setting default", key)
                
                return result_data
            elif response:
                _LOGGER.warning("AI Task response missing 'data' field, using response directly: %s", response)
                # If response doesn't have 'data' field, try to use the response directly
                if isinstance(response, dict):
                    # Ensure all expected keys have some value
                    expected_keys = list(structure.keys())
                    for key in expected_keys:
                        if key not in response or response[key] is None:
                            response[key] = "No analysis available"
                            _LOGGER.warning("Missing or None value for key %s, setting default", key)
                    return response
                else:
                    _LOGGER.error("AI Task response is not a dictionary: %s", type(response))
                    # Return a fallback structure
                    fallback_data = {}
                    for key in structure.keys():
                        fallback_data[key] = "Service response error"
                    return fallback_data
            else:
                _LOGGER.error("AI Task service returned empty response")
                # Return a fallback structure
                fallback_data = {}
                for key in structure.keys():
                    fallback_data[key] = "No response from AI service"
                return fallback_data

        except Exception as err:
            _LOGGER.error("Error communicating with AI Task service: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with AI Task service: {err}")