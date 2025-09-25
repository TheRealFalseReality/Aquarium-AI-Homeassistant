"""Config flow for Aquarium AI integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_SENSORS,
    CONF_AQUARIUM_TYPE,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_FREQUENCY,
    UPDATE_FREQUENCIES,
)

AQUARIUM_TYPES = ["Marine", "Freshwater - Tropical", "Freshwater - Coldwater", "Brackish"]

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
        if user_input is not None:
            return self.async_create_entry(title="Aquarium AI", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_AQUARIUM_TYPE): SelectSelector(
                SelectSelectorConfig(options=AQUARIUM_TYPES, mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_SENSORS): EntitySelector(
                EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Required(CONF_UPDATE_FREQUENCY, default=DEFAULT_FREQUENCY): SelectSelector(
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
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required(
                CONF_UPDATE_FREQUENCY,
                default=self.config_entry.options.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY),
            ): SelectSelector(
                SelectSelectorConfig(options=list(UPDATE_FREQUENCIES.keys()), mode=SelectSelectorMode.DROPDOWN)
            ),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)