"""Sensor platform for Aquarium AI integration."""
import logging
from datetime import timedelta
from typing import Optional

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
    CONF_ORP_SENSOR,
    CONF_CAMERA,
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
        (config_entry.data.get(CONF_ORP_SENSOR), "ORP"),
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
    
    # Create status emoji sensor (extracts emoji from simple status)
    entities.append(
        AquariumAIStatusEmoji(
            hass,
            config_entry,
            tank_name,
            aquarium_type,
            frequency_minutes,
            valid_sensor_mappings,
        )
    )
    
    # Create parameter status sensors for each sensor
    for sensor_entity, sensor_name in valid_sensor_mappings:
        entities.append(
            AquariumAIParameterStatus(
                hass,
                config_entry,
                tank_name,
                aquarium_type,
                sensor_entity,
                sensor_name,
                frequency_minutes,
                valid_sensor_mappings,
            )
        )
    
    # Create quick status sensor (short version of overall status)
    entities.append(
        AquariumAIQuickStatus(
            hass,
            config_entry,
            tank_name,
            aquarium_type,
            frequency_minutes,
            valid_sensor_mappings,
        )
    )
    
    # Create water change recommendation sensor
    entities.append(
        AquariumAIWaterChangeRecommendation(
            hass,
            config_entry,
            tank_name,
            aquarium_type,
            ai_task,
            frequency_minutes,
            valid_sensor_mappings,
        )
    )
    
    # Create camera visual analysis sensor (only if camera is configured)
    camera = config_entry.data.get(CONF_CAMERA)
    if camera:
        entities.append(
            AquariumAICameraAnalysis(
                hass,
                config_entry,
                tank_name,
                aquarium_type,
                camera,
                ai_task,
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
        frequency_minutes: Optional[int],
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
                "sensor_data": entry_data.get("sensor_data", []),
                "last_update": entry_data.get("last_update")
            }
        return {"sensor_analysis": {}, "sensor_data": [], "last_update": None}
        
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
        frequency_minutes: Optional[int],
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
        self._attr_extra_state_attributes = {}
        
    def _get_sensor_icon(self, sensor_name: str) -> str:
        """Get appropriate icon for sensor type."""
        sensor_icons = {
            "Temperature": "mdi:thermometer",
            "pH": "mdi:ph", 
            "Salinity": "mdi:shaker-outline",
            "Dissolved Oxygen": "mdi:air-purifier",
            "Water Level": "mdi:waves",
            "ORP": "mdi:lightning-bolt",
        }
        return sensor_icons.get(sensor_name, "mdi:chart-line")
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get sensor info to check availability
            sensor_info = get_sensor_info(self._hass, self._sensor_entity, self._sensor_name)
            if not sensor_info:
                self._state = "Sensor unavailable"
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Get shared analysis data
            shared_data = self._get_shared_data()
            sensor_analysis = shared_data["sensor_analysis"]
            
            # Look for analysis data for this specific sensor
            analysis_key = f"{self._sensor_name.lower().replace(' ', '_')}_analysis"
            
            if analysis_key in sensor_analysis and sensor_analysis[analysis_key]:
                # Use the AI analysis from the shared update
                self._state = sensor_analysis[analysis_key]
                analysis_source = "AI"
            else:
                # Fallback to simple status if no AI analysis available
                status = get_simple_status(sensor_info['name'], sensor_info['raw_value'], sensor_info['unit'], self._aquarium_type)
                self._state = f"{sensor_info['name']} is {status} at {sensor_info['value']}"
                analysis_source = "Fallback"
            
            # Add attributes with sensor info and analysis metadata
            self._attr_extra_state_attributes = {
                "sensor_name": sensor_info['name'],
                "sensor_value": sensor_info['value'],
                "raw_value": sensor_info['raw_value'],
                "unit": sensor_info['unit'],
                "source_entity": self._sensor_entity,
                "analysis_source": analysis_source,
                "aquarium_type": self._aquarium_type,
                "last_updated": shared_data.get("last_update"),
            }
                
        except Exception as err:
            _LOGGER.error("Error updating %s analysis sensor: %s", self._sensor_name, err)
            self._state = "Analysis unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAIOverallAnalysis(AquariumAIBaseSensor):
    """Sensor for overall aquarium analysis."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        ai_task: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the overall analysis sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._ai_task = ai_task
        self._attr_name = f"{tank_name} Overall Analysis"
        self._attr_unique_id = f"{config_entry.entry_id}_overall_analysis"
        self._attr_icon = "mdi:fish"
        self._attr_extra_state_attributes = {}
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get all sensor data to check availability
            sensor_data = []
            for sensor_entity, sensor_name in self._sensor_mappings:
                sensor_info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                if sensor_info:
                    sensor_data.append(sensor_info)
            
            if not sensor_data:
                self._state = "No sensor data available"
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Get shared analysis data
            shared_data = self._get_shared_data()
            sensor_analysis = shared_data["sensor_analysis"]
            
            if "overall_analysis" in sensor_analysis and sensor_analysis["overall_analysis"]:
                # Use the AI analysis from the shared update
                self._state = sensor_analysis["overall_analysis"]
                analysis_source = "AI"
            else:
                # Fallback to simple overall status
                self._state = get_overall_status(sensor_data, self._aquarium_type)
                analysis_source = "Fallback"
            
            # Add attributes with all sensor information
            sensors_info = {}
            for info in sensor_data:
                sensors_info[info['name']] = {
                    "value": info['value'],
                    "raw_value": info['raw_value'],
                    "unit": info['unit'],
                    "status": get_simple_status(info['name'], info['raw_value'], info['unit'], self._aquarium_type)
                }
            
            self._attr_extra_state_attributes = {
                "sensors": sensors_info,
                "total_sensors": len(sensor_data),
                "aquarium_type": self._aquarium_type,
                "analysis_source": analysis_source,
                "last_updated": shared_data.get("last_update"),
                "ai_task": self._ai_task,
            }
                
        except Exception as err:
            _LOGGER.error("Error updating overall analysis sensor: %s", err)
            self._state = "Analysis unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAISimpleStatus(AquariumAIBaseSensor):
    """Sensor for simple status overview."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the simple status sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._attr_name = f"{tank_name} Simple Status"
        self._attr_unique_id = f"{config_entry.entry_id}_simple_status"
        self._attr_icon = "mdi:check-circle"
        self._attr_extra_state_attributes = {}
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Try to get shared sensor data first (more efficient)
            shared_data = self._get_shared_data()
            sensor_data = shared_data["sensor_data"]
            
            # If no shared data, get fresh sensor data
            if not sensor_data:
                sensor_data = []
                for sensor_entity, sensor_name in self._sensor_mappings:
                    sensor_info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                    if sensor_info:
                        sensor_data.append(sensor_info)
            
            if not sensor_data:
                self._state = "No sensors configured"
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Use existing simple status logic
            self._state = get_overall_status(sensor_data, self._aquarium_type)
            
            # Collect individual sensor statuses for attributes
            individual_statuses = {}
            statuses = []
            for info in sensor_data:
                status = get_simple_status(info['name'], info['raw_value'], info['unit'], self._aquarium_type)
                individual_statuses[info['name']] = {
                    "status": status,
                    "value": info['value'],
                    "unit": info['unit']
                }
                statuses.append(status)
            
            # Calculate status distribution
            good_count = statuses.count("Good")
            ok_count = statuses.count("OK")
            problem_count = len([s for s in statuses if s in ["Check", "Adjust", "Low", "High"]])
            
            self._attr_extra_state_attributes = {
                "individual_statuses": individual_statuses,
                "status_summary": {
                    "good": good_count,
                    "ok": ok_count,
                    "problems": problem_count,
                    "total": len(statuses)
                },
                "aquarium_type": self._aquarium_type,
                "last_updated": shared_data.get("last_update"),
            }
                
        except Exception as err:
            _LOGGER.error("Error updating simple status sensor: %s", err)
            self._state = "Status unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAIStatusEmoji(AquariumAIBaseSensor):
    """Sensor for status emoji (extracted from simple status)."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the status emoji sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._attr_name = f"{tank_name} Status Emoji"
        self._attr_unique_id = f"{config_entry.entry_id}_status_emoji"
        self._attr_icon = "mdi:emoticon-happy-outline"
        self._attr_extra_state_attributes = {}
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Try to get shared sensor data first (more efficient)
            shared_data = self._get_shared_data()
            sensor_data = shared_data["sensor_data"]
            
            # If no shared data, get fresh sensor data
            if not sensor_data:
                sensor_data = []
                for sensor_entity, sensor_name in self._sensor_mappings:
                    sensor_info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                    if sensor_info:
                        sensor_data.append(sensor_info)
            
            if not sensor_data:
                self._state = "❓"
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Use existing simple status logic to get the full status message
            full_status = get_overall_status(sensor_data, self._aquarium_type)
            
            # Extract emoji from the status message
            # The emoji is always at the end of the message
            emoji_map = {
                "🌟": "Excellent",
                "👍": "Great", 
                "👌": "Good",
                "⚠️": "OK",
                "🚨": "Needs Attention"
            }
            
            # Extract the emoji by finding it in the message
            extracted_emoji = "❓"  # Default if no emoji found
            for emoji, status_text in emoji_map.items():
                if emoji in full_status:
                    extracted_emoji = emoji
                    break
            
            self._state = extracted_emoji
            
            # Collect individual sensor statuses for context
            individual_statuses = {}
            statuses = []
            for info in sensor_data:
                status = get_simple_status(info['name'], info['raw_value'], info['unit'], self._aquarium_type)
                individual_statuses[info['name']] = {
                    "status": status,
                    "value": info['value'],
                    "unit": info['unit']
                }
                statuses.append(status)
            
            # Calculate status distribution
            good_count = statuses.count("Good")
            ok_count = statuses.count("OK")
            problem_count = len([s for s in statuses if s in ["Check", "Adjust", "Low", "High"]])
            
            self._attr_extra_state_attributes = {
                "full_status_message": full_status,
                "status_summary": {
                    "good": good_count,
                    "ok": ok_count,
                    "problems": problem_count,
                    "total": len(statuses)
                },
                "aquarium_type": self._aquarium_type,
                "last_updated": shared_data.get("last_update"),
            }
                
        except Exception as err:
            _LOGGER.error("Error updating status emoji sensor: %s", err)
            self._state = "❓"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAIParameterStatus(AquariumAIBaseSensor):
    """Sensor for individual parameter status (Good/OK/Check)."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        sensor_entity: str,
        sensor_name: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the parameter status sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._sensor_entity = sensor_entity
        self._sensor_name = sensor_name
        self._attr_name = f"{tank_name} {sensor_name} Status"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_name.lower().replace(' ', '_')}_status"
        self._attr_icon = self._get_sensor_icon(sensor_name)
        self._attr_extra_state_attributes = {}
        
    def _get_sensor_icon(self, sensor_name: str) -> str:
        """Get appropriate icon for sensor type."""
        sensor_icons = {
            "Temperature": "mdi:thermometer",
            "pH": "mdi:ph", 
            "Salinity": "mdi:shaker-outline",
            "Dissolved Oxygen": "mdi:air-purifier",
            "Water Level": "mdi:waves",
            "ORP": "mdi:lightning-bolt",
        }
        return sensor_icons.get(sensor_name, "mdi:chart-line")
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get sensor info
            sensor_info = get_sensor_info(self._hass, self._sensor_entity, self._sensor_name)
            if not sensor_info:
                self._state = "Unavailable"
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Get simple status
            status = get_simple_status(sensor_info['name'], sensor_info['raw_value'], sensor_info['unit'], self._aquarium_type)
            self._state = status  # Only the status (Good, OK, Check, etc.)
            
            # Add sensor data as attributes
            self._attr_extra_state_attributes = {
                "sensor_value": sensor_info['value'],
                "raw_value": sensor_info['raw_value'],
                "unit": sensor_info['unit'],
                "sensor_name": sensor_info['name'],
                "source_entity": self._sensor_entity,
            }
                
        except Exception as err:
            _LOGGER.error("Error updating %s status sensor: %s", self._sensor_name, err)
            self._state = "Status unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAIQuickStatus(AquariumAIBaseSensor):
    """Sensor for quick status overview (one or two words)."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the quick status sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._attr_name = f"{tank_name} Quick Status"
        self._attr_unique_id = f"{config_entry.entry_id}_quick_status"
        self._attr_icon = "mdi:speedometer"
        self._attr_extra_state_attributes = {}
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Try to get shared sensor data first (more efficient)
            shared_data = self._get_shared_data()
            sensor_data = shared_data["sensor_data"]
            
            # If no shared data, get fresh sensor data
            if not sensor_data:
                sensor_data = []
                for sensor_entity, sensor_name in self._sensor_mappings:
                    sensor_info = get_sensor_info(self._hass, sensor_entity, sensor_name)
                    if sensor_info:
                        sensor_data.append(sensor_info)
            
            if not sensor_data:
                self._state = "No Data"
                self._available = False
                self._attr_extra_state_attributes = {}
                return
                
            self._available = True
            
            # Collect all individual sensor statuses
            statuses = []
            sensor_details = {}
            for info in sensor_data:
                status = get_simple_status(info['name'], info['raw_value'], info['unit'], self._aquarium_type)
                statuses.append(status)
                sensor_details[info['name']] = {
                    "status": status,
                    "value": info['value'],
                    "raw_value": info['raw_value'],
                    "unit": info['unit']
                }
            
            # Count different status types
            good_count = statuses.count("Good")
            ok_count = statuses.count("OK") 
            problem_count = len([s for s in statuses if s in ["Check", "Adjust", "Low", "High"]])
            
            total_sensors = len(statuses)
            
            # Determine quick status based on sensor status distribution
            if good_count == total_sensors:
                self._state = "Excellent"
                status_level = 5
            elif good_count >= total_sensors * 0.75:  # 75% or more good
                self._state = "Great"
                status_level = 4
            elif (good_count + ok_count) >= total_sensors * 0.8:  # 80% or more good/ok
                self._state = "Good"
                status_level = 3
            elif problem_count <= total_sensors * 0.4:  # Less than 40% problems
                self._state = "OK"
                status_level = 2
            else:
                self._state = "Needs Attention"
                status_level = 1
            
            # Add comprehensive attributes
            self._attr_extra_state_attributes = {
                "sensor_details": sensor_details,
                "status_counts": {
                    "good": good_count,
                    "ok": ok_count,
                    "problems": problem_count,
                    "total": total_sensors
                },
                "status_percentages": {
                    "good_percent": round((good_count / total_sensors) * 100, 1) if total_sensors > 0 else 0,
                    "ok_percent": round((ok_count / total_sensors) * 100, 1) if total_sensors > 0 else 0,
                    "problem_percent": round((problem_count / total_sensors) * 100, 1) if total_sensors > 0 else 0
                },
                "status_level": status_level,
                "aquarium_type": self._aquarium_type,
                "last_updated": shared_data.get("last_update"),
            }
                
        except Exception as err:
            _LOGGER.error("Error updating quick status sensor: %s", err)
            self._state = "Unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAIWaterChangeRecommendation(AquariumAIBaseSensor):
    """Sensor for water change recommendation."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        ai_task: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the water change recommendation sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._ai_task = ai_task
        self._attr_name = f"{tank_name} Water Change Recommendation"
        self._attr_unique_id = f"{config_entry.entry_id}_water_change_recommendation"
        self._attr_icon = "mdi:water-sync"
        self._attr_extra_state_attributes = {}
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get shared analysis data
            shared_data = self._get_shared_data()
            sensor_analysis = shared_data["sensor_analysis"]
            
            if "water_change_recommended" in sensor_analysis and sensor_analysis["water_change_recommended"]:
                # Use the brief recommendation from the shared update
                self._state = sensor_analysis["water_change_recommended"]
                self._available = True
                
                # Add attributes
                self._attr_extra_state_attributes = {
                    "aquarium_type": self._aquarium_type,
                    "last_updated": shared_data.get("last_update"),
                    "ai_task": self._ai_task,
                }
            else:
                # No analysis available yet
                self._state = "No analysis available"
                self._available = True
                self._attr_extra_state_attributes = {}
                
        except Exception as err:
            _LOGGER.error("Error updating water change recommendation sensor: %s", err)
            self._state = "Analysis unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}


class AquariumAICameraAnalysis(AquariumAIBaseSensor):
    """Sensor for camera visual analysis."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
        aquarium_type: str,
        camera: str,
        ai_task: str,
        frequency_minutes: Optional[int],
        sensor_mappings: list,
    ):
        """Initialize the camera analysis sensor."""
        super().__init__(hass, config_entry, tank_name, aquarium_type, frequency_minutes, sensor_mappings)
        self._camera = camera
        self._ai_task = ai_task
        self._attr_name = f"{tank_name} Camera Analysis"
        self._attr_unique_id = f"{config_entry.entry_id}_camera_analysis"
        self._attr_icon = "mdi:camera"
        self._attr_extra_state_attributes = {}
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr_extra_state_attributes
        
    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Get shared analysis data
            shared_data = self._get_shared_data()
            sensor_analysis = shared_data["sensor_analysis"]
            
            if "camera_visual_analysis" in sensor_analysis and sensor_analysis["camera_visual_analysis"]:
                # Use the brief camera analysis from the shared update
                self._state = sensor_analysis["camera_visual_analysis"]
                self._available = True
                
                # Add attributes
                self._attr_extra_state_attributes = {
                    "camera_entity": self._camera,
                    "aquarium_type": self._aquarium_type,
                    "last_updated": shared_data.get("last_update"),
                    "ai_task": self._ai_task,
                }
            else:
                # No analysis available yet
                self._state = "No camera analysis available"
                self._available = True
                self._attr_extra_state_attributes = {
                    "camera_entity": self._camera,
                }
                
        except Exception as err:
            _LOGGER.error("Error updating camera analysis sensor: %s", err)
            self._state = "Analysis unavailable"
            self._available = False
            self._attr_extra_state_attributes = {}