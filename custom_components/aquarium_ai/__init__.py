"""The Aquarium AI integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, CONF_TANK_NAME, CONF_TEMPERATURE_SENSOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aquarium AI from a config entry."""
    _LOGGER.info("Setting up Aquarium AI integration")
    
    tank_name = entry.data[CONF_TANK_NAME]
    temp_sensor = entry.data[CONF_TEMPERATURE_SENSOR]
    
    async def send_temperature_notification(now):
        """Send a notification with the current temperature."""
        try:
            sensor_state = hass.states.get(temp_sensor)
            if sensor_state and sensor_state.state not in ["unknown", "unavailable"]:
                temp_value = sensor_state.state
                unit = sensor_state.attributes.get("unit_of_measurement", "")
                
                message = f"{tank_name}: Current temperature is {temp_value}{unit}"
                
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": f"🐠 {tank_name} Temperature Update",
                        "message": message,
                        "notification_id": f"aquarium_ai_{entry.entry_id}",
                    },
                )
                _LOGGER.info("Sent temperature notification: %s", message)
            else:
                _LOGGER.warning("Temperature sensor %s is unavailable", temp_sensor)
        except Exception as err:
            _LOGGER.error("Error sending temperature notification: %s", err)
    
    # Store the data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "tank_name": tank_name,
        "temp_sensor": temp_sensor,
    }
    
    # Send initial notification
    await send_temperature_notification(None)
    
    # Schedule hourly notifications
    unsub = async_track_time_interval(
        hass, send_temperature_notification, timedelta(hours=1)
    )
    
    # Store the unsubscribe function
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Aquarium AI integration")
    
    # Cancel the scheduled notifications
    if entry.entry_id in hass.data[DOMAIN]:
        unsub = hass.data[DOMAIN][entry.entry_id].get("unsub")
        if unsub:
            unsub()
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return True