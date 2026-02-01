"""Binary sensor platform for Aquarium AI integration."""
import logging
from typing import Optional

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquarium AI binary sensors from a config entry."""
    tank_name = config_entry.data["tank_name"]
    
    entities = []
    
    # Create water change needed binary sensor
    entities.append(
        AquariumAIWaterChangeNeeded(
            hass,
            config_entry,
            tank_name,
        )
    )
    
    # Create AI analysis available binary sensor
    entities.append(
        AquariumAIAnalysisAvailable(
            hass,
            config_entry,
            tank_name,
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


class AquariumAIAnalysisAvailable(BinarySensorEntity):
    """Binary sensor for AI analysis availability status."""
    
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
        self._attr_name = f"{tank_name} AI Analysis Available"
        self._attr_unique_id = f"{config_entry.entry_id}_ai_analysis_available"
        self._attr_icon = "mdi:robot"
        self._attr_device_class = "update"
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
        """Return true if AI analysis is available."""
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
            last_update = shared_data.get("last_update")
            
            # Check if AI analysis is available
            # Must have actual AI-generated content (non-empty dict) and a valid timestamp
            # Empty dict means fallback/no AI, so sensor should be OFF
            if sensor_analysis and len(sensor_analysis) > 0 and last_update is not None:
                self._state = True
                self._available = True
                
                # Add attributes with the last update timestamp
                self._attr_extra_state_attributes = {
                    "last_updated": last_update,
                }
            else:
                # No AI analysis available yet
                self._state = False
                self._available = True
                # Don't include last_updated attribute when no analysis is available
                # to avoid showing "unknown" in the UI
                self._attr_extra_state_attributes = {}
                
        except Exception as err:
            _LOGGER.error("Error updating AI analysis available binary sensor: %s", err)
            self._state = False
            self._available = False
            self._attr_extra_state_attributes = {}
