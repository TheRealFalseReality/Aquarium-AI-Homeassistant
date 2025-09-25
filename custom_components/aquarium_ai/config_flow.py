"""Config flow for Aquarium AI integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    CONF_TANK_NAME,
    CONF_AQUARIUM_TYPE,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_TANK_NAME,
    DEFAULT_AQUARIUM_TYPE,
)

_LOGGER = logging.getLogger(__name__)


class AquariumAIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquarium AI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug("Config flow step_user called with input: %s", user_input)
        
        errors = {}
        
        if user_input is not None:
            # Validate the temperature sensor exists
            temp_sensor = user_input.get(CONF_TEMPERATURE_SENSOR)
            if temp_sensor:
                sensor_state = self.hass.states.get(temp_sensor)
                if not sensor_state:
                    errors[CONF_TEMPERATURE_SENSOR] = "sensor_not_found"
                else:
                    # Use the tank name as the title
                    tank_name = user_input.get(CONF_TANK_NAME, DEFAULT_TANK_NAME)
                    _LOGGER.debug("Creating config entry with title: %s", tank_name)
                    return self.async_create_entry(title=tank_name, data=user_input)
            else:
                errors[CONF_TEMPERATURE_SENSOR] = "sensor_required"

        data_schema = vol.Schema({
            vol.Required(CONF_TANK_NAME, default=DEFAULT_TANK_NAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_AQUARIUM_TYPE, default=DEFAULT_AQUARIUM_TYPE): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_TEMPERATURE_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            ),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema,
            errors=errors,
        )