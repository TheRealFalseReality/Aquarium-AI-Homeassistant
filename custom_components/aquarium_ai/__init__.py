"""The Aquarium AI integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval, async_call_later
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
    CONF_ORP_SENSOR,
    CONF_CAMERA,
    CONF_UPDATE_FREQUENCY,
    CONF_AI_TASK,
    CONF_AUTO_NOTIFICATIONS,
    CONF_NOTIFICATION_FORMAT,
    CONF_TANK_VOLUME,
    CONF_FILTRATION,
    CONF_WATER_CHANGE_FREQUENCY,
    CONF_INHABITANTS,
    DEFAULT_FREQUENCY,
    DEFAULT_AUTO_NOTIFICATIONS,
    DEFAULT_NOTIFICATION_FORMAT,
    UPDATE_FREQUENCIES,
)

_LOGGER = logging.getLogger(__name__)

# Service schema - no parameters needed
RUN_ANALYSIS_SCHEMA = vol.Schema({})


async def _send_notification_if_enabled(hass, auto_notifications, title, message, notification_id, tank_name, log_msg_type="analysis"):
    """Send notification only if auto-notifications is enabled."""
    if auto_notifications:
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": title,
                "message": message,
                "notification_id": notification_id,
            },
        )
        _LOGGER.info("Sent %s notification for %s", log_msg_type, tank_name)
    else:
        _LOGGER.debug("%s completed for %s (notifications disabled)", log_msg_type.title(), tank_name)


def get_overall_status(sensor_data, aquarium_type):
    """Generate an overall status message for the aquarium based on all sensors."""
    if not sensor_data:
        return f"Your {aquarium_type} Aquarium needs sensor data!"
    
    # Collect all individual sensor statuses
    statuses = []
    for info in sensor_data:
        status = get_simple_status(info['name'], info['raw_value'], info['unit'], aquarium_type)
        statuses.append(status)
    
    # Count different status types
    good_count = statuses.count("Good")
    ok_count = statuses.count("OK") 
    problem_count = len([s for s in statuses if s in ["Check", "Adjust", "Low", "High"]])
    
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
        "ORP": "⚡",
    }
    return sensor_icons.get(sensor_name, "📊")


def get_simple_status(sensor_name, value, unit="", aquarium_type=""):
    """Generate a simple 1-2 word status based on sensor value and type."""
    try:
        # Try to get numeric value for analysis
        numeric_value = float(value)
        
        # Temperature status - handle different units
        if sensor_name == "Temperature":
            if unit.lower() in ["°f", "f", "fahrenheit"]:
                # Convert Fahrenheit ranges: 76-79°F (24-26°C), 72-82°F (22-28°C)
                if 76 <= numeric_value <= 79:
                    return "Good"
                elif 72 <= numeric_value <= 82:
                    return "OK"
                else:
                    return "Check"
            else:
                # Default to Celsius (°C, C, celsius, or no unit)
                if 24 <= numeric_value <= 26:
                    return "Good"
                elif 22 <= numeric_value <= 28:
                    return "OK"
                else:
                    return "Check"
        
        # pH status - tank type dependent
        elif sensor_name == "pH":
            aquarium_type_lower = aquarium_type.lower()
            if "saltwater" in aquarium_type_lower or "marine" in aquarium_type_lower or "reef" in aquarium_type_lower:
                # Saltwater/Marine aquarium pH ranges
                if 8.0 <= numeric_value <= 8.4:
                    return "Good"
                elif 7.8 <= numeric_value <= 8.6:
                    return "OK"
                else:
                    return "Adjust"
            else:
                # Freshwater aquarium pH ranges (default)
                if 6.5 <= numeric_value <= 8.0:
                    return "Good"
                elif 6.0 <= numeric_value <= 8.5:
                    return "OK"
                else:
                    return "Adjust"
        
        # Salinity status - handle different units
        elif sensor_name == "Salinity":
            if unit.lower() in ["sg", "specific_gravity"]:
                # Specific gravity ranges: 1.020-1.025 (good), 1.018-1.027 (ok)
                if 1.020 <= numeric_value <= 1.025:
                    return "Good"
                elif 1.018 <= numeric_value <= 1.027:
                    return "OK"
                else:
                    return "Check"
            if unit.lower() in ["mS/cm", "ms/cm"]:
                # Conductivity ranges: 46.25-53.06 (good), 43.48-55.75 (ok)
                if 46.25 <= numeric_value <= 53.06:
                    return "Good"
                elif 43.48 <= numeric_value <= 55.75:
                    return "OK"
                else:
                    return "Check"
            else:
                # Default to ppt, psu, or similar salt concentration units
                if 30 <= numeric_value <= 35:
                    return "Good"
                elif 28 <= numeric_value <= 37:
                    return "OK"
                else:
                    return "Check"
        
        # Dissolved Oxygen status - handle different units
        elif sensor_name == "Dissolved Oxygen":
            if unit.lower() in ["ppm", "parts_per_million"]:
                # PPM is similar to mg/L for water
                if numeric_value >= 12:
                    return "High"
                elif numeric_value >= 7:
                    return "Good"
                elif numeric_value >= 4:
                    return "OK"
                else:
                    return "Low"
            elif unit.lower() in ["%", "percent", "saturation"]:
                # Percentage saturation
                if numeric_value >= 120:
                    return "High"
                elif numeric_value >= 85:
                    return "Good"
                elif numeric_value >= 60:
                    return "OK"
                else:
                    return "Low"
            else:
                # Default to mg/L
                if numeric_value >= 6:
                    return "Good"
                elif numeric_value >= 4:
                    return "OK"
                else:
                    return "Low"
        
        # Water Level - handle percentage or other units
        elif sensor_name == "Water Level":
            if unit.lower() in ["%", "percent"] or "%" in str(value):
                if numeric_value >= 80:
                    return "Good"
                elif numeric_value >= 60:
                    return "OK"
                else:
                    return "Low"
            else:
                # For absolute measurements (cm, inches, etc.), we can't easily determine good/bad
                # without knowing the tank specifications, so default to OK
                return "OK"
        
        # ORP (Oxidation-Reduction Potential) status - handle different units
        elif sensor_name == "ORP":
            # ORP is typically measured in millivolts (mV)
            aquarium_type_lower = aquarium_type.lower()
            if "saltwater" in aquarium_type_lower or "marine" in aquarium_type_lower or "reef" in aquarium_type_lower:
                # Saltwater/Marine aquarium ORP ranges (mV)
                if 300 <= numeric_value <= 400:
                    return "Good"
                elif 275 <= numeric_value <= 425:
                    return "OK"
                else:
                    return "Check"
            else:
                # Freshwater aquarium ORP ranges (mV)
                if 250 <= numeric_value <= 400:
                    return "Good"
                elif 150 <= numeric_value <= 500:
                    return "OK"
                else:
                    return "Check"
        
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


def _build_notification_message(notification_format, sensor_data, sensor_mappings, aquarium_type, response):
    """Build notification message based on the selected format."""
    message_parts = []
    
    # Add overall status at the top for all formats
    overall_status = get_overall_status(sensor_data, aquarium_type)
    message_parts.append(f"📋 {overall_status}")
    message_parts.append("")  # Add blank line
    
    if notification_format == "minimal":
        # Minimal format: Only parameter values and overall analysis
        for info in sensor_data:
            icon = get_sensor_icon(info['name'])
            message_parts.append(f"{icon} {info['name']}: {info['value']}")
        
        # Add overall analysis only
        if response and "data" in response:
            ai_data = response["data"]
            if "overall_notification_analysis" in ai_data:
                message_parts.append(f"\n🎯 Overall Assessment:\n{ai_data['overall_notification_analysis']}")
        else:
            message_parts.append("\nNo analysis available")
            
    elif notification_format == "condensed":
        # Condensed format: Parameter values + brief sensor analysis + overall analysis
        for info in sensor_data:
            icon = get_sensor_icon(info['name'])
            message_parts.append(f"{icon} {info['name']}: {info['value']}")
        
        message_parts.append("\n🤖 AI Analysis:")
        
        if response and "data" in response:
            ai_data = response["data"]
            
            # Use brief sensor analysis (same as used for sensors)
            for sensor_entity, sensor_name in sensor_mappings:
                analysis_key = sensor_name.lower().replace(" ", "_") + "_analysis"
                if analysis_key in ai_data:
                    # Find corresponding sensor info for icon
                    corresponding_sensor = None
                    for info in sensor_data:
                        if info['name'].lower() == sensor_name.lower():
                            corresponding_sensor = info
                            break
                    
                    if corresponding_sensor:
                        icon = get_sensor_icon(corresponding_sensor['name'])
                        status = get_simple_status(corresponding_sensor['name'], corresponding_sensor['raw_value'], corresponding_sensor['unit'], aquarium_type)
                        message_parts.append(f"\n{icon} {sensor_name} ({status}): {ai_data[analysis_key]}")
                    else:
                        message_parts.append(f"\n{sensor_name}: {ai_data[analysis_key]}")
            
            # Add overall brief analysis (same as used for sensors)
            if "overall_analysis" in ai_data:
                message_parts.append(f"\n🎯 Overall Assessment: {ai_data['overall_analysis']}")
        else:
            message_parts.append("No analysis available")
            
    else:  # "detailed" - current full format
        # Add sensor readings with icons
        for info in sensor_data:
            icon = get_sensor_icon(info['name'])
            message_parts.append(f"{icon} {info['name']}: {info['value']}")
        
        message_parts.append("\n🤖 AI Analysis:")
        
        if response and "data" in response:
            ai_data = response["data"]
            
            # Use detailed notification analysis for notifications
            for sensor_entity, sensor_name in sensor_mappings:
                notification_key = sensor_name.lower().replace(" ", "_") + "_notification_analysis"
                if notification_key in ai_data:
                    # Find corresponding sensor info for status and icon
                    corresponding_sensor = None
                    for info in sensor_data:
                        if info['name'].lower() == sensor_name.lower():
                            corresponding_sensor = info
                            break
                    
                    if corresponding_sensor:
                        icon = get_sensor_icon(corresponding_sensor['name'])
                        status = get_simple_status(corresponding_sensor['name'], corresponding_sensor['raw_value'], corresponding_sensor['unit'], aquarium_type)
                        message_parts.append(f"\n{icon} {sensor_name} ({status}):\n{ai_data[notification_key]}")
                    else:
                        message_parts.append(f"\n{sensor_name}:\n{ai_data[notification_key]}")
            
            # Add overall detailed analysis
            if "overall_notification_analysis" in ai_data:
                message_parts.append(f"\n🎯 Overall Assessment:\n{ai_data['overall_notification_analysis']}")
        else:
            message_parts.append("No analysis available")
    
    # Add water change recommendation at the end for all formats
    if response and "data" in response:
        ai_data = response["data"]
        if "water_change_recommendation" in ai_data:
            message_parts.append(f"\n💧 Water Change Recommendation:\n{ai_data['water_change_recommendation']}")
    
    return "\n".join(message_parts)


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
    orp_sensor = entry.data.get(CONF_ORP_SENSOR)
    camera = entry.data.get(CONF_CAMERA)
    frequency_key = entry.data.get(CONF_UPDATE_FREQUENCY, DEFAULT_FREQUENCY)
    ai_task = entry.data.get(CONF_AI_TASK)
    auto_notifications = entry.data.get(CONF_AUTO_NOTIFICATIONS, DEFAULT_AUTO_NOTIFICATIONS)
    notification_format = entry.data.get(CONF_NOTIFICATION_FORMAT, DEFAULT_NOTIFICATION_FORMAT)
    tank_volume = entry.data.get(CONF_TANK_VOLUME, "")
    filtration = entry.data.get(CONF_FILTRATION, "")
    water_change_frequency = entry.data.get(CONF_WATER_CHANGE_FREQUENCY, "")
    inhabitants = entry.data.get(CONF_INHABITANTS, "")
    frequency_minutes = UPDATE_FREQUENCIES.get(frequency_key, 60)
    
    # Set up sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    # Define sensor mappings
    sensor_mappings = [
        (temp_sensor, "Temperature"),
        (ph_sensor, "pH"),
        (salinity_sensor, "Salinity"),
        (dissolved_oxygen_sensor, "Dissolved Oxygen"),
        (water_level_sensor, "Water Level"),
        (orp_sensor, "ORP"),
    ]
    
    async def send_ai_aquarium_analysis(now):
        """Send an AI analysis notification about all configured sensors."""
        try:
            # Collect all available sensor data
            sensor_data = []
            analysis_structure_sensors = {}
            analysis_structure_notification = {}
            
            for sensor_entity, sensor_name in sensor_mappings:
                sensor_info = get_sensor_info(hass, sensor_entity, sensor_name)
                if sensor_info:
                    sensor_data.append(sensor_info)
                    # Add to AI analysis structure for sensors (brief)
                    structure_key = sensor_name.lower().replace(" ", "_") + "_analysis"
                    analysis_structure_sensors[structure_key] = {
                        "description": f"Brief 1-2 sentence analysis of the aquarium's {sensor_name.lower()} conditions (under 200 characters).",
                        "required": True,
                        "selector": {"text": None}
                    }
                    # Add to AI analysis structure for notifications (detailed)
                    notification_key = sensor_name.lower().replace(" ", "_") + "_notification_analysis"
                    analysis_structure_notification[notification_key] = {
                        "description": f"Detailed analysis of the aquarium's {sensor_name.lower()} conditions. Provide comprehensive explanation including current status, potential issues, trends, and detailed recommendations if needed.",
                        "required": True,
                        "selector": {"text": None}
                    }
            
            if not sensor_data:
                _LOGGER.warning("No valid sensor data available for analysis")
                return
            
            # Build the conditions string for AI instructions with explicit units
            conditions_list = [f"- Type: {aquarium_type}"]
            if tank_volume and tank_volume.strip():
                conditions_list.append(f"- Tank Volume: {tank_volume}")
            if filtration and filtration.strip():
                conditions_list.append(f"- Filtration: {filtration}")
            if water_change_frequency and water_change_frequency.strip():
                conditions_list.append(f"- Water Change Schedule: {water_change_frequency}")
            if inhabitants and inhabitants.strip():
                conditions_list.append(f"- Inhabitants: {inhabitants}")
            
            for info in sensor_data:
                if info['unit']:
                    conditions_list.append(f"- {info['name']}: {info['raw_value']} {info['unit']}")
                else:
                    conditions_list.append(f"- {info['name']}: {info['raw_value']} (no units)")
            conditions_str = "\n".join(conditions_list)
            
            # Add overall analysis to both structures
            analysis_structure_sensors["overall_analysis"] = {
                "description": "Brief 1-2 sentence overall aquarium health assessment (under 200 characters).",
                "required": True,
                "selector": {"text": None}
            }
            analysis_structure_sensors["water_change_recommended"] = {
                "description": "Simple yes or no answer on whether a water change is recommended based on current parameters, bioload, and water change schedule. Answer with 'Yes' or 'No' followed by a brief reason (under 150 characters total).",
                "required": True,
                "selector": {"text": None}
            }
            analysis_structure_notification["overall_notification_analysis"] = {
                "description": "Comprehensive overall aquarium health assessment. Provide detailed summary of all parameters, their relationships, overall tank health, and any recommendations for improvement.",
                "required": True,
                "selector": {"text": None}
            }
            analysis_structure_notification["water_change_recommendation"] = {
                "description": "Detailed water change recommendation considering current parameters, bioload from inhabitants, filtration capacity, and water change schedule. If recommended, suggest approximate percentage and timing. Consider the relationship between water quality, stocking levels, filtration, and maintenance schedule.",
                "required": True,
                "selector": {"text": None}
            }
            
            # Combine both structures for the AI task
            combined_analysis_structure = {**analysis_structure_sensors, **analysis_structure_notification}
            
            # Prepare camera instructions if camera is configured
            camera_instructions = ""
            if camera:
                camera_instructions = """

If an aquarium camera image is provided:
- Analyze the visual aspects of the aquarium focusing on:
  * Water clarity and quality (cloudy, clear, tinted, etc.) - NO NUMERICAL ANALYSIS
  * Fish identification and count if visible (species, behavior, health appearance)
  * Plant health and growth if visible
  * Equipment visibility and condition
  * Overall aquarium aesthetics and cleanliness
  * Any visible algae, debris, or maintenance needs
- Focus only on aquarium-related observations that can be determined visually
- Do not attempt to provide numerical measurements from the image
- Integrate visual observations with sensor data when drawing conclusions"""

            # Prepare AI Task data with separate instructions for sensor vs notification analysis
            ai_task_data = {
                "task_name": tank_name,
                "instructions": f"""Based on the current conditions:

{conditions_str}{camera_instructions}

Provide analysis for this {aquarium_type.lower()} aquarium. 

For sensor analysis fields (ending with '_analysis'):
- Provide brief 1-2 sentence analysis under 200 characters
- Focus on current status and immediate concerns only

For notification analysis fields (ending with '_notification_analysis'):
- Provide detailed analysis of the parameter
- Include current status, potential issues, relationships with other parameters
- Provide recommendations for improvement only if the parameter is negative to the aquarium health, do not mention if everything is fine. If there are no concerns, issues or recommendations simply state that the parameter is within optimal range.

For overall_analysis: Brief 1-2 sentence health assessment under 200 characters.
For overall_notification_analysis: Detailed but short paragraph assessment without character limits.

For water_change_recommended: Answer 'Yes' or 'No' with a brief reason considering all factors (under 150 characters).
For water_change_recommendation: Provide detailed recommendation considering water quality, bioload from inhabitants, filtration capacity, and water change schedule. If a water change is recommended, suggest approximate percentage and timing.

Consider the relationships between different parameters 
Consider impact on aquarium health when the parameters are negative to the aquarium health
Consider the bioload from inhabitants and whether filtration is adequate
Consider the water change schedule and whether it's sufficient for the current bioload
Always correctly write ph as pH.

When considering the parameters, use the following guidelines for healthy ranges:
- Temperature: 22-28°C (72-82°F) for most fish, 24-28°C (76-82°F) acceptable for tropical fish, 20-24°C (68-75°F) for coldwater fish, 24-26°C (75-79°F) for reef tanks
- Water Level: 80%+ if percentage, otherwise ensure within acceptable range for tank size
- pH: 6.5-8.0 for freshwater, 8.0-8.4 for saltwater/marine
- Salinity: 30-35 ppt/psu for saltwater, 1.020-1.025 SG or 46.25-53.06 mS/cm for saltwater specific gravity/conductivity
- Dissolved Oxygen: 6+ mg/L, 85%+ saturation, 7+ ppm. But Higher levels (up to 120% saturation or 12+ mg/L) can lead to gas bubble disease
- ORP: 250-400 mV for freshwater, 300-400 mV for saltwater/marine

IMPORTANT: Pay careful attention to the units provided for each parameter. Use the actual units when evaluating if values are appropriate:
- Temperature: Consider if values are in Celsius (°C) or Fahrenheit (°F)
- Salinity: Consider if values are in ppt/psu (parts per thousand) or specific gravity (SG)
- Dissolved Oxygen: Consider if values are in mg/L, ppm, or percentage saturation
- Water Level: Consider if values are percentages or absolute measurements
- pH: Typically has no units (pure number scale 0-14)""",
                "structure": combined_analysis_structure
            }
            
            # Add camera attachment if configured
            if camera:
                ai_task_data["attachments"] = {
                    "media_content_id": f"media-source://camera/{camera}",
                    "media_content_type": "application/vnd.apple.mpegurl",
                    "metadata": {
                        "title": f"{camera.replace('camera.', '').title()} Camera",
                        "thumbnail": f"/api/camera_proxy/{camera}",
                        "media_class": "video",
                        "children_media_class": None,
                        "navigateIds": [
                            {},
                            {
                                "media_content_type": "app",
                                "media_content_id": "media-source://camera"
                            }
                        ]
                    }
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
            
            # Extract the AI analysis and build message based on format
            message = _build_notification_message(
                notification_format, sensor_data, sensor_mappings, aquarium_type, response
            )
            
            # Send notification using consolidated helper
            await _send_notification_if_enabled(
                hass, 
                auto_notifications,
                f"🐠 {tank_name} AI Analysis",
                message,
                f"aquarium_ai_{entry.entry_id}",
                tank_name,
                "AI analysis"
            )
            
            # Store AI analysis data for sensors to use
            if response and "data" in response:
                ai_data = response["data"]
                
                # Store sensor analysis data (brief versions for sensors)
                sensor_analysis_data = {}
                for structure_key in analysis_structure_sensors.keys():
                    if structure_key in ai_data:
                        analysis_text = ai_data[structure_key]
                        # Ensure we stay under 255 characters for sensors
                        if len(analysis_text) > 255:
                            analysis_text = analysis_text[:252] + "..."
                        sensor_analysis_data[structure_key] = analysis_text
                
                # Store overall analysis with brief version for sensors
                if "overall_analysis" in ai_data:
                    overall_analysis = ai_data["overall_analysis"]
                    if len(overall_analysis) > 255:
                        overall_analysis = overall_analysis[:252] + "..."
                    sensor_analysis_data["overall_analysis"] = overall_analysis
                
                # Store water change recommendation with brief version for sensors
                if "water_change_recommended" in ai_data:
                    water_change_rec = ai_data["water_change_recommended"]
                    if len(water_change_rec) > 255:
                        water_change_rec = water_change_rec[:252] + "..."
                    sensor_analysis_data["water_change_recommended"] = water_change_rec
                
                # Store the analysis data and sensor data in hass.data for sensors to access
                hass.data[DOMAIN][entry.entry_id]["sensor_analysis"] = sensor_analysis_data
                hass.data[DOMAIN][entry.entry_id]["sensor_data"] = sensor_data
                hass.data[DOMAIN][entry.entry_id]["last_update"] = now
            
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
                    
                    # Send fallback notification using consolidated helper
                    await _send_notification_if_enabled(
                        hass,
                        auto_notifications,
                        f"🐠 {tank_name} Aquarium Update",
                        fallback_message,
                        f"aquarium_ai_{entry.entry_id}",
                        tank_name,
                        "fallback analysis"
                    )
                    
                    # Store fallback sensor data for sensors to use
                    hass.data[DOMAIN][entry.entry_id]["sensor_analysis"] = {}
                    hass.data[DOMAIN][entry.entry_id]["sensor_data"] = fallback_sensor_data
                    hass.data[DOMAIN][entry.entry_id]["last_update"] = now
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
        "orp_sensor": orp_sensor,
        "camera": camera,
        "frequency_minutes": frequency_minutes,
        "ai_task": ai_task,
        "auto_notifications": auto_notifications,
        "notification_format": notification_format,
        "tank_volume": tank_volume,
        "filtration": filtration,
        "water_change_frequency": water_change_frequency,
        "inhabitants": inhabitants,
        "analysis_function": send_ai_aquarium_analysis,
    }
    
    # Schedule delayed AI analysis on startup to ensure HA is fully ready (only if not manual-only)
    async def delayed_startup_analysis(now):
        """Run initial AI analysis after HA is fully started."""
        _LOGGER.info("Running delayed startup AI analysis for %s", tank_name)
        await send_ai_aquarium_analysis(None)
    
    # Initialize unsub as None
    unsub = None
    
    # Only schedule automatic analysis if frequency is not "never"
    if frequency_minutes is not None:
        # Run initial analysis after 60 seconds to ensure HA is fully ready
        async_call_later(hass, 60, delayed_startup_analysis)
        
        # Schedule AI analyses based on configured frequency
        unsub = async_track_time_interval(
            hass, send_ai_aquarium_analysis, timedelta(minutes=frequency_minutes)
        )
        _LOGGER.info("Scheduled automatic analysis every %d minutes for %s", frequency_minutes, tank_name)
    else:
        _LOGGER.info("Manual analysis only mode enabled for %s", tank_name)
    
    # Store the unsubscribe function
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
    
    # Unload sensor platform
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])