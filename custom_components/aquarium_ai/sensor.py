"""Sensor platform for Aquarium AI integration."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

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
    UPDATE_FREQUENCIES,
)
from . import get_sensor_info, get_simple_status, get_overall_status

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquarium AI sensors from a config entry."""
    tank_name = config_entry.data[CONF_TANK_NAME]
    aquarium_type = config_entry.data[CONF_AQUARIUM_TYPE]
    ai_task = config_entry.data.get(CONF_AI_TASK)
    frequency_key = config_entry.data.get(CONF_UPDATE_FREQUENCY, "1_hour")
    frequency_minutes = UPDATE_FREQUENCIES.get(frequency_key, 60)
    
    # Define sensor mappings
    sensor_mappings = [
        (config_entry.data.get(CONF_TEMPERATURE_SENSOR), "Temperature"),
        (config_entry.data.get(CONF_PH_SENSOR), "pH"),
        (config_entry.data.get(CONF_SALINITY_SENSOR), "Salinity"),
        (config_entry.data.get(CONF_DISSOLVED_OXYGEN_SENSOR), "Dissolved Oxygen"),
        (config_entry.data.get(CONF_WATER_LEVEL_SENSOR), "Water Level"),
    ]
    
    # Filter out empty sensors
    valid_sensor_mappings = [(entity, name) for entity, name in sensor_mappings if entity]
    
    entities = []
    
    # Create individual sensor analysis entities
    for sensor_entity, sensor_name in valid_sensor_mappings:
        entities.append(
            AquariumAISensorAnalysis(
                hass,
                config_entry,
                tank_name,
                aquarium_type,
                sensor_entity,
                sensor_name,
                ai_task,
                frequency_minutes,
                valid_sensor_mappings,
            )
        )
    
    # Create overall analysis sensor
    entities.append(
        AquariumAIOverallAnalysis(
            hass,
            config_entry,
            tank_name,
            aquarium_type,
            ai_task,
            frequency_minutes,
            valid_sensor_mappings,
        )
    )
    
    # Create simple status sensor
    entities.append(
        AquariumAISimpleStatus(
            hass,
            config_entry,
            tank_name,
            aquarium_type,
            frequency_minutes,
            valid_sensor_mappings,
        )
    )
    
    async_add_entities(entities)


class AquariumAIBaseSensor(SensorEntity):
    """Base class for Aquarium AI sensors."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        frequency_minutes: int,
        sensor_mappings: list,
    ):
        """Initialize the base sensor."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._aquarium_type = aquarium_type
        self._frequency_minutes = frequency_minutes
        self._sensor_mappings = sensor_mappings
        self._state = None
        self._available = True
        self._unsub = None
        
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await self.async_update()
        # Set up periodic updates
        self._unsub = async_track_time_interval(
            self._hass, self._async_update_data, timedelta(minutes=self._frequency_minutes)
        )
        
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self._unsub:
            self._unsub()
            
    async def _async_update_data(self, now=None) -> None:
        """Update sensor data."""
        await self.async_update()
        self.async_write_ha_state()
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available
        
    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state
        
    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Aquarium AI - {self._tank_name}",
            "manufacturer": "Aquarium AI",
            "model": "AI Analysis",
            "entry_type": "service",
        }


class AquariumAISensorAnalysis(AquariumAIBaseSensor):
    """Sensor for individual parameter AI analysis."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        sensor_entity: str,
        sensor_name: str,
        ai_task: str,
        frequency_minutes: int,
        sensor_mappings: list,
    ):
        """Initialize the sensor analysis."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._sensor_entity = sensor_entity
        self._sensor_name = sensor_name
        self._ai_task = ai_task
        self._attr_name = f"{tank_name} {sensor_name} Analysis"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_name.lower().replace(' ', '_')}_analysis"
        self._attr_icon = self._get_sensor_icon(sensor_name)
        
    def _get_sensor_icon(self, sensor_name: str) -> str:
        """Get appropriate icon for sensor type."""
        sensor_icons = {
            "Temperature": "mdi:thermometer",
            "pH": "mdi:ph", 
            "Salinity": "mdi:shaker-outline",
            "Dissolved Oxygen": "mdi:air-purifier",
            "Water Level": "mdi:waves",
        }
        return sensor_icons.get(sensor_name, "mdi:chart-line")
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get sensor info
            sensor_info = get_sensor_info(self._hass, self._sensor_entity, self._sensor_name)
            if not sensor_info:
                self._state = "Sensor unavailable"
                self._available = False
                return
                
            self._available = True
            
            # Get all sensor data for context
            all_sensor_data = []
            for sensor_entity, sensor_name in self._sensor_mappings:
                info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                if info:
                    all_sensor_data.append(info)
            
            # Build conditions string
            conditions_list = [f"- Type: {self._aquarium_type}"]
            for info in all_sensor_data:
                if info['unit']:
                    conditions_list.append(f"- {info['name']}: {info['raw_value']} {info['unit']}")
                else:
                    conditions_list.append(f"- {info['name']}: {info['raw_value']} (no units)")
            conditions_str = "\n".join(conditions_list)
            
            # Prepare AI Task data for brief analysis
            ai_task_data = {
                "task_name": f"{self._tank_name} {self._sensor_name}",
                "instructions": f"""Based on the current conditions:

{conditions_str}

Provide a brief 1-2 sentence analysis of the {self._sensor_name.lower()} for this {self._aquarium_type.lower()} aquarium. Focus specifically on the {self._sensor_name.lower()} parameter. Keep response under 200 characters. Only mention recommendations if critical - otherwise just state the current status. Always correctly write ph as pH.

IMPORTANT: Pay attention to units when evaluating values:
- Temperature: Consider if values are in Celsius (°C) or Fahrenheit (°F)
- Salinity: Consider if values are in ppt/psu or specific gravity (SG)
- Dissolved Oxygen: Consider if values are in mg/L, ppm, or percentage saturation
- Water Level: Consider if percentages or absolute measurements
- pH: Typically no units (scale 0-14)""",
                "structure": {
                    "analysis": {
                        "description": f"Brief analysis of {self._sensor_name.lower()} conditions",
                        "required": True,
                        "selector": {"text": None}
                    }
                }
            }
            
            # Call AI Task service
            response = await self._hass.services.async_call(
                "ai_task",
                "generate_data",
                {**ai_task_data, "entity_id": self._ai_task},
                blocking=True,
                return_response=True,
            )
            
            if response and "data" in response and "analysis" in response["data"]:
                analysis = response["data"]["analysis"]
                # Ensure we stay under 255 characters
                if len(analysis) > 255:
                    analysis = analysis[:252] + "..."
                self._state = analysis
            else:
                # Fallback to simple status
                status = get_simple_status(sensor_info['name'], sensor_info['raw_value'], sensor_info['unit'], self._aquarium_type)
                self._state = f"{sensor_info['name']} is {status} at {sensor_info['value']}"
                
        except Exception as err:
            _LOGGER.error("Error updating %s analysis sensor: %s", self._sensor_name, err)
            self._state = "Analysis unavailable"
            self._available = False


class AquariumAIOverallAnalysis(AquariumAIBaseSensor):
    """Sensor for overall aquarium analysis."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        ai_task: str,
        frequency_minutes: int,
        sensor_mappings: list,
    ):
        """Initialize the overall analysis sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._ai_task = ai_task
        self._attr_name = f"{tank_name} Overall Analysis"
        self._attr_unique_id = f"{config_entry.entry_id}_overall_analysis"
        self._attr_icon = "mdi:fish"
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get all sensor data
            sensor_data = []
            for sensor_entity, sensor_name in self._sensor_mappings:
                sensor_info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                if sensor_info:
                    sensor_data.append(sensor_info)
            
            if not sensor_data:
                self._state = "No sensor data available"
                self._available = False
                return
                
            self._available = True
            
            # Build conditions string
            conditions_list = [f"- Type: {self._aquarium_type}"]
            for info in sensor_data:
                if info['unit']:
                    conditions_list.append(f"- {info['name']}: {info['raw_value']} {info['unit']}")
                else:
                    conditions_list.append(f"- {info['name']}: {info['raw_value']} (no units)")
            conditions_str = "\n".join(conditions_list)
            
            # Prepare AI Task data for brief overall analysis
            ai_task_data = {
                "task_name": f"{self._tank_name} Overall",
                "instructions": f"""Based on the current conditions:

{conditions_str}

Provide a brief 1-2 sentence overall health assessment of this {self._aquarium_type.lower()} aquarium. Keep response under 200 characters. Focus on overall status and only mention critical issues if any. Always correctly write ph as pH.

IMPORTANT: Pay attention to units when evaluating values:
- Temperature: Consider if values are in Celsius (°C) or Fahrenheit (°F)
- Salinity: Consider if values are in ppt/psu or specific gravity (SG)
- Dissolved Oxygen: Consider if values are in mg/L, ppm, or percentage saturation
- Water Level: Consider if percentages or absolute measurements
- pH: Typically no units (scale 0-14)""",
                "structure": {
                    "analysis": {
                        "description": "Brief overall aquarium health assessment",
                        "required": True,
                        "selector": {"text": None}
                    }
                }
            }
            
            # Call AI Task service
            response = await self._hass.services.async_call(
                "ai_task",
                "generate_data",
                {**ai_task_data, "entity_id": self._ai_task},
                blocking=True,
                return_response=True,
            )
            
            if response and "data" in response and "analysis" in response["data"]:
                analysis = response["data"]["analysis"]
                # Ensure we stay under 255 characters
                if len(analysis) > 255:
                    analysis = analysis[:252] + "..."
                self._state = analysis
            else:
                # Fallback to simple overall status
                self._state = get_overall_status(sensor_data, self._aquarium_type)
                
        except Exception as err:
            _LOGGER.error("Error updating overall analysis sensor: %s", err)
            self._state = "Analysis unavailable"
            self._available = False


class AquariumAISimpleStatus(AquariumAIBaseSensor):
    """Sensor for simple status overview."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        frequency_minutes: int,
        sensor_mappings: list,
    ):
        """Initialize the simple status sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._attr_name = f"{tank_name} Simple Status"
        self._attr_unique_id = f"{config_entry.entry_id}_simple_status"
        self._attr_icon = "mdi:check-circle"
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get all sensor data
            sensor_data = []
            for sensor_entity, sensor_name in self._sensor_mappings:
                sensor_info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                if sensor_info:
                    sensor_data.append(sensor_info)
            
            if not sensor_data:
                self._state = "No sensors configured"
                self._available = False
                return
                
            self._available = True
            
            # Use existing simple status logic
            self._state = get_overall_status(sensor_data, self._aquarium_type)
                
        except Exception as err:
            _LOGGER.error("Error updating simple status sensor: %s", err)
            self._state = "Status unavailable"
            self._available = False