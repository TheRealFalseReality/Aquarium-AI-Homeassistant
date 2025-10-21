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
    CONF_ORP_SENSOR,
    CONF_CAMERA,
    CONF_UPDATE_FREQUENCY,
    CONF_AI_TASK,
    CONF_AUTO_NOTIFICATIONS,
    CONF_NOTIFICATION_FORMAT,
    CONF_TANK_VOLUME,
    CONF_FILTRATION,
    CONF_WATER_CHANGE_FREQUENCY,
    CONF_INHABITANTS,
    CONF_LAST_WATER_CHANGE,
    CONF_MISC_INFO,
    DEFAULT_TANK_NAME,
    DEFAULT_AQUARIUM_TYPE,
    DEFAULT_FREQUENCY,
    DEFAULT_AUTO_NOTIFICATIONS,
    DEFAULT_NOTIFICATION_FORMAT,
    DEFAULT_TANK_VOLUME,
    DEFAULT_FILTRATION,
    DEFAULT_WATER_CHANGE_FREQUENCY,
    DEFAULT_INHABITANTS,
    DEFAULT_MISC_INFO,
    UPDATE_FREQUENCIES,
    NOTIFICATION_FORMATS,
)

_LOGGER = logging.getLogger(__name__)


class AquariumAIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquarium AI."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return AquariumAIOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step - Basic Configuration."""
        _LOGGER.debug("Config flow step_user called with input: %s", user_input)
        
        errors = {}
        
        if user_input is not None:
            if not user_input.get(CONF_AI_TASK):
                errors[CONF_AI_TASK] = "ai_task_required"
            else:
                # Store the basic config data
                self._data.update(user_input)
                # Move to sensors step
                return await self.async_step_sensors()

        data_schema = vol.Schema({
            vol.Required(CONF_TANK_NAME, default=DEFAULT_TANK_NAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_AQUARIUM_TYPE, default=DEFAULT_AQUARIUM_TYPE): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Required(CONF_AI_TASK): EntitySelector(
                EntitySelectorConfig(
                    domain="ai_task",
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
                        {"value": "never", "label": "Never (manual only)"},
                    ],
                    mode=SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Required(CONF_AUTO_NOTIFICATIONS, default=DEFAULT_AUTO_NOTIFICATIONS): BooleanSelector(
                BooleanSelectorConfig()
            ),
            vol.Required(CONF_NOTIFICATION_FORMAT, default=DEFAULT_NOTIFICATION_FORMAT): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": "detailed", "label": "Full and detailed evaluation"},
                        {"value": "condensed", "label": "Condensed version with brief analysis"}, 
                        {"value": "minimal", "label": "Minimal with parameters and overall analysis only"}
                    ],
                    mode=SelectSelectorMode.DROPDOWN
                )
            ),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"step_description": "Configure basic tank settings and AI preferences"}
        )
    
    async def async_step_sensors(self, user_input=None):
        """Handle the sensors configuration step."""
        _LOGGER.debug("Config flow step_sensors called with input: %s", user_input)
        
        errors = {}
        
        if user_input is not None:
            # Check that at least one sensor is provided
            sensors = [
                user_input.get(CONF_TEMPERATURE_SENSOR),
                user_input.get(CONF_PH_SENSOR),
                user_input.get(CONF_SALINITY_SENSOR),
                user_input.get(CONF_DISSOLVED_OXYGEN_SENSOR),
                user_input.get(CONF_WATER_LEVEL_SENSOR),
                user_input.get(CONF_ORP_SENSOR),
            ]
            
            # Filter out empty/None sensors
            valid_sensors = [s for s in sensors if s and s.strip()]
            
            if not valid_sensors:
                errors["base"] = "at_least_one_sensor"
            else:
                # Validate that all provided sensors exist
                sensor_errors = {}
                for sensor_key, sensor_entity in [
                    (CONF_TEMPERATURE_SENSOR, user_input.get(CONF_TEMPERATURE_SENSOR)),
                    (CONF_PH_SENSOR, user_input.get(CONF_PH_SENSOR)),
                    (CONF_SALINITY_SENSOR, user_input.get(CONF_SALINITY_SENSOR)),
                    (CONF_DISSOLVED_OXYGEN_SENSOR, user_input.get(CONF_DISSOLVED_OXYGEN_SENSOR)),
                    (CONF_WATER_LEVEL_SENSOR, user_input.get(CONF_WATER_LEVEL_SENSOR)),
                    (CONF_ORP_SENSOR, user_input.get(CONF_ORP_SENSOR)),
                ]:
                    if sensor_entity and sensor_entity.strip():
                        sensor_state = self.hass.states.get(sensor_entity)
                        if not sensor_state:
                            sensor_errors[sensor_key] = "sensor_not_found"
                
                if sensor_errors:
                    errors.update(sensor_errors)
                else:
                    # Store sensor data
                    self._data.update(user_input)
                    # Move to tank info step
                    return await self.async_step_tank_info()

        data_schema = vol.Schema({
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
            vol.Optional(CONF_ORP_SENSOR): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            ),
            vol.Optional(CONF_CAMERA): EntitySelector(
                EntitySelectorConfig(
                    domain="camera",
                    multiple=False
                )
            ),
        })

        return self.async_show_form(
            step_id="sensors", 
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"step_description": "Select sensors to monitor (at least one required)"}
        )
    
    async def async_step_tank_info(self, user_input=None):
        """Handle the tank information configuration step."""
        _LOGGER.debug("Config flow step_tank_info called with input: %s", user_input)
        
        if user_input is not None:
            # Merge all collected data
            self._data.update(user_input)
            
            # Use the tank name as the title
            tank_name = self._data.get(CONF_TANK_NAME, DEFAULT_TANK_NAME)
            _LOGGER.debug("Creating config entry with title: %s", tank_name)
            return self.async_create_entry(title=tank_name, data=self._data)

        data_schema = vol.Schema({
            vol.Optional(CONF_TANK_VOLUME, default=DEFAULT_TANK_VOLUME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_FILTRATION, default=DEFAULT_FILTRATION): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
            ),
            vol.Optional(CONF_WATER_CHANGE_FREQUENCY, default=DEFAULT_WATER_CHANGE_FREQUENCY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(CONF_INHABITANTS, default=DEFAULT_INHABITANTS): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
            ),
            vol.Optional(CONF_LAST_WATER_CHANGE): EntitySelector(
                EntitySelectorConfig(
                    domain=["input_datetime", "sensor"],
                    multiple=False
                )
            ),
            vol.Optional(CONF_MISC_INFO, default=DEFAULT_MISC_INFO): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
            ),
        })

        return self.async_show_form(
            step_id="tank_info", 
            data_schema=data_schema,
            description_placeholders={"step_description": "Optional: Add tank details for better AI analysis"}
        )


class AquariumAIOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Aquarium AI."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self._data = {}

    async def async_step_init(self, user_input=None):
        """Manage the options - Main menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["basic_settings", "sensors", "tank_info"]
        )
    
    async def async_step_basic_settings(self, user_input=None):
        """Handle basic settings configuration."""
        if user_input is not None:
            if not user_input.get(CONF_AI_TASK):
                return self.async_show_form(
                    step_id="basic_settings", 
                    data_schema=self._get_basic_settings_schema(self.config_entry.data),
                    errors={CONF_AI_TASK: "ai_task_required"},
                    last_step=False
                )
            
            # Update the config entry data directly
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
                title=user_input.get(CONF_TANK_NAME, self.config_entry.data.get(CONF_TANK_NAME, DEFAULT_TANK_NAME))
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="basic_settings", 
            data_schema=self._get_basic_settings_schema(self.config_entry.data),
            description_placeholders={"step_description": "Configure basic tank settings and AI preferences"},
            last_step=False
        )
    
    async def async_step_sensors(self, user_input=None):
        """Handle sensors configuration."""
        if user_input is not None:
            # Check that at least one sensor is provided
            sensors = [
                user_input.get(CONF_TEMPERATURE_SENSOR),
                user_input.get(CONF_PH_SENSOR),
                user_input.get(CONF_SALINITY_SENSOR),
                user_input.get(CONF_DISSOLVED_OXYGEN_SENSOR),
                user_input.get(CONF_WATER_LEVEL_SENSOR),
                user_input.get(CONF_ORP_SENSOR),
            ]
            
            # Filter out empty/None sensors
            valid_sensors = [s for s in sensors if s and s.strip()]
            
            if not valid_sensors:
                return self.async_show_form(
                    step_id="sensors", 
                    data_schema=self._get_sensors_schema(self.config_entry.data),
                    errors={"base": "at_least_one_sensor"},
                    last_step=False
                )
            
            # Update the config entry data directly
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="sensors", 
            data_schema=self._get_sensors_schema(self.config_entry.data),
            description_placeholders={"step_description": "Select sensors to monitor (at least one required)"},
            last_step=False
        )
    
    async def async_step_tank_info(self, user_input=None):
        """Handle tank information configuration."""
        if user_input is not None:
            # Update the config entry data directly
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="tank_info", 
            data_schema=self._get_tank_info_schema(self.config_entry.data),
            description_placeholders={"step_description": "Optional: Add tank details for better AI analysis"},
            last_step=False
        )
    
    def _get_basic_settings_schema(self, current_data):
        """Get the basic settings schema with current values."""
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
                    {"value": "never", "label": "Never (manual only)"},
                ],
                mode=SelectSelectorMode.DROPDOWN
            )
        )
        
        # Add auto-notifications toggle
        schema_dict[vol.Required(
            CONF_AUTO_NOTIFICATIONS,
            default=current_data.get(CONF_AUTO_NOTIFICATIONS, DEFAULT_AUTO_NOTIFICATIONS),
        )] = BooleanSelector(BooleanSelectorConfig())
        
        # Add notification format selector
        schema_dict[vol.Required(
            CONF_NOTIFICATION_FORMAT,
            default=current_data.get(CONF_NOTIFICATION_FORMAT, DEFAULT_NOTIFICATION_FORMAT),
        )] = SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": "detailed", "label": "Full and detailed evaluation"},
                    {"value": "condensed", "label": "Condensed version with brief analysis"}, 
                    {"value": "minimal", "label": "Minimal with parameters and overall analysis only"}
                ],
                mode=SelectSelectorMode.DROPDOWN
            )
        )
        
        return vol.Schema(schema_dict)
    
    def _get_sensors_schema(self, current_data):
        """Get the sensors schema with current values."""
        schema_dict = {}
        
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
            
        orp_sensor = current_data.get(CONF_ORP_SENSOR)
        if orp_sensor:
            schema_dict[vol.Optional(CONF_ORP_SENSOR, default=orp_sensor)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_ORP_SENSOR)] = EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=False
                )
            )
            
        camera = current_data.get(CONF_CAMERA)
        if camera:
            schema_dict[vol.Optional(CONF_CAMERA, default=camera)] = EntitySelector(
                EntitySelectorConfig(
                    domain="camera",
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_CAMERA)] = EntitySelector(
                EntitySelectorConfig(
                    domain="camera",
                    multiple=False
                )
            )
        
        return vol.Schema(schema_dict)
    
    def _get_tank_info_schema(self, current_data):
        """Get the tank information schema with current values."""
        schema_dict = {}
        
        # Add tank information fields
        schema_dict[vol.Optional(
            CONF_TANK_VOLUME,
            default=current_data.get(CONF_TANK_VOLUME, DEFAULT_TANK_VOLUME),
        )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
        
        schema_dict[vol.Optional(
            CONF_FILTRATION,
            default=current_data.get(CONF_FILTRATION, DEFAULT_FILTRATION),
        )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True))
        
        schema_dict[vol.Optional(
            CONF_WATER_CHANGE_FREQUENCY,
            default=current_data.get(CONF_WATER_CHANGE_FREQUENCY, DEFAULT_WATER_CHANGE_FREQUENCY),
        )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
        
        schema_dict[vol.Optional(
            CONF_INHABITANTS,
            default=current_data.get(CONF_INHABITANTS, DEFAULT_INHABITANTS),
        )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True))
        
        # Add last water change sensor field
        last_water_change = current_data.get(CONF_LAST_WATER_CHANGE)
        if last_water_change:
            schema_dict[vol.Optional(CONF_LAST_WATER_CHANGE, default=last_water_change)] = EntitySelector(
                EntitySelectorConfig(
                    domain=["input_datetime", "sensor"],
                    multiple=False
                )
            )
        else:
            schema_dict[vol.Optional(CONF_LAST_WATER_CHANGE)] = EntitySelector(
                EntitySelectorConfig(
                    domain=["input_datetime", "sensor"],
                    multiple=False
                )
            )
        
        # Add misc info field
        schema_dict[vol.Optional(
            CONF_MISC_INFO,
            default=current_data.get(CONF_MISC_INFO, DEFAULT_MISC_INFO),
        )] = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True))
        
        return vol.Schema(schema_dict)