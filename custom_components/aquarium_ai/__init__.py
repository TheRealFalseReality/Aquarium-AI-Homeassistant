"""The Aquarium AI integration."""
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
    CONF_LAST_WATER_CHANGE,
    CONF_MISC_INFO,
    CONF_RUN_ANALYSIS_ON_STARTUP,
    CONF_ANALYZE_TEMPERATURE,
    CONF_ANALYZE_PH,
    CONF_ANALYZE_SALINITY,
    CONF_ANALYZE_DISSOLVED_OXYGEN,
    CONF_ANALYZE_WATER_LEVEL,
    CONF_ANALYZE_ORP,
    CONF_PROMPT_MAIN_INSTRUCTIONS,
    CONF_PROMPT_PARAMETER_GUIDELINES,
    CONF_PROMPT_CAMERA_INSTRUCTIONS,
    CONF_PROMPT_BRIEF_ANALYSIS,
    CONF_PROMPT_DETAILED_ANALYSIS,
    CONF_PROMPT_WATER_CHANGE,
    CONF_PROMPT_OVERALL_ANALYSIS,
    DEFAULT_FREQUENCY,
    DEFAULT_AUTO_NOTIFICATIONS,
    DEFAULT_NOTIFICATION_FORMAT,
    DEFAULT_RUN_ANALYSIS_ON_STARTUP,
    DEFAULT_ANALYZE_TEMPERATURE,
    DEFAULT_ANALYZE_PH,
    DEFAULT_ANALYZE_SALINITY,
    DEFAULT_ANALYZE_DISSOLVED_OXYGEN,
    DEFAULT_ANALYZE_WATER_LEVEL,
    DEFAULT_ANALYZE_ORP,
    DEFAULT_PROMPT_MAIN_INSTRUCTIONS,
    DEFAULT_PROMPT_PARAMETER_GUIDELINES,
    DEFAULT_PROMPT_CAMERA_INSTRUCTIONS,
    DEFAULT_PROMPT_BRIEF_ANALYSIS,
    DEFAULT_PROMPT_DETAILED_ANALYSIS,
    DEFAULT_PROMPT_WATER_CHANGE,
    DEFAULT_PROMPT_OVERALL_ANALYSIS,
    UPDATE_FREQUENCIES,
)

_LOGGER = logging.getLogger(__name__)

# Service schema - optional send_notification parameter for run_analysis
RUN_ANALYSIS_SCHEMA = vol.Schema({
    vol.Optional("send_notification", default=True): cv.boolean,
})

# Service schema for run_analysis_for_aquarium - requires config_entry parameter, optional send_notification
RUN_ANALYSIS_FOR_AQUARIUM_SCHEMA = vol.Schema({
    vol.Required("config_entry"): cv.string,
    vol.Optional("send_notification", default=True): cv.boolean,
})


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
                if 8.2 <= numeric_value <= 8.4:
                    return "Good"
                elif 8.0 <= numeric_value <= 8.6:
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
        
        # Add water change recommendation before overall analysis
        if response and "data" in response:
            ai_data = response["data"]
            if "water_change_recommendation" in ai_data:
                message_parts.append(f"\n💧 Water Change:\n{ai_data['water_change_recommendation']}")
            
            # Add camera visual analysis if available
            if "camera_visual_notification_analysis" in ai_data:
                message_parts.append(f"\n📷 Camera Analysis:\n{ai_data['camera_visual_notification_analysis']}")
            
            # Add overall analysis
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
            for sensor_entity, sensor_name, analyze_conf, default_analyze in sensor_mappings:
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
            
            # Add water change recommendation before overall analysis
            if "water_change_recommendation" in ai_data:
                message_parts.append(f"\n💧 Water Change: {ai_data['water_change_recommendation']}")
            
            # Add camera visual analysis if available (brief version for condensed)
            if "camera_visual_analysis" in ai_data:
                message_parts.append(f"\n📷 Camera Analysis: {ai_data['camera_visual_analysis']}")
            
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
            for sensor_entity, sensor_name, analyze_conf, default_analyze in sensor_mappings:
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
            
            # Add water change recommendation before overall analysis
            if "water_change_recommendation" in ai_data:
                message_parts.append(f"\n💧 Water Change:\n{ai_data['water_change_recommendation']}")
            
            # Add camera visual analysis if available (detailed version)
            if "camera_visual_notification_analysis" in ai_data:
                message_parts.append(f"\n📷 Camera Analysis:\n{ai_data['camera_visual_notification_analysis']}")
            
            # Add overall detailed analysis
            if "overall_notification_analysis" in ai_data:
                message_parts.append(f"\n🎯 Overall Assessment:\n{ai_data['overall_notification_analysis']}")
        else:
            message_parts.append("No analysis available")
    
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
    last_water_change = entry.data.get(CONF_LAST_WATER_CHANGE, "")
    misc_info = entry.data.get(CONF_MISC_INFO, "")
    frequency_minutes = UPDATE_FREQUENCIES.get(frequency_key, 60)
    
    # Load custom AI prompts or use defaults
    prompt_main_instructions = entry.data.get(CONF_PROMPT_MAIN_INSTRUCTIONS, DEFAULT_PROMPT_MAIN_INSTRUCTIONS)
    prompt_parameter_guidelines = entry.data.get(CONF_PROMPT_PARAMETER_GUIDELINES, DEFAULT_PROMPT_PARAMETER_GUIDELINES)
    prompt_camera_instructions = entry.data.get(CONF_PROMPT_CAMERA_INSTRUCTIONS, DEFAULT_PROMPT_CAMERA_INSTRUCTIONS)
    prompt_brief_analysis = entry.data.get(CONF_PROMPT_BRIEF_ANALYSIS, DEFAULT_PROMPT_BRIEF_ANALYSIS)
    prompt_detailed_analysis = entry.data.get(CONF_PROMPT_DETAILED_ANALYSIS, DEFAULT_PROMPT_DETAILED_ANALYSIS)
    prompt_water_change = entry.data.get(CONF_PROMPT_WATER_CHANGE, DEFAULT_PROMPT_WATER_CHANGE)
    prompt_overall_analysis = entry.data.get(CONF_PROMPT_OVERALL_ANALYSIS, DEFAULT_PROMPT_OVERALL_ANALYSIS)
    
    # Get run_analysis_on_startup setting, default to False
    run_analysis_on_startup = entry.data.get(CONF_RUN_ANALYSIS_ON_STARTUP, DEFAULT_RUN_ANALYSIS_ON_STARTUP)
    
    # Set up sensor, binary_sensor, switch, select, and button platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch", "select", "button"])
    
    # Define sensor mappings with their analysis toggle configurations
    # Format: (sensor_entity, sensor_name, analyze_config_key, default_analyze_value)
    sensor_mappings = [
        (temp_sensor, "Temperature", CONF_ANALYZE_TEMPERATURE, DEFAULT_ANALYZE_TEMPERATURE),
        (ph_sensor, "pH", CONF_ANALYZE_PH, DEFAULT_ANALYZE_PH),
        (salinity_sensor, "Salinity", CONF_ANALYZE_SALINITY, DEFAULT_ANALYZE_SALINITY),
        (dissolved_oxygen_sensor, "Dissolved Oxygen", CONF_ANALYZE_DISSOLVED_OXYGEN, DEFAULT_ANALYZE_DISSOLVED_OXYGEN),
        (water_level_sensor, "Water Level", CONF_ANALYZE_WATER_LEVEL, DEFAULT_ANALYZE_WATER_LEVEL),
        (orp_sensor, "ORP", CONF_ANALYZE_ORP, DEFAULT_ANALYZE_ORP),
    ]
    
    async def send_ai_aquarium_analysis(now, override_notification=None):
        """Send an AI analysis notification about all configured sensors.
        
        Args:
            now: Timestamp or None
            override_notification: Optional bool to override auto_notifications setting.
                                  If True, forces notification. If False, prevents notification.
                                  If None, uses auto_notifications config.
        """
        try:
            # Determine whether to send notification
            should_send_notification = override_notification if override_notification is not None else auto_notifications
            
            # Collect all available sensor data
            sensor_data = []
            analysis_structure_sensors = {}
            analysis_structure_notification = {}
            
            for sensor_entity, sensor_name, analyze_conf, default_analyze in sensor_mappings:
                # Check if analysis is enabled for this parameter
                analyze_enabled = entry.data.get(analyze_conf, default_analyze)
                
                # Only process sensor if it's configured AND analysis is enabled
                if sensor_entity and analyze_enabled:
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
                elif sensor_entity and not analyze_enabled:
                    _LOGGER.debug("Skipping %s analysis for %s (toggle disabled)", sensor_name, tank_name)
            
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
            
            # Add last water change information if available
            if last_water_change and last_water_change.strip():
                last_change_state = hass.states.get(last_water_change)
                if last_change_state and last_change_state.state not in ["unknown", "unavailable"]:
                    conditions_list.append(f"- Last Water Change: {last_change_state.state}")
            
            # Add misc info if provided
            if misc_info and misc_info.strip():
                conditions_list.append(f"- Additional Information: {misc_info}")
            
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
                "description": "Concise water change recommendation. If recommended, state the percentage and timing (e.g., '30% within 2-3 days' or '25% this week'). If not needed, state when next scheduled change is due based on maintenance schedule. Do not include generic benefits or explanations about why water changes are important - focus only on whether it's needed and when.",
                "required": True,
                "selector": {"text": None}
            }
            
            # Combine both structures for the AI task
            combined_analysis_structure = {**analysis_structure_sensors, **analysis_structure_notification}
            
            # Prepare camera instructions if camera is configured
            camera_instructions = ""
            if camera:
                # Add camera analysis fields to the structure
                combined_analysis_structure["camera_visual_analysis"] = {
                    "description": "Brief 1-2 sentence visual analysis of the aquarium from the camera image (under 200 characters). Focus on water clarity, fish/plant health, and any maintenance needs visible.",
                    "required": True,
                    "selector": {"text": None}
                }
                combined_analysis_structure["camera_visual_notification_analysis"] = {
                    "description": "Detailed visual analysis of the aquarium from the camera image. Include observations about water clarity, fish identification and behavior, plant health, equipment condition, and any visible maintenance needs. Provide specific observations and recommendations based on what is visible in the image.",
                    "required": True,
                    "selector": {"text": None}
                }
                
                # Use custom camera instructions
                camera_instructions = f"\n\n{prompt_camera_instructions}"

            # Build AI instructions from custom prompts
            instructions_parts = [
                f"Based on the current conditions:\n\n{conditions_str}{camera_instructions}\n",
                prompt_main_instructions.format(aquarium_type=aquarium_type.lower()),
                "\n\n" + prompt_brief_analysis,
                "\n\n" + prompt_detailed_analysis,
                "\n\n" + prompt_overall_analysis,
                "\n\n" + prompt_water_change,
                "\n\n" + prompt_parameter_guidelines
            ]
            
            # Prepare AI Task data with custom instructions
            ai_task_data = {
                "task_name": tank_name,
                "instructions": "".join(instructions_parts),
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
                should_send_notification,
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
                
                # Store camera visual analysis with brief version for sensors (if camera configured)
                if "camera_visual_analysis" in ai_data:
                    camera_analysis = ai_data["camera_visual_analysis"]
                    if len(camera_analysis) > 255:
                        camera_analysis = camera_analysis[:252] + "..."
                    sensor_analysis_data["camera_visual_analysis"] = camera_analysis
                
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
                
                for sensor_entity, sensor_name, analyze_conf, default_analyze in sensor_mappings:
                    # Only process sensor if analysis is enabled
                    analyze_enabled = entry.data.get(analyze_conf, default_analyze)
                    if sensor_entity and analyze_enabled:
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
                        should_send_notification,
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
        "last_water_change": last_water_change,
        "misc_info": misc_info,
        "analysis_function": send_ai_aquarium_analysis,
    }
    
    # Schedule delayed AI analysis on startup to ensure HA is fully ready (only if enabled via switch)
    async def delayed_startup_analysis(now):
        """Run initial AI analysis after HA is fully started."""
        _LOGGER.info("Running delayed startup AI analysis for %s", tank_name)
        await send_ai_aquarium_analysis(None)
    
    # Initialize unsub as None
    unsub = None
    
    # Only schedule automatic analysis if frequency is not "never"
    if frequency_minutes is not None:
        # Run initial analysis after 60 seconds only if run_analysis_on_startup is enabled
        if run_analysis_on_startup:
            async_call_later(hass, 60, delayed_startup_analysis)
            _LOGGER.info("Startup analysis enabled for %s - will run in 60 seconds", tank_name)
        else:
            _LOGGER.info("Startup analysis disabled for %s - skipping initial analysis", tank_name)
        
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
        send_notification = call.data.get("send_notification", True)
        _LOGGER.info("Manual analysis service called (send_notification=%s)", send_notification)
        
        # Run analysis on all configured aquarium integrations
        if DOMAIN in hass.data:
            for entry_id, entry_data in hass.data[DOMAIN].items():
                if "analysis_function" in entry_data:
                    try:
                        analysis_function = entry_data["analysis_function"]
                        tank_name = entry_data.get("tank_name", "Unknown Tank")
                        await analysis_function(None, override_notification=send_notification)
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
    
    # Register the specific aquarium analysis service
    async def run_analysis_for_aquarium_service(call: ServiceCall):
        """Handle the run_analysis_for_aquarium service call - runs on a specific aquarium."""
        config_entry_id = call.data["config_entry"]
        send_notification = call.data.get("send_notification", True)
        
        _LOGGER.info("Manual analysis service called for config entry: %s (send_notification=%s)", config_entry_id, send_notification)
        
        # Run analysis on the specific aquarium integration
        if DOMAIN in hass.data and config_entry_id in hass.data[DOMAIN]:
            entry_data = hass.data[DOMAIN][config_entry_id]
            if "analysis_function" in entry_data:
                try:
                    analysis_function = entry_data["analysis_function"]
                    tank_name = entry_data.get("tank_name", "Unknown Tank")
                    await analysis_function(None, override_notification=send_notification)
                    _LOGGER.info("Manual analysis completed for: %s", tank_name)
                except Exception as err:
                    _LOGGER.error("Error running manual analysis for entry %s: %s", config_entry_id, err)
            else:
                _LOGGER.error("No analysis function found for entry %s", config_entry_id)
        else:
            _LOGGER.error("Aquarium integration %s not found", config_entry_id)
    
    # Register service only once
    if not hass.services.has_service(DOMAIN, "run_analysis_for_aquarium"):
        hass.services.async_register(
            DOMAIN,
            "run_analysis_for_aquarium",
            run_analysis_for_aquarium_service,
            schema=RUN_ANALYSIS_FOR_AQUARIUM_SCHEMA,
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
        if hass.services.has_service(DOMAIN, "run_analysis_for_aquarium"):
            hass.services.async_remove(DOMAIN, "run_analysis_for_aquarium")
    
    # Unload sensor, binary_sensor, switch, select, and button platforms
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "switch", "select", "button"])
