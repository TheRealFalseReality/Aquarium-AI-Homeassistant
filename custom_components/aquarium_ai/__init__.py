"""The Aquarium AI integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, 
    CONF_TANK_NAME, 
    CONF_AQUARIUM_TYPE, 
    CONF_TEMPERATURE_SENSOR,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_FREQUENCY,
    UPDATE_FREQUENCIES,
)

_LOGGER = logging.getLogger(__name__)

# Service schema
RUN_ANALYSIS_SCHEMA = vol.Schema({
    vol.Required("config_entry_id"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aquarium AI from a config entry."""
    _LOGGER.info("Setting up Aquarium AI integration")
    
    tank_name = entry.data[CONF_TANK_NAME]
    aquarium_type = entry.data[CONF_AQUARIUM_TYPE]
    temp_sensor = entry.data[CONF_TEMPERATURE_SENSOR]
    frequency_key = entry.data.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY)
    frequency_minutes = UPDATE_FREQUENCIES.get(frequency_key, 60)
    
    async def send_ai_temperature_analysis(now):
        """Send an AI analysis notification about the current temperature."""
        try:
            sensor_state = hass.states.get(temp_sensor)
            if sensor_state and sensor_state.state not in ["unknown", "unavailable"]:
                temp_value = sensor_state.state
                unit = sensor_state.attributes.get("unit_of_measurement", "")
                
                # Prepare AI Task data
                ai_task_data = {
                    "task_name": tank_name,
                    "instructions": f"""Based on the current conditions:

- Type: {aquarium_type}
- Temperature: {temp_value}{unit}

Analyze my aquarium's temperature conditions and provide recommendations if needed. Focus specifically on the temperature aspect for this {aquarium_type.lower()} aquarium.""",
                    "structure": {
                        "temperature_analysis": {
                            "description": "An analysis of the aquarium's temperature conditions with recommendations.",
                            "required": True,
                            "selector": {"text": None}
                        }
                    }
                }
                
                # Call AI Task service
                _LOGGER.debug("Calling AI Task service with data: %s", ai_task_data)
                response = await hass.services.async_call(
                    "ai_task",
                    "generate_data",
                    ai_task_data,
                    blocking=True,
                    return_response=True,
                )
                
                # Extract the AI analysis
                ai_analysis = "No analysis available"
                if response and "data" in response:
                    ai_data = response["data"]
                    if "temperature_analysis" in ai_data:
                        ai_analysis = ai_data["temperature_analysis"]
                
                # Send notification with AI analysis
                message = f"🌡️ Temperature: {temp_value}{unit}\n\n🤖 AI Analysis:\n{ai_analysis}"
                
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": f"🐠 {tank_name} AI Temperature Analysis",
                        "message": message,
                        "notification_id": f"aquarium_ai_{entry.entry_id}",
                    },
                )
                _LOGGER.info("Sent AI temperature analysis notification for %s", tank_name)
            else:
                _LOGGER.warning("Temperature sensor %s is unavailable", temp_sensor)
        except Exception as err:
            _LOGGER.error("Error sending AI temperature analysis: %s", err)
            # Fallback to simple notification if AI fails
            try:
                sensor_state = hass.states.get(temp_sensor)
                if sensor_state and sensor_state.state not in ["unknown", "unavailable"]:
                    temp_value = sensor_state.state
                    unit = sensor_state.attributes.get("unit_of_measurement", "")
                    
                    message = f"Temperature: {temp_value}{unit}\n\n(AI analysis temporarily unavailable)"
                    
                    await hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": f"🐠 {tank_name} Temperature Update",
                            "message": message,
                            "notification_id": f"aquarium_ai_{entry.entry_id}",
                        },
                    )
            except Exception as fallback_err:
                _LOGGER.error("Error sending fallback notification: %s", fallback_err)
    
    # Store the data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "tank_name": tank_name,
        "aquarium_type": aquarium_type,
        "temp_sensor": temp_sensor,
        "frequency_minutes": frequency_minutes,
        "analysis_function": send_ai_temperature_analysis,
    }
    
    # Send initial AI analysis
    await send_ai_temperature_analysis(None)
    
    # Schedule AI analyses based on configured frequency
    unsub = async_track_time_interval(
        hass, send_ai_temperature_analysis, timedelta(minutes=frequency_minutes)
    )
    
    # Store the unsubscribe function
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub
    
    # Register the manual analysis service
    async def run_analysis_service(call: ServiceCall):
        """Handle the run_analysis service call."""
        config_entry_id = call.data["config_entry_id"]
        
        if config_entry_id in hass.data[DOMAIN]:
            analysis_function = hass.data[DOMAIN][config_entry_id]["analysis_function"]
            await analysis_function(None)
            _LOGGER.info("Manual analysis triggered for config entry: %s", config_entry_id)
        else:
            _LOGGER.error("Config entry not found: %s", config_entry_id)
    
    # Register service only once
    if not hass.services.has_service(DOMAIN, "run_analysis"):
        hass.services.async_register(
            DOMAIN,
            "run_analysis",
            run_analysis_service,
            schema=RUN_ANALYSIS_SCHEMA,
        )
    
    # Add listener for options updates
    entry.async_on_unload(entry.add_update_listener(async_options_updated))
    
    return True


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("Aquarium AI options updated, reloading entry")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Aquarium AI integration")
    
    # Cancel the scheduled notifications
    if entry.entry_id in hass.data[DOMAIN]:
        unsub = hass.data[DOMAIN][entry.entry_id].get("unsub")
        if unsub:
            unsub()
        hass.data[DOMAIN].pop(entry.entry_id)
    
    # Remove the service if this is the last entry
    if not hass.data[DOMAIN]:  # If no more entries exist
        if hass.services.has_service(DOMAIN, "run_analysis"):
            hass.services.async_remove(DOMAIN, "run_analysis")
    
    return True