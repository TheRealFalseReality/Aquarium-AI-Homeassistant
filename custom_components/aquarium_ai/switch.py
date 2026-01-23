"""Switch platform for Aquarium AI integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_RUN_ANALYSIS_ON_STARTUP,
    CONF_AUTO_NOTIFICATIONS,
    DEFAULT_RUN_ANALYSIS_ON_STARTUP,
    DEFAULT_AUTO_NOTIFICATIONS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquarium AI switches from a config entry."""
    tank_name = config_entry.data["tank_name"]
    
    entities = []
    
    # Create run analysis on startup switch
    entities.append(
        RunAnalysisOnStartupSwitch(
            hass,
            config_entry,
            tank_name,
        )
    )
    # Create auto-send notifications switch
    entities.append(
        AutoNotificationsSwitch(
            hass,
            config_entry,
            tank_name,
        )
    )
    
    async_add_entities(entities)


class RunAnalysisOnStartupSwitch(SwitchEntity):
    """Switch to control whether analysis runs when Home Assistant starts."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
    ):
        """Initialize the switch."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._attr_name = f"{tank_name} Run Analysis on Startup"
        self._attr_unique_id = f"{config_entry.entry_id}_run_analysis_on_startup"
        self._attr_icon = "mdi:play-circle-outline"
        # Get initial state from config, default to False (off)
        self._attr_is_on = config_entry.data.get(
            CONF_RUN_ANALYSIS_ON_STARTUP, DEFAULT_RUN_ANALYSIS_ON_STARTUP
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
    
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        # Update config entry data
        new_data = {**self._config_entry.data, CONF_RUN_ANALYSIS_ON_STARTUP: True}
        self._hass.config_entries.async_update_entry(
            self._config_entry, data=new_data
        )
        
        # Update state after config is updated
        self._attr_is_on = True
        self.async_write_ha_state()
        _LOGGER.info(
            "Startup analysis enabled for %s. Will run on next HA restart.",
            self._tank_name
        )
    
    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        # Update config entry data
        new_data = {**self._config_entry.data, CONF_RUN_ANALYSIS_ON_STARTUP: False}
        self._hass.config_entries.async_update_entry(
            self._config_entry, data=new_data
        )
        
        # Update state after config is updated
        self._attr_is_on = False
        self.async_write_ha_state()
        _LOGGER.info(
            "Startup analysis disabled for %s. Will not run on next HA restart.",
            self._tank_name
        )


class AutoNotificationsSwitch(SwitchEntity):
    """Switch to control automatic notifications."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
    ):
        """Initialize the switch."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._attr_name = f"{tank_name} Auto-send Notifications"
        self._attr_unique_id = f"{config_entry.entry_id}_auto_notifications"
        self._attr_icon = "mdi:bell-ring-outline"
        # Get initial state from config, default to True (on)
        self._attr_is_on = config_entry.data.get(
            CONF_AUTO_NOTIFICATIONS, DEFAULT_AUTO_NOTIFICATIONS
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
    
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        # Update config entry data
        new_data = {**self._config_entry.data, CONF_AUTO_NOTIFICATIONS: True}
        self._hass.config_entries.async_update_entry(
            self._config_entry, data=new_data
        )
        
        # Update state after config is updated
        self._attr_is_on = True
        self.async_write_ha_state()
        _LOGGER.info(
            "Auto-send notifications enabled for %s",
            self._tank_name
        )
    
    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        # Update config entry data
        new_data = {**self._config_entry.data, CONF_AUTO_NOTIFICATIONS: False}
        self._hass.config_entries.async_update_entry(
            self._config_entry, data=new_data
        )
        
        # Update state after config is updated
        self._attr_is_on = False
        self.async_write_ha_state()
        _LOGGER.info(
            "Auto-send notifications disabled for %s",
            self._tank_name
        )

