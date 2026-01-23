"""Constants for the Aquarium AI integration."""
from typing import Final

DOMAIN: Final = "aquarium_ai"

# Configuration constants
CONF_TANK_NAME: Final = "tank_name"
CONF_AQUARIUM_TYPE: Final = "aquarium_type"
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_PH_SENSOR: Final = "ph_sensor"
CONF_SALINITY_SENSOR: Final = "salinity_sensor"
CONF_DISSOLVED_OXYGEN_SENSOR: Final = "dissolved_oxygen_sensor"
CONF_WATER_LEVEL_SENSOR: Final = "water_level_sensor"
CONF_ORP_SENSOR: Final = "orp_sensor"
CONF_CAMERA: Final = "camera"
CONF_UPDATE_FREQUENCY: Final = "update_frequency"
CONF_AI_TASK: Final = "ai_task"
CONF_AUTO_NOTIFICATIONS: Final = "auto_notifications"
CONF_NOTIFICATION_FORMAT: Final = "notification_format"
CONF_TANK_VOLUME: Final = "tank_volume"
CONF_FILTRATION: Final = "filtration"
CONF_WATER_CHANGE_FREQUENCY: Final = "water_change_frequency"
CONF_INHABITANTS: Final = "inhabitants"
CONF_LAST_WATER_CHANGE: Final = "last_water_change"
CONF_MISC_INFO: Final = "misc_info"
CONF_RUN_ANALYSIS_ON_STARTUP: Final = "run_analysis_on_startup"

# Parameter analysis toggle configuration constants
CONF_ANALYZE_TEMPERATURE: Final = "analyze_temperature"
CONF_ANALYZE_PH: Final = "analyze_ph"
CONF_ANALYZE_SALINITY: Final = "analyze_salinity"
CONF_ANALYZE_DISSOLVED_OXYGEN: Final = "analyze_dissolved_oxygen"
CONF_ANALYZE_WATER_LEVEL: Final = "analyze_water_level"
CONF_ANALYZE_ORP: Final = "analyze_orp"

# AI Prompt Configuration constants
CONF_PROMPT_MAIN_INSTRUCTIONS: Final = "prompt_main_instructions"
CONF_PROMPT_PARAMETER_GUIDELINES: Final = "prompt_parameter_guidelines"
CONF_PROMPT_CAMERA_INSTRUCTIONS: Final = "prompt_camera_instructions"
CONF_PROMPT_BRIEF_ANALYSIS: Final = "prompt_brief_analysis"
CONF_PROMPT_DETAILED_ANALYSIS: Final = "prompt_detailed_analysis"
CONF_PROMPT_WATER_CHANGE: Final = "prompt_water_change"
CONF_PROMPT_OVERALL_ANALYSIS: Final = "prompt_overall_analysis"

# Default values
DEFAULT_TANK_NAME: Final = "My Aquarium"
DEFAULT_AQUARIUM_TYPE: Final = "Freshwater"
DEFAULT_FREQUENCY: Final = "1_hour"
DEFAULT_AUTO_NOTIFICATIONS: Final = True
DEFAULT_NOTIFICATION_FORMAT: Final = "detailed"
DEFAULT_TANK_VOLUME: Final = ""
DEFAULT_FILTRATION: Final = ""
DEFAULT_WATER_CHANGE_FREQUENCY: Final = ""
DEFAULT_INHABITANTS: Final = ""
DEFAULT_MISC_INFO: Final = ""
DEFAULT_RUN_ANALYSIS_ON_STARTUP: Final = False

# Default values for parameter analysis toggles (all enabled by default)
DEFAULT_ANALYZE_TEMPERATURE: Final = True
DEFAULT_ANALYZE_PH: Final = True
DEFAULT_ANALYZE_SALINITY: Final = True
DEFAULT_ANALYZE_DISSOLVED_OXYGEN: Final = True
DEFAULT_ANALYZE_WATER_LEVEL: Final = True
DEFAULT_ANALYZE_ORP: Final = True

# Update frequency options (in minutes)
UPDATE_FREQUENCIES: Final = {
    "1_hour": 60,
    "2_hours": 120,
    "4_hours": 240,
    "6_hours": 360,
    "12_hours": 720,
    "daily": 1440,
    "never": None,  # Manual analysis only
}

# Notification format options
NOTIFICATION_FORMATS: Final = {
    "detailed": "Full and detailed evaluation",
    "condensed": "Condensed version with brief analysis", 
    "minimal": "Minimal with parameters and overall analysis only"
}

# Default AI Prompts
DEFAULT_PROMPT_MAIN_INSTRUCTIONS: Final = """Provide analysis for this {aquarium_type} aquarium.

Consider the relationships between different parameters.
Consider impact on aquarium health when the parameters are negative to the aquarium health.
Consider the bioload from inhabitants and whether filtration is adequate.
Consider the water change schedule and whether it's sufficient for the current bioload.
If last water change date is provided, factor in the time elapsed when making water change recommendations.
Consider any additional information provided in the context.
Always correctly write ph as pH."""

DEFAULT_PROMPT_PARAMETER_GUIDELINES: Final = """When considering the parameters, use the following guidelines for healthy ranges:
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
- pH: Typically has no units (pure number scale 0-14)"""

DEFAULT_PROMPT_CAMERA_INSTRUCTIONS: Final = """If an aquarium camera image is provided:
- Analyze the visual aspects of the aquarium focusing on:
  * Water clarity and quality (cloudy, clear, tinted, etc.) - NO NUMERICAL ANALYSIS
  * Fish identification and count if visible (species, behavior, health appearance)
  * Plant health and growth if visible
  * Equipment visibility and condition
  * Overall aquarium aesthetics and cleanliness
  * Any visible algae, debris, or maintenance needs
- Focus only on aquarium-related observations that can be determined visually
- Do not attempt to provide numerical measurements from the image
- Integrate visual observations with sensor data when drawing conclusions

For camera_visual_analysis: Provide a brief 1-2 sentence summary of visual observations (under 200 characters).
For camera_visual_notification_analysis: Provide detailed visual analysis with specific observations and recommendations."""

DEFAULT_PROMPT_BRIEF_ANALYSIS: Final = """For sensor analysis fields (ending with '_analysis'):
- Provide brief 1-2 sentence analysis under 200 characters
- Focus on current status and immediate concerns only"""

DEFAULT_PROMPT_DETAILED_ANALYSIS: Final = """For notification analysis fields (ending with '_notification_analysis'):
- Provide detailed analysis of the parameter
- Include current status, potential issues, relationships with other parameters
- Provide recommendations for improvement only if the parameter is negative to the aquarium health, do not mention if everything is fine. If there are no concerns, issues or recommendations simply state that the parameter is within optimal range."""

DEFAULT_PROMPT_WATER_CHANGE: Final = """For water_change_recommended: Answer 'Yes' or 'No' with a brief reason considering all factors (under 150 characters).
For water_change_recommendation: Keep it concise. State whether a water change is needed, and if so, specify the percentage and when (e.g., '30% within 2-3 days'). If not needed now, mention when the next scheduled change is due. Do not include generic text about benefits like 'to replenish minerals', 'to maintain optimal conditions', or explanations about why water changes are important. Focus only on the specific need and timing based on current parameters, bioload, filtration, water change schedule, and time since last change."""

DEFAULT_PROMPT_OVERALL_ANALYSIS: Final = """For overall_analysis: Brief 1-2 sentence health assessment under 200 characters.
For overall_notification_analysis: Detailed but short paragraph assessment without character limits."""