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
    CONF_PH_SENSOR,
    CONF_SALINITY_SENSOR,
    CONF_DISSOLVED_OXYGEN_SENSOR,
    CONF_WATER_LEVEL_SENSOR,
    CONF_UPDATE_FREQUENCY,
    CONF_AI_TASK,
    CONF_AUTO_NOTIFICATIONS,
    DEFAULT_FREQUENCY,
    DEFAULT_AUTO_NOTIFICATIONS,
    UPDATE_FREQUENCIES,
)

_LOGGER = logging.getLogger(__name__)

# Service schema - no parameters needed
RUN_ANALYSIS_SCHEMA = vol.Schema({})


def get_overall_status(sensor_data, aquarium_type):
    """Generate an overall status message for the aquarium based on all sensors."""
    if not sensor_data:
        return f"Your {aquarium_type} Aquarium needs sensor data!"
    
    # Collect all individual sensor statuses
    statuses = []
    for info in sensor_data:
        status = get_simple_status(info['name'], info['raw_value'], info['unit'])
        statuses.append(status)
    
    # Count different status types
    good_count = statuses.count("Good")
    ok_count = statuses.count("OK") 
    problem_count = len([s for s in statuses if s in ["Check", "Adjust", "Low"]])
    
    total_sensors = len(statuses)
    
    # Determine overall status based on sensor status distribution
    if good_count == total_sensors:
        return f"Your {aquarium_type} Aquarium is Excellent! 🌟"
    elif good_count >= total_sensors * 0.75:  # 75% or more good
        return f"Your {aquarium_type} Aquarium is Great! 👍"
    elif (good_count + ok_count) >= total_sensors * 0.8:  # 80% or more good/ok
        return f"Your {aquarium_type} Aquarium is Good 👌"
    elif problem_count <= total_sensors * 0.4:  # Less than 40% problems
        return f"Your {aquarium_type} Aquarium is OK ⚠️"
    else:
        return f"Your {aquarium_type} Aquarium needs attention! 🚨"


def get_sensor_icon(sensor_name):
    """Get appropriate icon for sensor type."""
    sensor_icons = {
        "Temperature": "🌡️",
        "pH": "⚗️", 
        "Salinity": "🧂",
        "Dissolved Oxygen": "💨",
        "Water Level": "📏",
    }
    return sensor_icons.get(sensor_name, "📊")


def get_simple_status(sensor_name, value, unit=""):
    """Generate a simple 1-2 word status based on sensor value and type."""
    try:
        # Try to get numeric value for analysis
        numeric_value = float(value)
        
        # Temperature status (assuming Celsius, but works for Fahrenheit too)
        if sensor_name == "Temperature":
            if 22 <= numeric_value <= 26:
                return "Good"
            elif 20 <= numeric_value <= 28:
                return "OK"
            else:
                return "Check"
        
        # pH status
        elif sensor_name == "pH":
            if 6.8 <= numeric_value <= 7.5:
                return "Good"
            elif 6.5 <= numeric_value <= 8.0:
                return "OK"
            else:
                return "Adjust"
        
        # Salinity status (assuming ppt or similar)
        elif sensor_name == "Salinity":
            if 30 <= numeric_value <= 35:
                return "Good"
            elif 28 <= numeric_value <= 37:
                return "OK"
            else:
                return "Check"
        
        # Dissolved Oxygen status (assuming mg/L)
        elif sensor_name == "Dissolved Oxygen":
            if numeric_value >= 6:
                return "Good"
            elif numeric_value >= 4:
                return "OK"
            else:
                return "Low"
        
        # Water Level percentage
        elif sensor_name == "Water Level" and ("%" in str(value) or "%" in unit):
            if numeric_value >= 80:
                return "Good"
            elif numeric_value >= 60:
                return "OK"
            else:
                return "Low"
        
        # Default for numeric values
        return "OK"
        
    except (ValueError, TypeError):
        # For non-numeric values (like "Normal", "High", "Low")
        value_str = str(value).lower()
        if value_str in ["normal", "good", "excellent", "ok"]:
            return "Good"
        elif value_str in ["high", "low", "warning"]:
            return "Check"
        else:
            return "OK"


def format_sensor_value(value, unit=""):
    """Format sensor value with proper rounding and unit."""
    try:
        # Try to convert to float and round to 1 decimal place
        float_value = float(value)
        rounded_value = round(float_value, 1)
        return f"{rounded_value}{unit}"
    except (ValueError, TypeError):
        # If it's not a number, return as string (for status values like "Normal", "High", etc.)
        return f"{value}{unit}"


def get_sensor_info(hass, sensor_entity_id, sensor_name):
    """Get sensor value and unit, properly formatted."""
    if not sensor_entity_id:
        return None
    
    sensor_state = hass.states.get(sensor_entity_id)
    if not sensor_state or sensor_state.state in ["unknown", "unavailable"]:
        return None
    
    unit = sensor_state.attributes.get("unit_of_measurement", "")
    value = sensor_state.state
    formatted_value = format_sensor_value(value, unit)
    
    return {
        "name": sensor_name,
        "value": formatted_value,
        "raw_value": value,
        "unit": unit
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aquarium AI from a config entry."""
    _LOGGER.info("Setting up Aquarium AI integration")
    
    tank_name = entry.data[CONF_TANK_NAME]
    aquarium_type = entry.data[CONF_AQUARIUM_TYPE]
    temp_sensor = entry.data.get(CONF_TEMPERATURE_SENSOR)
    ph_sensor = entry.data.get(CONF_PH_SENSOR)
    salinity_sensor = entry.data.get(CONF_SALINITY_SENSOR)
    dissolved_oxygen_sensor = entry.data.get(CONF_DISSOLVED_OXYGEN_SENSOR)
    water_level_sensor = entry.data.get(CONF_WATER_LEVEL_SENSOR)
    frequency_key = entry.data.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY)
    ai_task = entry.data.get(CONF_AI_TASK)
    auto_notifications = entry.data.get(CONF_AUTO_NOTIFICATIONS, DEFAULT_AUTO_NOTIFICATIONS)
    frequency_minutes = UPDATE_FREQUENCIES.get(frequency_key, 60)
    
    # Define sensor mappings
    sensor_mappings = [
        (temp_sensor, "Temperature"),
        (ph_sensor, "pH"),
        (salinity_sensor, "Salinity"),
        (dissolved_oxygen_sensor, "Dissolved Oxygen"),
        (water_level_sensor, "Water Level"),
    ]
    
    async def send_ai_aquarium_analysis(now):
        """Send an AI analysis notification about all configured sensors."""
        try:
            # Collect all available sensor data
            sensor_data = []
            analysis_structure = {}
            
            for sensor_entity, sensor_name in sensor_mappings:
                sensor_info = get_sensor_info(hass, sensor_entity, sensor_name)
                if sensor_info:
                    sensor_data.append(sensor_info)
                    # Add to AI analysis structure
                    structure_key = sensor_name.lower().replace(" ", "_") + "_analysis"
                    analysis_structure[structure_key] = {
                        "description": f"An analysis of the aquarium's {sensor_name.lower()} conditions with recommendations.",
                        "required": True,
                        "selector": {"text": None}
                    }
            
            if not sensor_data:
                _LOGGER.warning("No valid sensor data available for analysis")
                return
            
            # Build the conditions string for AI instructions
            conditions_list = [f"- Type: {aquarium_type}"]
            conditions_list.extend([f"- {info['name']}: {info['value']}" for info in sensor_data])
            conditions_str = "\n".join(conditions_list)
            
            # Add overall analysis to structure
            analysis_structure["overall_analysis"] = {
                "description": "A comprehensive analysis of the aquarium's overall health and condition.",
                "required": True,
                "selector": {"text": None}
            }
            
            # Prepare AI Task data
            ai_task_data = {
                "task_name": tank_name,
                "instructions": f"""Based on the current conditions:

{conditions_str}

Analyze my aquarium's conditions and provide recommendations only if needed, do not mention if no adjustments or recommendations are necessary. 
Focus on all available parameters for this {aquarium_type.lower()} aquarium. 
Consider the relationships between different parameters and their impact on aquarium health. 
Always correctly write ph as pH""",

                "structure": analysis_structure
            }
            
            # Call AI Task service using entity ID
            _LOGGER.debug("Calling AI Task service with data: %s", ai_task_data)
            response = await hass.services.async_call(
                "ai_task",
                "generate_data",
                {**ai_task_data, "entity_id": ai_task},
                blocking=True,
                return_response=True,
            )
            
            # Extract the AI analysis
            message_parts = []
            
            # Add overall status at the top
            overall_status = get_overall_status(sensor_data, aquarium_type)
            message_parts.append(f"📋 {overall_status}")
            message_parts.append("")  # Add blank line
            
            # Add sensor readings with icons only (no status labels)
            for info in sensor_data:
                icon = get_sensor_icon(info['name'])
                message_parts.append(f"{icon} {info['name']}: {info['value']}")
            
            message_parts.append("\n🤖 AI Analysis:")
            
            if response and "data" in response:
                ai_data = response["data"]
                for structure_key in analysis_structure.keys():
                    if structure_key in ai_data:
                        analysis_name = structure_key.replace("_analysis", "").replace("_", " ").title()
                        # Find corresponding sensor info for status and icon
                        corresponding_sensor = None
                        for info in sensor_data:
                            if info['name'].lower() == analysis_name.lower():
                                corresponding_sensor = info
                                break
                        
                        if corresponding_sensor:
                            icon = get_sensor_icon(corresponding_sensor['name'])
                            status = get_simple_status(corresponding_sensor['name'], corresponding_sensor['raw_value'], corresponding_sensor['unit'])
                            message_parts.append(f"\n{icon} {analysis_name} ({status}):\n{ai_data[structure_key]}")
                        else:
                            message_parts.append(f"\n{analysis_name}:\n{ai_data[structure_key]}")
            else:
                message_parts.append("No analysis available")
            
            message = "\n".join(message_parts)
            
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"🐠 {tank_name} AI Analysis",
                    "message": message,
                    "notification_id": f"aquarium_ai_{entry.entry_id}",
                },
            )
            _LOGGER.info("Sent AI aquarium analysis notification for %s", tank_name)
            
        except Exception as err:
            _LOGGER.error("Error sending AI aquarium analysis: %s", err)
            # Fallback to simple notification if AI fails
            try:
                fallback_message_parts = []
                fallback_sensor_data = []
                
                for sensor_entity, sensor_name in sensor_mappings:
                    sensor_info = get_sensor_info(hass, sensor_entity, sensor_name)
                    if sensor_info:
                        fallback_sensor_data.append(sensor_info)
                        icon = get_sensor_icon(sensor_info['name'])
                        fallback_message_parts.append(f"{icon} {sensor_info['name']}: {sensor_info['value']}")
                
                if fallback_message_parts:
                    # Add overall status at the top of fallback message too
                    overall_status = get_overall_status(fallback_sensor_data, aquarium_type)
                    fallback_message = f"📋 {overall_status}\n\n" + "\n".join(fallback_message_parts)
                    fallback_message += "\n\n(AI analysis temporarily unavailable)"
                    
                    await hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": f"🐠 {tank_name} Aquarium Update",
                            "message": fallback_message,
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
        "ph_sensor": ph_sensor,
        "salinity_sensor": salinity_sensor,
        "dissolved_oxygen_sensor": dissolved_oxygen_sensor,
        "water_level_sensor": water_level_sensor,
        "frequency_minutes": frequency_minutes,
        "ai_task": ai_task,
        "auto_notifications": auto_notifications,
        "analysis_function": send_ai_aquarium_analysis,
    }
    
    # Send initial AI analysis only if auto-notifications is enabled
    if auto_notifications:
        await send_ai_aquarium_analysis(None)
    
    # Schedule AI analyses based on configured frequency only if auto-notifications is enabled
    unsub = None
    if auto_notifications:
        unsub = async_track_time_interval(
            hass, send_ai_aquarium_analysis, timedelta(minutes=frequency_minutes)
        )
    
    # Store the unsubscribe function (will be None if auto-notifications is disabled)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub
    
    # Register the manual analysis service
    async def run_analysis_service(call: ServiceCall):
        """Handle the run_analysis service call - runs on all aquarium integrations."""
        _LOGGER.info("Manual analysis service called")
        
        # Run analysis on all configured aquarium integrations
        if DOMAIN in hass.data:
            for entry_id, entry_data in hass.data[DOMAIN].items():
                if "analysis_function" in entry_data:
                    try:
                        analysis_function = entry_data["analysis_function"]
                        tank_name = entry_data.get("tank_name", "Unknown Tank")
                        await analysis_function(None)
                        _LOGGER.info("Manual analysis completed for: %s", tank_name)
                    except Exception as err:
                        _LOGGER.error("Error running manual analysis for entry %s: %s", entry_id, err)
        else:
            _LOGGER.warning("No aquarium integrations found to analyze")
    
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