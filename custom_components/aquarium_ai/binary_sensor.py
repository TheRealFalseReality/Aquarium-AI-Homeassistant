"""Binary sensor platform for Aquarium AI."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_SENSORS


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the binary sensor platform."""
    entities = []
    
    # Create Trend Binary Sensors for each numeric input sensor
    sensor_entities = config_entry.data[CONF_SENSORS]
    for entity_id in sensor_entities:
        state = hass.states.get(entity_id)
        if state and state.state not in ["unknown", "unavailable"] and state.state.replace('.', '', 1).isdigit():
            entities.append(AquariumAITrendSensor(hass, config_entry, entity_id))

    async_add_entities(entities)


class AquariumAITrendSensor(BinarySensorEntity):
    """Trend sensor for an aquarium parameter."""
    def __init__(self, hass, config_entry, sensor_entity_id):
        self._hass = hass
        self._sensor_entity_id = sensor_entity_id
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_entity_id}_trend"
        sensor_state = hass.states.get(sensor_entity_id)
        sensor_name = sensor_state.attributes.get("friendly_name", sensor_entity_id) if sensor_state else sensor_entity_id
        self._attr_name = f"{sensor_name} Trend"
        # Link it to the same device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="Aquarium AI",
        )
        self._previous_values = []
        self._attr_is_on = False
        
    @property
    def is_on(self):
        """Return true if the trend is rising or falling."""
        return self._attr_is_on
        
    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False
    
    async def async_added_to_hass(self) -> None:
        """Listen for state changes."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.helpers.event.async_track_state_change_event(
                self._sensor_entity_id, self._on_sensor_change
            )
        )
    
    @callback
    def _on_sensor_change(self, event):
        """Handle sensor state changes."""
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
                        self._attr_is_on = True
                    elif recent[2] < recent[0] - 0.1:  # Falling  
                        self._attr_is_on = True
                    else:  # Stable
                        self._attr_is_on = False
                else:
                    self._attr_is_on = False
                    
                self.async_write_ha_state()
            except (ValueError, TypeError):
                pass