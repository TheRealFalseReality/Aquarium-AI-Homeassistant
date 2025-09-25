"""Sensor platform for Aquarium AI."""
from homeassistant.components.sensor import SensorEntity
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

    # Create Trend Text Sensors for each numeric input sensor  
    for entity_id in sensor_entities:
        state = hass.states.get(entity_id)
        if state and state.state not in ["unknown", "unavailable"] and state.state.replace('.', '', 1).isdigit():
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

# For the text version of the trend, we create a new entity
class AquariumAITrendTextSensor(SensorEntity):
    """Text representation of the trend sensor."""
    def __init__(self, hass, config_entry, sensor_entity_id):
        self._hass = hass
        self._sensor_entity_id = sensor_entity_id
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_entity_id}_trend_text"
        sensor_state = hass.states.get(sensor_entity_id)
        sensor_name = sensor_state.attributes.get("friendly_name", sensor_entity_id) if sensor_state else sensor_entity_id
        self._attr_name = f"{sensor_name} Trend Status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="Aquarium AI",
        )
        self._previous_values = []
        self._attr_native_value = "Stable"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._attr_native_value
    
    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True

    @property
    def should_poll(self) -> bool:
        """This sensor updates when the source sensor updates."""
        return False

    async def async_added_to_hass(self) -> None:
        """Listen for state changes for the source sensor."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.helpers.event.async_track_state_change_event(
                self._sensor_entity_id, self._on_sensor_change
            )
        )
    
    @callback
    def _on_sensor_change(self, event):
        """Update the trend status when the source sensor changes."""
        new_state = event.data.get("new_state")
        if new_state and new_state.state not in ["unknown", "unavailable"]:
            try:
                value = float(new_state.state)
                self._previous_values.append(value)
                # Keep only the last 10 values for trend calculation
                if len(self._previous_values) > 10:
                    self._previous_values.pop(0)
                
                # Simple trend detection: compare recent values
                if len(self._previous_values) >= 3:
                    recent = self._previous_values[-3:]
                    if recent[2] > recent[0] + 0.1:  # Rising
                        self._attr_native_value = "Rising"
                    elif recent[2] < recent[0] - 0.1:  # Falling  
                        self._attr_native_value = "Falling"
                    else:  # Stable
                        self._attr_native_value = "Stable"
                else:
                    self._attr_native_value = "Stable"
                    
                self.async_write_ha_state()
            except (ValueError, TypeError):
                pass