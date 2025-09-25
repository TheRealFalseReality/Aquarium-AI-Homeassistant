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
    CONF_SENSORS,
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

        data_schema = vol.Schema({
            vol.Required(CONF_AQUARIUM_NAME, default="My Aquarium", description="Name for your aquarium setup"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_AQUARIUM_TYPE, default="Freshwater", description="Type of aquarium (e.g., Freshwater, Marine, Brackish)"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_SENSORS, description="Select the sensor entities you want the AI to analyze"): EntitySelector(
                EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Required(CONF_UPDATE_FREQUENCY, default=DEFAULT_FREQUENCY, description="How often should the AI analysis run automatically"): SelectSelector(
                SelectSelectorConfig(options=list(UPDATE_FREQUENCIES.keys()), mode=SelectSelectorMode.DROPDOWN)
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)


class AquariumAIOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Aquarium AI."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        _LOGGER.debug("Options flow step_init called with input: %s", user_input)
        
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required(
                CONF_UPDATE_FREQUENCY,
                default=self.config_entry.options.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY),
                description="How often should the AI analysis run automatically"
            ): SelectSelector(
                SelectSelectorConfig(options=list(UPDATE_FREQUENCIES.keys()), mode=SelectSelectorMode.DROPDOWN)
            ),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)