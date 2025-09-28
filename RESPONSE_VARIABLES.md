# Aquarium AI Response Variables

This document describes the response variables exposed by the Aquarium AI integration for use in custom automations and scripts.

## Overview

The Aquarium AI integration now exposes comprehensive response variables that allow users to access both condensed and full AI analysis data in their Home Assistant automations. These response variables provide programmatic access to all the AI analysis results, making it easy to create custom notifications, triggers, and actions based on aquarium conditions.

## Available Response Variable Sensors

### 1. Full AI Response Sensor

**Entity ID**: `sensor.[tank_name]_full_ai_response`

This sensor provides comprehensive access to all AI analysis data in a structured format ideal for automations.

#### State
- Shows a summary like "Analysis available (6 parameters)"
- State indicates how many parameters have analysis data

#### Attributes
```yaml
sensor_responses:
  temperature:
    sensor_name: "Temperature"
    condensed_analysis: "Brief 1-2 sentence analysis"
    full_analysis: "Detailed comprehensive analysis"
    sensor_value: "24.5°C"
    raw_value: 24.5
    unit: "°C"
  ph:
    sensor_name: "pH"
    condensed_analysis: "Brief pH analysis"
    full_analysis: "Detailed pH analysis with recommendations"
    sensor_value: "8.2"
    raw_value: 8.2
    unit: ""
  # ... additional sensors
overall_condensed_analysis: "Brief overall tank assessment"
overall_full_analysis: "Detailed overall analysis with recommendations"
analysis_timestamp: "2025-01-03T10:30:00"
aquarium_type: "Marine"
total_sensors: 6
response_format: "full_detailed"
```

### 2. Detailed Individual Sensor Analysis

**Entity ID**: `sensor.[tank_name]_[sensor_name]_detailed_analysis`

These sensors provide the full, detailed AI analysis for each individual parameter (temperature, pH, salinity, etc.).

#### State
- Contains the full detailed AI analysis text (no character limit)
- Falls back to condensed analysis if detailed not available
- Falls back to simple status if no AI analysis available

#### Attributes
```yaml
sensor_name: "Temperature"
sensor_value: "24.5°C"
raw_value: 24.5
unit: "°C"
source_entity: "sensor.aquarium_temperature"
analysis_source: "AI_Detailed"  # or "AI_Condensed" or "Fallback"
condensed_analysis: "Brief analysis version"
full_analysis: "Full detailed analysis version"
aquarium_type: "Marine"
last_updated: "2025-01-03T10:30:00"
analysis_type: "detailed"
```

### 3. Overall Detailed Analysis

**Entity ID**: `sensor.[tank_name]_overall_detailed_analysis`

This sensor provides the comprehensive overall aquarium assessment.

#### State
- Contains the full detailed overall analysis
- Includes comprehensive assessment of all parameters and their relationships

#### Attributes
```yaml
sensors:
  Temperature:
    value: "24.5°C"
    raw_value: 24.5
    unit: "°C"
    status: "Good"
  pH:
    value: "8.2"
    raw_value: 8.2
    unit: ""
    status: "Good"
  # ... additional sensors
total_sensors: 6
aquarium_type: "Marine"
analysis_source: "AI_Detailed"
condensed_analysis: "Brief overall assessment"
detailed_analysis: "Full comprehensive overall analysis"
last_updated: "2025-01-03T10:30:00"
ai_task: "ai_task.your_provider"
analysis_type: "detailed_overall"
```

## Response Data Types

### Condensed vs Full Analysis

- **Condensed Analysis**: Brief 1-2 sentence summaries (under 200 characters) optimized for sensor display
- **Full Analysis**: Comprehensive detailed analysis with explanations, recommendations, and contextual information

### Analysis Sources

The `analysis_source` attribute indicates the source of the analysis:
- `AI_Detailed`: Full AI analysis from notification analysis
- `AI_Condensed`: Brief AI analysis from sensor analysis
- `Fallback`: Simple status-based analysis when AI is unavailable

## Usage Examples

### Example 1: Custom Notification Based on Temperature Analysis

```yaml
automation:
  - alias: "Custom Temperature Alert"
    trigger:
      - platform: state
        entity_id: sensor.main_tank_temperature_detailed_analysis
    condition:
      - condition: template
        value_template: >
          {{ 'concern' in trigger.to_state.state.lower() or 
             'high' in trigger.to_state.state.lower() or
             'low' in trigger.to_state.state.lower() }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🌡️ Temperature Issue Detected"
          message: >
            Tank: {{ state_attr('sensor.main_tank_temperature_detailed_analysis', 'sensor_name') }}
            Current: {{ state_attr('sensor.main_tank_temperature_detailed_analysis', 'sensor_value') }}
            
            Analysis: {{ states('sensor.main_tank_temperature_detailed_analysis') }}
```

### Example 2: Automation Using Full Response Data

```yaml
automation:
  - alias: "Comprehensive Tank Check"
    trigger:
      - platform: state
        entity_id: sensor.main_tank_full_ai_response
    action:
      - service: script.process_tank_analysis
        data:
          tank_data: >
            {{
              {
                'overall_analysis': state_attr('sensor.main_tank_full_ai_response', 'overall_full_analysis'),
                'temperature': state_attr('sensor.main_tank_full_ai_response', 'sensor_responses')['temperature'],
                'ph': state_attr('sensor.main_tank_full_ai_response', 'sensor_responses')['ph'],
                'timestamp': state_attr('sensor.main_tank_full_ai_response', 'analysis_timestamp')
              }
            }}
```

### Example 3: Conditional Logic Based on Analysis Type

```yaml
automation:
  - alias: "Analysis Quality Check"
    trigger:
      - platform: state
        entity_id: sensor.main_tank_overall_detailed_analysis
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.main_tank_overall_detailed_analysis', 'analysis_source') == 'AI_Detailed' }}
    action:
      - service: persistent_notification.create
        data:
          title: "High Quality Analysis Available"
          message: >
            Detailed AI analysis completed for {{ state_attr('sensor.main_tank_overall_detailed_analysis', 'total_sensors') }} sensors.
            
            {{ states('sensor.main_tank_overall_detailed_analysis') }}
```

### Example 4: Data Extraction for External Processing

```yaml
script:
  extract_analysis_data:
    sequence:
      - variables:
          full_response: "{{ state_attr('sensor.main_tank_full_ai_response', 'sensor_responses') }}"
          timestamp: "{{ state_attr('sensor.main_tank_full_ai_response', 'analysis_timestamp') }}"
      - repeat:
          for_each: "{{ full_response.keys() }}"
          sequence:
            - service: logbook.log
              data:
                name: "Aquarium Analysis"
                message: >
                  Parameter: {{ full_response[repeat.item]['sensor_name'] }}
                  Value: {{ full_response[repeat.item]['sensor_value'] }}
                  Analysis: {{ full_response[repeat.item]['full_analysis'] }}
                entity_id: sensor.main_tank_full_ai_response
```

## Template Sensors

You can create custom template sensors to extract specific information:

### Example: Temperature Status Template

```yaml
template:
  - sensor:
      - name: "Tank Temperature Status"
        state: >
          {% set temp_data = state_attr('sensor.main_tank_full_ai_response', 'sensor_responses')['temperature'] %}
          {% if 'optimal' in temp_data['full_analysis'].lower() %}
            Optimal
          {% elif 'concern' in temp_data['full_analysis'].lower() %}
            Concerning
          {% else %}
            Unknown
          {% endif %}
        attributes:
          current_temp: >
            {{ state_attr('sensor.main_tank_full_ai_response', 'sensor_responses')['temperature']['sensor_value'] }}
          analysis: >
            {{ state_attr('sensor.main_tank_full_ai_response', 'sensor_responses')['temperature']['full_analysis'] }}
```

## Best Practices

1. **Check Analysis Source**: Always verify the `analysis_source` to ensure you're getting the quality of analysis you expect.

2. **Handle Missing Data**: Use template conditions to handle cases where AI analysis might not be available.

3. **Use Appropriate Analysis Type**: 
   - Use condensed analysis for simple status checks
   - Use full analysis for detailed decision making and notifications

4. **Monitor Update Frequency**: The response variables update according to your configured analysis frequency.

5. **Error Handling**: Include fallback logic for when sensors are unavailable or analysis fails.

## Troubleshooting

### Common Issues

1. **Empty Response Variables**: Check that the AI task is properly configured and functioning.

2. **Outdated Data**: Verify the `last_updated` timestamp to ensure data freshness.

3. **Missing Sensor Data**: Check that individual sensors are available and reporting valid data.

### Debugging Templates

Use this template to inspect the full response structure:

```yaml
template:
  - sensor:
      - name: "Debug Full Response"
        state: "{{ states('sensor.main_tank_full_ai_response') }}"
        attributes:
          full_attributes: "{{ state_attr('sensor.main_tank_full_ai_response', 'sensor_responses') | tojsonpretty }}"
```

## Migration from Previous Versions

If you were previously using individual analysis sensors, the new response variables provide backward compatibility while offering enhanced functionality:

- **Existing sensors continue to work** (condensed analysis)
- **New detailed sensors** provide full analysis text
- **Full response sensor** provides structured access to all data
- **Backward compatible** with existing automations

## Support

For questions or issues with response variables:

1. Check the Home Assistant logs for any error messages
2. Verify AI task integration is working properly
3. Ensure sensors are reporting valid data
4. Review the response variable attributes for debugging information

The response variables are designed to be flexible and powerful, enabling sophisticated aquarium monitoring and automation scenarios while maintaining simplicity for basic use cases.