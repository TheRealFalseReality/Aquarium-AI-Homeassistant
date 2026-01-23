"""Select platform for Aquarium AI integration."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_UPDATE_FREQUENCY,
    CONF_NOTIFICATION_FORMAT,
    DEFAULT_FREQUENCY,
    DEFAULT_NOTIFICATION_FORMAT,
    UPDATE_FREQUENCIES,
    NOTIFICATION_FORMATS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquarium AI select entities from a config entry."""
    tank_name = config_entry.data["tank_name"]
    
    entities = []
    
    # Create update frequency selector
    entities.append(
        UpdateFrequencySelect(
            hass,
            config_entry,
            tank_name,
        )
    )
    
    # Create notification format selector
    entities.append(
        NotificationFormatSelect(
            hass,
            config_entry,
            tank_name,
        )
    )
    
    async_add_entities(entities)


class UpdateFrequencySelect(SelectEntity):
    """Select entity for controlling update frequency."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
    ):
        """Initialize the select entity."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._attr_name = f"{tank_name} Update Frequency"
        self._attr_unique_id = f"{config_entry.entry_id}_update_frequency"
        self._attr_icon = "mdi:clock-outline"
        
        # Set options based on UPDATE_FREQUENCIES keys
        self._attr_options = list(UPDATE_FREQUENCIES.keys())
        
        # Get initial value from config
        self._attr_current_option = config_entry.data.get(
            CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY
        )
        
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
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Update config entry data
        new_data = {**self._config_entry.data, CONF_UPDATE_FREQUENCY: option}
        self._hass.config_entries.async_update_entry(
            self._config_entry, data=new_data
        )
        
        # Update state
        self._attr_current_option = option
        self.async_write_ha_state()
        
        # Request integration reload to apply new frequency
        _LOGGER.info(
            "Update frequency changed to %s for %s. Reloading integration...",
            option,
            self._tank_name
        )
        await self._hass.config_entries.async_reload(self._config_entry.entry_id)


class NotificationFormatSelect(SelectEntity):
    """Select entity for controlling notification format."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
    ):
        """Initialize the select entity."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._attr_name = f"{tank_name} Notification Format"
        self._attr_unique_id = f"{config_entry.entry_id}_notification_format"
        self._attr_icon = "mdi:format-text"
        
        # Set options based on NOTIFICATION_FORMATS keys
        self._attr_options = list(NOTIFICATION_FORMATS.keys())
        
        # Get initial value from config
        self._attr_current_option = config_entry.data.get(
            CONF_NOTIFICATION_FORMAT, DEFAULT_NOTIFICATION_FORMAT
        )
        
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
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Update config entry data
        new_data = {**self._config_entry.data, CONF_NOTIFICATION_FORMAT: option}
        self._hass.config_entries.async_update_entry(
            self._config_entry, data=new_data
        )
        
        # Update state
        self._attr_current_option = option
        self.async_write_ha_state()
        
        _LOGGER.info(
            "Notification format changed to %s for %s",
            option,
            self._tank_name
        )
