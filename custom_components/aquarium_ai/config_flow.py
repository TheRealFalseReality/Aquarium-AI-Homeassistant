"""Config flow for Aquarium AI integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    CONF_AQUARIUM_NAME,
    CONF_TEMPERATURE_SENSOR,
    CONF_AQUARIUM_TYPE,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_FREQUENCY,
    UPDATE_FREQUENCIES,
)

_LOGGER = logging.getLogger(__name__)

class AquariumAIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquarium AI."""

    VERSION = 1

    @staticmethod
    @callback  
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return AquariumAIOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug("Config flow step_user called with input: %s", user_input)
        
        if user_input is not None:
            # Use the aquarium name as the title
            aquarium_name = user_input.get(CONF_AQUARIUM_NAME, "Aquarium AI")
            _LOGGER.debug("Creating config entry with title: %s", aquarium_name)
            return self.async_create_entry(title=aquarium_name, data=user_input)

        # Get all temperature sensors
        all_sensors = self.hass.states.async_all('sensor')
        temperature_sensors = [
            entity.entity_id for entity in all_sensors 
            if entity.attributes.get('device_class') == 'temperature' or
               'temperature' in entity.entity_id.lower() or
               'temp' in entity.entity_id.lower() or
               entity.attributes.get('unit_of_measurement') in ['°C', '°F', 'C', 'F']
        ]

        data_schema = vol.Schema({
            vol.Required(CONF_AQUARIUM_NAME, default="My Aquarium"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_AQUARIUM_TYPE, default="Freshwater"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_TEMPERATURE_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            ),
            vol.Required(CONF_UPDATE_FREQUENCY, default=DEFAULT_FREQUENCY): SelectSelector(
                SelectSelectorConfig(options=list(UPDATE_FREQUENCIES.keys()), mode=SelectSelectorMode.DROPDOWN)
            ),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema,
            description_placeholders={
                "aquarium_name": "Name for your aquarium setup",
                "aquarium_type": "Type of aquarium (e.g., Freshwater, Marine, Brackish)",
                "temperature_sensor": "Select the temperature sensor for your aquarium",
                "update_frequency": "How often should the AI analysis run automatically"
            }
        )


class AquariumAIOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Aquarium AI."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        _LOGGER.debug("Options flow step_init called with input: %s", user_input)
        
        if user_input is not None:
            # Update the config entry data with new values
            new_data = self.config_entry.data.copy()
            
            # Update any changed values
            if CONF_AQUARIUM_NAME in user_input:
                new_data[CONF_AQUARIUM_NAME] = user_input[CONF_AQUARIUM_NAME]
            if CONF_AQUARIUM_TYPE in user_input:
                new_data[CONF_AQUARIUM_TYPE] = user_input[CONF_AQUARIUM_TYPE] 
            if CONF_TEMPERATURE_SENSOR in user_input:
                new_data[CONF_TEMPERATURE_SENSOR] = user_input[CONF_TEMPERATURE_SENSOR]
            
            # Update the config entry data
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            
            # Return options entry for frequency (stored in options, not data)
            return self.async_create_entry(
                title="", 
                data={CONF_UPDATE_FREQUENCY: user_input.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY)}
            )

        # Get current values from config entry
        current_name = self.config_entry.data.get(CONF_AQUARIUM_NAME, "My Aquarium")
        current_type = self.config_entry.data.get(CONF_AQUARIUM_TYPE, "Freshwater")
        current_sensor = self.config_entry.data.get(CONF_TEMPERATURE_SENSOR, "")
        current_frequency = self.config_entry.options.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY)

        options_schema = vol.Schema({
            vol.Required(
                CONF_AQUARIUM_NAME,
                default=current_name
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(
                CONF_AQUARIUM_TYPE,
                default=current_type
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(
                CONF_TEMPERATURE_SENSOR,
                default=current_sensor
            ): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            ),
            vol.Required(
                CONF_UPDATE_FREQUENCY,
                default=current_frequency
            ): SelectSelector(
                SelectSelectorConfig(options=list(UPDATE_FREQUENCIES.keys()), mode=SelectSelectorMode.DROPDOWN)
            ),
        })

        return self.async_show_form(
            step_id="init", 
            data_schema=options_schema,
            description_placeholders={
                "aquarium_name": "Name for your aquarium setup",
                "aquarium_type": "Type of aquarium (e.g., Freshwater, Marine, Brackish)",
                "temperature_sensor": "Select the temperature sensor for your aquarium",
                "update_frequency": "How often should the AI analysis run automatically"
            }
        )