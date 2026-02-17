"""Binary sensor platform for Aquarium AI integration."""
import logging
from typing import Optional

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
)
from . import get_sensor_info, get_simple_status

_LOGGER = logging.getLogger(__name__)

# Status values that indicate no problem (healthy parameters)
HEALTHY_STATUSES = ["Good", "OK"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquarium AI binary sensors from a config entry."""
    tank_name = config_entry.data[CONF_TANK_NAME]
    aquarium_type = config_entry.data[CONF_AQUARIUM_TYPE]
    
    # Define sensor mappings
    sensor_mappings = [
        (config_entry.data.get(CONF_TEMPERATURE_SENSOR), "Temperature"),
        (config_entry.data.get(CONF_PH_SENSOR), "pH"),
        (config_entry.data.get(CONF_SALINITY_SENSOR), "Salinity"),
        (config_entry.data.get(CONF_DISSOLVED_OXYGEN_SENSOR), "Dissolved Oxygen"),
        (config_entry.data.get(CONF_WATER_LEVEL_SENSOR), "Water Level"),
        (config_entry.data.get(CONF_ORP_SENSOR), "ORP"),
    ]
    
    # Filter out empty sensors
    valid_sensor_mappings = [(entity, name) for entity, name in sensor_mappings if entity]
    
    entities = []
    
    # Create water change needed binary sensor
    entities.append(
        AquariumAIWaterChangeNeeded(
            hass,
            config_entry,
            tank_name,
        )
    )
    
    # Create parameter problem binary sensors for each configured sensor
    for sensor_entity, sensor_name in valid_sensor_mappings:
        entities.append(
            AquariumAIParameterProblem(
                hass,
                config_entry,
                tank_name,
                aquarium_type,
                sensor_entity,
                sensor_name,
            )
        )
    
    async_add_entities(entities)


class AquariumAIWaterChangeNeeded(BinarySensorEntity):
    """Binary sensor for water change needed status."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
    ):
        """Initialize the binary sensor."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._attr_name = f"{tank_name} Water Change Needed"
        self._attr_unique_id = f"{config_entry.entry_id}_water_change_needed"
        self._attr_icon = "mdi:water-alert"
        self._attr_device_class = "problem"
        self._state = False
        self._available = True
        self._attr_extra_state_attributes = {}
        
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        # Initial update
        await self.async_update()
        
    def _get_shared_data(self):
        """Get shared analysis data from the integration."""
        if DOMAIN in self._hass.data and self._config_entry.entry_id in self._hass.data[DOMAIN]:
            entry_data = self._hass.data[DOMAIN][self._config_entry.entry_id]
            return {
                "sensor_analysis": entry_data.get("sensor_analysis", {}),
                "last_update": entry_data.get("last_update")
            }
        return {"sensor_analysis": {}, "last_update": None}
    
    @property
    def is_on(self) -> bool:
        """Return true if water change is needed."""
        return self._state
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
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
        
    async def async_update(self) -> None:
        """Update the binary sensor."""
        try:
            # Get shared analysis data
            shared_data = self._get_shared_data()
            sensor_analysis = shared_data["sensor_analysis"]
            
            if "water_change_recommended" in sensor_analysis and sensor_analysis["water_change_recommended"]:
                recommendation = sensor_analysis["water_change_recommended"]
                # Check if recommendation starts with "Yes"
                self._state = recommendation.lower().startswith("yes")
                self._available = True
                
                # Add attributes with the full recommendation text
                self._attr_extra_state_attributes = {
                    "recommendation": recommendation,
                    "last_updated": shared_data.get("last_update"),
                }
            else:
                # No analysis available yet
                self._state = False
                self._available = True
                self._attr_extra_state_attributes = {
                    "recommendation": "No analysis available yet",
                }
                
        except Exception as err:
            _LOGGER.error("Error updating water change needed binary sensor: %s", err)
            self._state = False
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAIParameterProblem(BinarySensorEntity):
    """Binary sensor for individual parameter problem detection."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        sensor_entity: str,
        sensor_name: str,
    ):
        """Initialize the parameter problem binary sensor."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._aquarium_type = aquarium_type
        self._sensor_entity = sensor_entity
        self._sensor_name = sensor_name
        self._attr_name = f"{tank_name} {sensor_name} Problem"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_name.lower().replace(' ', '_')}_problem"
        self._attr_icon = self._get_sensor_icon(sensor_name)
        self._attr_device_class = "problem"
        self._state = False
        self._available = True
        self._attr_extra_state_attributes = {}
        
    def _get_sensor_icon(self, sensor_name: str) -> str:
        """Get appropriate icon for sensor type."""
        sensor_icons = {
            "Temperature": "mdi:thermometer-alert",
            "pH": "mdi:ph",
            "Salinity": "mdi:shaker-outline",
            "Dissolved Oxygen": "mdi:air-purifier",
            "Water Level": "mdi:waves-arrow-up",
            "ORP": "mdi:lightning-bolt-circle",
        }
        return sensor_icons.get(sensor_name, "mdi:alert-circle")
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        # Initial update
        await self.async_update()
        
    @property
    def is_on(self) -> bool:
        """Return true if parameter has a problem."""
        return self._state
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
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
        
    async def async_update(self) -> None:
        """Update the binary sensor."""
        try:
            # Get sensor info
            sensor_info = get_sensor_info(self._hass, self._sensor_entity, self._sensor_name)
            if not sensor_info:
                self._state = False
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Get simple status
            status = get_simple_status(
                sensor_info['name'], 
                sensor_info['raw_value'], 
                sensor_info['unit'], 
                self._aquarium_type
            )
            
            # Set state to True (problem) if status is NOT "Good" or "OK"
            # Problem statuses include: "Check", "Adjust", "Low", "High", "Unavailable", etc.
            self._state = status not in HEALTHY_STATUSES
            
            # Add sensor data as attributes
            self._attr_extra_state_attributes = {
                "status": status,
                "sensor_value": sensor_info['value'],
                "raw_value": sensor_info['raw_value'],
                "unit": sensor_info['unit'],
                "sensor_name": sensor_info['name'],
                "source_entity": self._sensor_entity,
            }
                
        except Exception as err:
            _LOGGER.error("Error updating %s problem binary sensor: %s", self._sensor_name, err)
            self._state = False
            self._available = False
            self._attr_extra_state_attributes = {}

