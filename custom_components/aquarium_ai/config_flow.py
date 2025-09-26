"""Config flow for Aquarium AI integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_TANK_NAME,
    CONF_AQUARIUM_TYPE,
    CONF_TEMPERATURE_SENSOR,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_TANK_NAME,
    DEFAULT_AQUARIUM_TYPE,
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
        return AquariumAIOptionsFlow(config_entry)

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
            vol.Required(CONF_UPDATE_FREQUENCY, default=DEFAULT_FREQUENCY): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": "1_hour", "label": "Every hour"},
                        {"value": "2_hours", "label": "Every 2 hours"},
                        {"value": "4_hours", "label": "Every 4 hours"},
                        {"value": "6_hours", "label": "Every 6 hours"},
                        {"value": "12_hours", "label": "Every 12 hours"},
                        {"value": "daily", "label": "Daily"},
                    ],
                    mode=SelectSelectorMode.DROPDOWN
                )
            ),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema,
            errors=errors,
        )


class AquariumAIOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Aquarium AI."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the config entry data directly
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
                title=user_input.get(CONF_TANK_NAME, self.config_entry.data.get(CONF_TANK_NAME, DEFAULT_TANK_NAME))
            )
            return self.async_create_entry(title="", data={})

        # Get current values for defaults
        current_data = self.config_entry.data
        
        options_schema = vol.Schema({
            vol.Required(
                CONF_TANK_NAME,
                default=current_data.get(CONF_TANK_NAME, DEFAULT_TANK_NAME),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_AQUARIUM_TYPE,
                default=current_data.get(CONF_AQUARIUM_TYPE, DEFAULT_AQUARIUM_TYPE),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_TEMPERATURE_SENSOR,
                default=current_data.get(CONF_TEMPERATURE_SENSOR),
            ): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            ),
            vol.Required(
                CONF_UPDATE_FREQUENCY,
                default=current_data.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": "1_hour", "label": "Every hour"},
                        {"value": "2_hours", "label": "Every 2 hours"},
                        {"value": "4_hours", "label": "Every 4 hours"},
                        {"value": "6_hours", "label": "Every 6 hours"},
                        {"value": "12_hours", "label": "Every 12 hours"},
                        {"value": "daily", "label": "Daily"},
                    ],
                    mode=SelectSelectorMode.DROPDOWN
                )
            ),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)