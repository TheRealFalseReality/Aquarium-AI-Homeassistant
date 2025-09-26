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
    BooleanSelector,
    BooleanSelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_TANK_NAME,
    CONF_AQUARIUM_TYPE,
    CONF_TEMPERATURE_SENSOR,
    CONF_PH_SENSOR,
    CONF_SALINITY_SENSOR,
    CONF_DISSOLVED_OXYGEN_SENSOR,
    CONF_WATER_LEVEL_SENSOR,
    CONF_UPDATE_FREQUENCY,
    CONF_AI_TASK,
    CONF_AUTO_NOTIFICATIONS,
    DEFAULT_TANK_NAME,
    DEFAULT_AQUARIUM_TYPE,
    DEFAULT_FREQUENCY,
    DEFAULT_AUTO_NOTIFICATIONS,
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
            # Check that at least one sensor is provided
            sensors = [
                user_input.get(CONF_TEMPERATURE_SENSOR),
                user_input.get(CONF_PH_SENSOR),
                user_input.get(CONF_SALINITY_SENSOR),
                user_input.get(CONF_DISSOLVED_OXYGEN_SENSOR),
                user_input.get(CONF_WATER_LEVEL_SENSOR),
            ]
            
            # Filter out empty/None sensors
            valid_sensors = [s for s in sensors if s and s.strip()]
            
            if not valid_sensors:
                errors["base"] = "at_least_one_sensor"
            elif not user_input.get(CONF_AI_TASK):
                errors[CONF_AI_TASK] = "ai_task_required"
            else:
                # Validate that all provided sensors exist
                sensor_errors = {}
                for sensor_key, sensor_entity in [
                    (CONF_TEMPERATURE_SENSOR, user_input.get(CONF_TEMPERATURE_SENSOR)),
                    (CONF_PH_SENSOR, user_input.get(CONF_PH_SENSOR)),
                    (CONF_SALINITY_SENSOR, user_input.get(CONF_SALINITY_SENSOR)),
                    (CONF_DISSOLVED_OXYGEN_SENSOR, user_input.get(CONF_DISSOLVED_OXYGEN_SENSOR)),
                    (CONF_WATER_LEVEL_SENSOR, user_input.get(CONF_WATER_LEVEL_SENSOR)),
                ]:
                    if sensor_entity and sensor_entity.strip():
                        sensor_state = self.hass.states.get(sensor_entity)
                        if not sensor_state:
                            sensor_errors[sensor_key] = "sensor_not_found"
                
                if sensor_errors:
                    errors.update(sensor_errors)
                else:
                    # Use the tank name as the title
                    tank_name = user_input.get(CONF_TANK_NAME, DEFAULT_TANK_NAME)
                    _LOGGER.debug("Creating config entry with title: %s", tank_name)
                    return self.async_create_entry(title=tank_name, data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_TANK_NAME, default=DEFAULT_TANK_NAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_AQUARIUM_TYPE, default=DEFAULT_AQUARIUM_TYPE): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_TEMPERATURE_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            ),
            vol.Optional(CONF_PH_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            ),
            vol.Optional(CONF_SALINITY_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            ),
            vol.Optional(CONF_DISSOLVED_OXYGEN_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            ),
            vol.Optional(CONF_WATER_LEVEL_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
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
            vol.Required(CONF_AI_TASK): EntitySelector(
                EntitySelectorConfig(
                    domain="ai_task",
                    multiple=False
                )
            ),
            vol.Required(CONF_AUTO_NOTIFICATIONS, default=DEFAULT_AUTO_NOTIFICATIONS): BooleanSelector(
                BooleanSelectorConfig()
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
            # Check that at least one sensor is provided
            sensors = [
                user_input.get(CONF_TEMPERATURE_SENSOR),
                user_input.get(CONF_PH_SENSOR),
                user_input.get(CONF_SALINITY_SENSOR),
                user_input.get(CONF_DISSOLVED_OXYGEN_SENSOR),
                user_input.get(CONF_WATER_LEVEL_SENSOR),
            ]
            
            # Filter out empty/None sensors
            valid_sensors = [s for s in sensors if s and s.strip()]
            
            if not valid_sensors:
                return self.async_show_form(
                    step_id="init", 
                    data_schema=self._get_options_schema(self.config_entry.data),
                    errors={"base": "at_least_one_sensor"}
                )
            
            if not user_input.get(CONF_AI_TASK):
                return self.async_show_form(
                    step_id="init", 
                    data_schema=self._get_options_schema(self.config_entry.data),
                    errors={CONF_AI_TASK: "ai_task_required"}
                )
            
            # Update the config entry data directly
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
                title=user_input.get(CONF_TANK_NAME, self.config_entry.data.get(CONF_TANK_NAME, DEFAULT_TANK_NAME))
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init", 
            data_schema=self._get_options_schema(self.config_entry.data)
        )
    
    def _get_options_schema(self, current_data):
        """Get the options schema with current values."""
        # Build schema dict with optional sensor fields
        schema_dict = {
            vol.Required(
                CONF_TANK_NAME,
                default=current_data.get(CONF_TANK_NAME, DEFAULT_TANK_NAME),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_AQUARIUM_TYPE,
                default=current_data.get(CONF_AQUARIUM_TYPE, DEFAULT_AQUARIUM_TYPE),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }
        
        # Add sensor fields only if they have values to avoid "Entity None" error
        temp_sensor = current_data.get(CONF_TEMPERATURE_SENSOR)
        if temp_sensor:
            schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR, default=temp_sensor)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False
                )
            )
            
        ph_sensor = current_data.get(CONF_PH_SENSOR)
        if ph_sensor:
            schema_dict[vol.Optional(CONF_PH_SENSOR, default=ph_sensor)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_PH_SENSOR)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
            
        salinity_sensor = current_data.get(CONF_SALINITY_SENSOR)
        if salinity_sensor:
            schema_dict[vol.Optional(CONF_SALINITY_SENSOR, default=salinity_sensor)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_SALINITY_SENSOR)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
            
        dissolved_oxygen_sensor = current_data.get(CONF_DISSOLVED_OXYGEN_SENSOR)
        if dissolved_oxygen_sensor:
            schema_dict[vol.Optional(CONF_DISSOLVED_OXYGEN_SENSOR, default=dissolved_oxygen_sensor)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_DISSOLVED_OXYGEN_SENSOR)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
            
        water_level_sensor = current_data.get(CONF_WATER_LEVEL_SENSOR)
        if water_level_sensor:
            schema_dict[vol.Optional(CONF_WATER_LEVEL_SENSOR, default=water_level_sensor)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_WATER_LEVEL_SENSOR)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
        
        # Add frequency selector
        schema_dict[vol.Required(
            CONF_UPDATE_FREQUENCY,
            default=current_data.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY),
        )] = SelectSelector(
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
        )
        
        # Add AI task selector
        ai_task = current_data.get(CONF_AI_TASK)
        if ai_task:
            schema_dict[vol.Required(CONF_AI_TASK, default=ai_task)] = EntitySelector(
                EntitySelectorConfig(
                    domain="ai_task",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Required(CONF_AI_TASK)] = EntitySelector(
                EntitySelectorConfig(
                    domain="ai_task",
                    multiple=False
                )
            )
        
        # Add auto-notifications toggle
        schema_dict[vol.Required(
            CONF_AUTO_NOTIFICATIONS,
            default=current_data.get(CONF_AUTO_NOTIFICATIONS, DEFAULT_AUTO_NOTIFICATIONS),
        )] = BooleanSelector(BooleanSelectorConfig())
        
        return vol.Schema(schema_dict)