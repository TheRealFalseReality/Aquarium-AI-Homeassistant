"""Sensor platform for Aquarium AI."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.trend.sensor import TrendSensor
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SENSORS
from .coordinator import AquariumAIDataUpdateCoordinator

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Create Analysis Sensors
    sensor_entities = config_entry.data[CONF_SENSORS]
    
    # Generate a list of keys for the expected AI response
    response_keys = []
    for entity_id in sensor_entities:
        state = hass.states.get(entity_id)
        if state:
            name = state.attributes.get("friendly_name", entity_id).lower().replace(" ", "_")
            response_keys.append(f"{name}_analysis")

    response_keys.extend(["overall_analysis", "quick_analysis"])

    for key in response_keys:
        entities.append(AquariumAIAnalysisSensor(coordinator, key))

    # Create Trend Sensors for each numeric input sensor
    for entity_id in sensor_entities:
        state = hass.states.get(entity_id)
        if state and state.state not in ["unknown", "unavailable"] and state.state.replace('.', '', 1).isdigit():
            entities.append(AquariumAITrendSensor(hass, config_entry, entity_id))
            entities.append(AquariumAITrendTextSensor(hass, config_entry, entity_id))

    async_add_entities(entities)


class AquariumAIBaseSensor(CoordinatorEntity):
    """Base class for Aquarium AI sensors."""
    def __init__(self, coordinator: AquariumAIDataUpdateCoordinator, context: str):
        super().__init__(coordinator)
        self._context = context
        self._config_entry = coordinator.config_entry
        self._attr_unique_id = f"{self._config_entry.entry_id}_{self._context}"
        
        # All sensors will be part of the same device in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="Aquarium AI",
            manufacturer="Your Name",
            entry_type="service",
        )

class AquariumAIAnalysisSensor(AquariumAIBaseSensor, SensorEntity):
    """Representation of an Aquarium AI Analysis sensor."""
    def __init__(self, coordinator: AquariumAIDataUpdateCoordinator, analysis_key: str):
        super().__init__(coordinator, context=analysis_key)
        self._analysis_key = analysis_key
        self._attr_name = f"Aquarium AI {analysis_key.replace('_', ' ').title()}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._analysis_key)
        return None

# We subclass TrendSensor directly for the binary sensor
class AquariumAITrendSensor(TrendSensor):
    """Trend sensor for an aquarium parameter."""
    def __init__(self, hass, config_entry, sensor_entity_id):
        super().__init__(hass, config_entry.entry_id, sensor_entity_id, None, None, None, None, 0, False)
        self._sensor_entity_id = sensor_entity_id
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_entity_id}_trend"
        self._attr_name = f"{hass.states.get(sensor_entity_id).name} Trend"
        # Link it to the same device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="Aquarium AI",
        )

# For the text version of the trend, we create a new entity
class AquariumAITrendTextSensor(SensorEntity):
    """Text representation of the trend sensor."""
    def __init__(self, hass, config_entry, sensor_entity_id):
        self._hass = hass
        self._trend_entity_id = f"binary_sensor.{hass.states.get(sensor_entity_id).name.lower().replace(' ', '_')}_trend"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_entity_id}_trend_text"
        self._attr_name = f"{hass.states.get(sensor_entity_id).name} Trend Status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="Aquarium AI",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        trend_state = self._hass.states.get(self._trend_entity_id)
        if trend_state is None:
            return "Initializing"
        
        if trend_state.state == 'on':
            return "Rising" if trend_state.attributes.get('gradient', 0) > 0 else "Falling"
        return "Stable"
    
    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True # You might want this to be False by default

    @property
    def should_poll(self) -> bool:
        """This sensor updates when the trend sensor updates."""
        return False

    async def async_added_to_hass(self) -> None:
        """Listen for state changes for the trend sensor."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.helpers.event.async_track_state_change_event(
                self._trend_entity_id, self._on_trend_change
            )
        )
    
    @callback
    def _on_trend_change(self, event):
        """Update the state when the trend sensor changes."""
        self.async_write_ha_state()