"""Sensor platform for Aquarium AI."""
import logging
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
            name = state.attributes.get("friendly_name", entity_id).lower().replace(" ", "_")
            response_keys.append(f"{name}_analysis")
            _LOGGER.debug("Added response key: %s for entity %s", f"{name}_analysis", entity_id)

    response_keys.extend(["overall_analysis", "quick_analysis"])
    _LOGGER.debug("Total response keys: %s", response_keys)

    for key in response_keys:
        sensor = AquariumAIAnalysisSensor(coordinator, key)
        entities.append(sensor)
        _LOGGER.debug("Created sensor: %s", sensor.name)

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
            manufacturer="Your Name",
            entry_type="service",
        )

class AquariumAIAnalysisSensor(AquariumAIBaseSensor, SensorEntity):
    """Representation of an Aquarium AI Analysis sensor."""
    def __init__(self, coordinator: AquariumAIDataUpdateCoordinator, analysis_key: str):
        super().__init__(coordinator, context=analysis_key)
        self._analysis_key = analysis_key
        self._attr_name = f"Aquarium AI {analysis_key.replace('_', ' ').title()}"
        _LOGGER.debug("Initialized sensor %s with key: %s", self._attr_name, analysis_key)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self._analysis_key)
            _LOGGER.debug("Sensor %s returning value: %s", self._attr_name, value)
            return value
        _LOGGER.debug("Sensor %s has no coordinator data", self._attr_name)
        return None

    @property
    def available(self):
        """Return True if entity is available."""
        available = self.coordinator.last_update_success
        _LOGGER.debug("Sensor %s availability: %s", self._attr_name, available)
        return available