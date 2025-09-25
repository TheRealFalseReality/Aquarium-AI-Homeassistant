"""Sensor platform for Aquarium AI."""
import logging
import re
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SENSORS, CONF_AQUARIUM_NAME
from .coordinator import AquariumAIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up Aquarium AI sensor platform")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Create Analysis Sensors
    sensor_entities = config_entry.data[CONF_SENSORS]
    _LOGGER.debug("Creating sensors for entities: %s", sensor_entities)
    
    # Generate a list of keys for the expected AI response
    response_keys = []
    for entity_id in sensor_entities:
        state = hass.states.get(entity_id)
        if state:
            # Clean up the name to avoid issues with special characters
            friendly_name = state.attributes.get("friendly_name", entity_id)
            # Create a clean key by removing special characters and replacing spaces
            clean_name = "".join(c for c in friendly_name if c.isalnum() or c in (' ', '_')).replace(' ', '_').lower()
            analysis_key = f"{clean_name}_analysis"
            response_keys.append(analysis_key)
            _LOGGER.debug("Added response key: %s for entity %s (friendly name: %s)", analysis_key, entity_id, friendly_name)

    # Add standard analysis keys
    response_keys.extend(["overall_analysis", "quick_analysis"])
    _LOGGER.debug("Total response keys: %s", response_keys)

    # Create entities with error handling
    for key in response_keys:
        try:
            sensor = AquariumAIAnalysisSensor(coordinator, key)
            entities.append(sensor)
            _LOGGER.debug("Created sensor: %s with unique_id: %s", sensor.name, sensor.unique_id)
        except Exception as e:
            _LOGGER.error("Failed to create sensor for key %s: %s", key, e, exc_info=True)

    _LOGGER.debug("Adding %d entities to Home Assistant", len(entities))
    async_add_entities(entities)


class AquariumAIBaseSensor(CoordinatorEntity):
    """Base class for Aquarium AI sensors."""
    def __init__(self, coordinator: AquariumAIDataUpdateCoordinator, context: str):
        super().__init__(coordinator)
        self._context = context
        self._config_entry = coordinator.config_entry
        self._attr_unique_id = f"{self._config_entry.entry_id}_{self._context}"
        
        # Use the aquarium name from config or fallback to default
        aquarium_name = self._config_entry.data.get(CONF_AQUARIUM_NAME, "Aquarium AI")
        
        # All sensors will be part of the same device in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=aquarium_name,
            manufacturer="Aquarium AI",
            entry_type="service",
        )
        
        # Set entity registry options
        self._attr_entity_registry_enabled_default = True
        self._attr_should_poll = False

class AquariumAIAnalysisSensor(AquariumAIBaseSensor, SensorEntity):
    """Representation of an Aquarium AI Analysis sensor."""
    def __init__(self, coordinator: AquariumAIDataUpdateCoordinator, analysis_key: str):
        super().__init__(coordinator, context=analysis_key)
        self._analysis_key = analysis_key
        
        # Create a cleaner, more readable name
        display_name = analysis_key.replace('_', ' ').title()
        self._attr_name = f"Aquarium AI {display_name}"
        
        # Ensure the entity has a proper state class for text sensors
        self._attr_state_class = None
        self._attr_device_class = None
        self._attr_icon = "mdi:fish"
        
        _LOGGER.debug("Initialized sensor %s with key: %s, unique_id: %s", 
                     self._attr_name, analysis_key, self.unique_id)

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            if self.coordinator.data:
                value = self.coordinator.data.get(self._analysis_key)
                # Ensure the value is a string and not too long for HA state
                if value is not None:
                    str_value = str(value)
                    # Limit state length to prevent issues
                    if len(str_value) > 255:
                        str_value = str_value[:252] + "..."
                    _LOGGER.debug("Sensor %s returning value: %s", self._attr_name, str_value[:50] + "..." if len(str_value) > 50 else str_value)
                    return str_value
                else:
                    _LOGGER.debug("Sensor %s has None value for key %s", self._attr_name, self._analysis_key)
                    return "Waiting for analysis..."
            else:
                _LOGGER.debug("Sensor %s has no coordinator data", self._attr_name)
                return "Waiting for analysis..."
        except Exception as e:
            _LOGGER.error("Error getting native_value for sensor %s: %s", self._attr_name, e, exc_info=True)
            return "Error"

    @property
    def available(self):
        """Return True if entity is available."""
        try:
            # Entity is always available, even if coordinator hasn't updated yet
            return True
        except Exception as e:
            _LOGGER.error("Error checking availability for sensor %s: %s", self._attr_name, e, exc_info=True)
            return False

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        try:
            attrs = {
                "analysis_key": self._analysis_key,
                "integration": "Aquarium AI",
            }
            if self.coordinator.last_update_success_time:
                attrs["last_update"] = self.coordinator.last_update_success_time.isoformat()
            if hasattr(self.coordinator, 'last_exception') and self.coordinator.last_exception:
                attrs["last_error"] = str(self.coordinator.last_exception)
            return attrs
        except Exception as e:
            _LOGGER.error("Error getting extra_state_attributes for sensor %s: %s", self._attr_name, e, exc_info=True)
            return {"analysis_key": self._analysis_key}