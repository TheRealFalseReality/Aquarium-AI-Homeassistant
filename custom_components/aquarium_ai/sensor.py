"""Sensor platform for Aquarium AI."""
import logging
import re
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_TEMPERATURE_SENSOR, CONF_AQUARIUM_NAME
from .coordinator import AquariumAIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up Aquarium AI sensor platform")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Create temperature analysis sensors (simplified structure)
    temperature_sensor = config_entry.data[CONF_TEMPERATURE_SENSOR]
    _LOGGER.debug("Creating sensors for temperature sensor: %s", temperature_sensor)
    
    # Create the three analysis sensors
    analysis_sensors = [
        "temperature_analysis",
        "overall_analysis", 
        "quick_analysis"
    ]
    
    _LOGGER.debug("Creating analysis sensors: %s", analysis_sensors)

    # Create entities with comprehensive error handling
    for key in analysis_sensors:
        try:
            # Validate the key before creating sensor
            if not key or not isinstance(key, str):
                _LOGGER.error("Invalid key for sensor creation: %s", key)
                continue
                
            sensor = AquariumAIAnalysisSensor(coordinator, key)
            
            # Validate the sensor was created properly
            if not hasattr(sensor, '_attr_unique_id') or not sensor._attr_unique_id:
                _LOGGER.error("Sensor created with invalid unique_id: %s", key)
                continue
                
            if not hasattr(sensor, '_attr_name') or not sensor._attr_name:
                _LOGGER.error("Sensor created with invalid name: %s", key)
                continue
                
            entities.append(sensor)
            _LOGGER.debug("Successfully created sensor: %s with unique_id: %s", sensor.name, sensor.unique_id)
        except Exception as e:
            _LOGGER.error("Failed to create sensor for key %s: %s", key, e, exc_info=True)

    _LOGGER.debug("Adding %d entities to Home Assistant", len(entities))
    if entities:
        async_add_entities(entities, update_before_add=False)
    else:
        _LOGGER.warning("No entities were created for Aquarium AI integration")


class AquariumAIBaseSensor(CoordinatorEntity):
    """Base class for Aquarium AI sensors."""
    def __init__(self, coordinator: AquariumAIDataUpdateCoordinator, context: str):
        super().__init__(coordinator)
        self._context = context
        self._config_entry = coordinator.config_entry
        
        # Create a safe unique ID by sanitizing the context
        safe_context = re.sub(r'[^a-zA-Z0-9_]', '_', context).lower()
        self._attr_unique_id = f"{self._config_entry.entry_id}_{safe_context}"
        
        # Use the aquarium name from config or fallback to default
        aquarium_name = self._config_entry.data.get(CONF_AQUARIUM_NAME, "Aquarium AI")
        
        # All sensors will be part of the same device in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=str(aquarium_name),  # Ensure it's a string
            manufacturer="Aquarium AI",
            entry_type="service",
        )
        
        # Set entity registry options
        self._attr_entity_registry_enabled_default = True
        self._attr_should_poll = False
        
        # Ensure we have safe attributes set
        self._attr_entity_category = None
        self._attr_unit_of_measurement = None

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
        
        # Set a safe initial state to prevent write errors
        self._attr_native_value = "Initializing..."
        
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
                    str_value = str(value).strip()
                    # Ensure it's not empty
                    if not str_value:
                        return "No analysis data"
                    # Limit state length to prevent issues (HA limit is 255 chars)
                    if len(str_value) > 253:
                        str_value = str_value[:250] + "..."
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
            return "Error retrieving data"

    @property
    def available(self):
        """Return True if entity is available."""
        # Always return True to prevent availability issues during entity creation
        return True

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        try:
            attrs = {
                "analysis_key": str(self._analysis_key),
                "integration": "Aquarium AI",
            }
            # Only add optional attributes if they exist and are serializable
            try:
                if hasattr(self.coordinator, 'last_update_success_time') and self.coordinator.last_update_success_time:
                    attrs["last_update"] = self.coordinator.last_update_success_time.isoformat()
            except Exception as e:
                _LOGGER.debug("Could not add last_update attribute: %s", e)
                
            try:
                if hasattr(self.coordinator, 'last_exception') and self.coordinator.last_exception:
                    attrs["last_error"] = str(self.coordinator.last_exception)[:200]  # Limit error message length
            except Exception as e:
                _LOGGER.debug("Could not add last_error attribute: %s", e)
                
            return attrs
        except Exception as e:
            _LOGGER.error("Error getting extra_state_attributes for sensor %s: %s", self._attr_name, e, exc_info=True)
            # Return minimal safe attributes
            return {"analysis_key": str(self._analysis_key)}