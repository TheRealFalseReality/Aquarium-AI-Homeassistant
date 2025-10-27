# Aquarium AI for Home Assistant

![Aquarium AI](/assets/logo.png)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

**Aquarium AI** is a custom integration for [Home Assistant](https://www.home-assistant.io/) that uses the power of AI to analyze the conditions of your aquarium. It dynamically evaluates your existing sensors and camera feeds, providing clear text-based analyses of both quantitative sensor data and qualitative visual observations.

This integration takes the guesswork out of maintaining a healthy aquatic environment by turning raw sensor data and visual monitoring into actionable insights.

> [!WARNING]
> **AI Disclaimer**: While this integration leverages advanced AI technology to analyze your aquarium conditions, please remember that AI can sometimes get things wrong. The AI-generated analyses and recommendations should be used as helpful guidance, but should not replace your own expertise, professional advice, or careful observation of your aquarium. Always verify AI suggestions against your knowledge of aquarium care and consult with aquarium professionals when making important decisions about your aquatic environment.

---

## Features

* **AI-Powered Analysis**: Leverages the built-in `ai_task` service to generate natural language analyses of your aquarium's conditions.
* **Dynamic Entity Creation**: Automatically creates text sensors for each AI analysis point (e.g., temperature, pH, overall health) based on the sensors you provide.
* **Water Change Recommendations**: AI evaluates when water changes are needed based on parameters, bioload, filtration, and maintenance schedule.
* **Context-Aware Analysis**: Optionally provide tank volume, filtration details, inhabitants, and maintenance history for more accurate recommendations.
* **Camera Visual Analysis**: Optional camera integration for AI-powered visual monitoring of water clarity, fish health, plant condition, and maintenance needs.
* **Binary Sensors**: Simple on/off indicators for water change needs and other critical conditions.
* **UI Configuration**: Simple setup process through the Home Assistant UI. No YAML configuration is required.
* **Customizable Polling**: Choose how often the AI analysis should run, from every hour to once a day.
* **On-Demand Updates**: Trigger an analysis at any time using a service call, perfect for automations and custom schedules.
* **Multiple Notification Formats**: Choose between detailed, condensed, or minimal notification styles.

---

## Prerequisites

> [!IMPORTANT]
> *Important Notice Regarding Home Assistant AI Tasks feature*:  
> **You must have a generative LLM AI installed in you Home Assistant via integrations (see link below), this typially creates an `ai_task.YOUR_PROVIDER` for this integration to use.**
>
Before you can install and use Aquarium AI, you must have the following set up:  

1. A working **Home Assistant** instance (Version 2025.1.0+).
2. **HACS (Home Assistant Community Store)** installed.  
3. The core **`ai_task`** integration must be enabled and configured in Home Assistant. This integration will not work without it. [**AI Task Documentation**](https://www.home-assistant.io/integrations/ai_task)
4. One or more **aquarium-related sensors** (e.g., temperature, pH, salinity, etc.) available in Home Assistant.
5. Optionally, one or more **camera entities** for visual monitoring of your aquarium.

---

## Installation

### Method 1: HACS (Recommended)

1. Navigate to the **HACS** section in your Home Assistant.
2. Click on **Integrations**, then click the three-dots menu in the top-right and select **"Custom repositories"**.
3. Add the URL to this GitHub repository in the "Repository" field.
4. Select **"Integration"** for the category and click **"Add"**.
5. The "Aquarium AI" integration will now appear in your HACS list. Click on it and then click **"Download"**.
6. Restart Home Assistant when prompted.

### Method 2: Manual Installation

1. Download the latest release from the [Releases page](https://github.com/TheRealFalseReality/Aquarium-AI-Homeassistant/releases).
2. Unzip the downloaded file.
3. Copy the `aquarium_ai` folder (from within the `custom_components` directory) into your Home Assistant's `config/custom_components/` directory.
4. Restart Home Assistant.

---

## Configuration

Once installed, the integration must be configured through the UI.

1. Navigate to **Settings** -> **Devices & Services**.
2. Click the **"+ Add Integration"** button in the bottom right.
3. Search for **"Aquarium AI"** and click on it.
4. A configuration dialog will appear. You will be asked to provide:
   * **Aquarium Name**: A custom name for your tank (e.g., "Main Tank", "Reef Setup").
   * **Aquarium Type**: Select the type of your aquarium (e.g., Marine, Freshwater, Reef).
   * **AI Task**: Choose the AI task entity to use for analysis (e.g., ai_task.google_ai_task).
   * **Update Frequency**: Choose how often you want the analysis to run automatically.
   * **Auto-send Notifications**: Enable or disable automatic notifications.
   * **Notification Format**: Choose between detailed, condensed, or minimal notification styles.
   * **Sensors**: Select the sensor entities you wish for the AI to analyze (temperature, pH, salinity, dissolved oxygen, water level, ORP).
   * **Camera** (Optional): Select a camera entity for visual analysis of water quality, fish health, and maintenance needs.
   
   **Enhanced Tank Context (Optional - Recommended for Better AI Analysis):**
   * **Tank Volume**: Enter your aquarium's total water volume (e.g., "100 liters", "50 gallons").
   * **Filtration System**: Describe your filter setup including type, flow rate, and media (e.g., "Canister filter 1200 L/h with bio-media").
   * **Water Change Frequency**: Specify your maintenance schedule (e.g., "25% weekly", "20% every 2 weeks").
   * **Tank Inhabitants**: List your fish, invertebrates, and plants with quantities (e.g., "10 Neon Tetras, 5 Corydoras, 20 Cherry Shrimp").
   * **Last Water Change Date**: Select an input_datetime helper or sensor tracking your last water change (see setup instructions below).
   * **Additional Information**: Add any other context (e.g., "Recently added new fish", "Using CO2 injection").
   
5. Click **"Submit"**. The integration will set up all the necessary entities.

### Setting Up Last Water Change Tracking

To enable the AI to consider time since your last water change, you need to create a helper:

1. Navigate to **Settings** -> **Devices & Services** -> **Helpers**.
2. Click **"+ Create Helper"** and select **"Date and/or time"**.
3. Configure the helper:
   * **Name**: "Last Water Change" (or your preferred name)
   * **Icon**: `mdi:water-sync`
   * **Has date**: ✓ (checked)
   * **Has time**: ✓ (optional but recommended)
4. Click **"Create"**.
5. Update this helper's value whenever you perform a water change (manually or via automation).
6. In the Aquarium AI configuration, select this helper as the "Last Water Change Date" sensor.

**Pro Tip:** Create an automation to remind you to update this helper after each water change, or use a dashboard button to quickly update it.

---

## Usage & Entities

After configuration, the integration will create a new "Aquarium AI" device with several entities associated with it.

![Marine Sensors](/assets/Marinesensors.png)

### AI Analysis Sensors

These `sensor` entities contain AI-generated text analysis limited to 1-2 sentences (under 255 characters):

* `sensor.[tank_name]_[sensor_name]_analysis`: AI analysis of each specific parameter (e.g., Temperature Analysis, pH Analysis).
* `sensor.[tank_name]_overall_analysis`: Comprehensive AI summary of the aquarium's overall health.
* `sensor.[tank_name]_water_change_recommendation`: AI-powered water change recommendation with brief reasoning.

### Status Sensors

These `sensor` entities provide quick status information:

* `sensor.[tank_name]_simple_status`: Overall status message with emoji (e.g., "Your Marine Aquarium is Excellent! 🌟").
* `sensor.[tank_name]_quick_status`: One or two-word status (e.g., "Excellent", "Good", "Needs Attention").
* `sensor.[tank_name]_[sensor_name]_status`: Status for each parameter with current value (e.g., "Good (24.5°C)").

### Binary Sensors

These `binary_sensor` entities provide simple on/off states:

* `binary_sensor.[tank_name]_water_change_needed`: Indicates whether a water change is currently recommended (On = Yes, Off = No).

![Sensors](/assets/sensors_example.png)

### Notification System

The integration also sends periodic notifications (if enabled) with detailed analysis including:

* Overall status summary
* Current sensor readings with icons
* Detailed AI analysis for each parameter
* Visual observations from camera (if configured)
* **Water change recommendations** based on parameters, bioload, and maintenance schedule
* Recommendations when needed

#### Example Notifications

<table>
  <tr>
    <th>Marine Aquarium</th>
    <th>Reef Aquarium</th>
    <th>Cichlids Aquarium</th>
  </tr>
  <tr>
    <td><img src="assets/Marine.png" alt="Marine Notification" width="300"></td>
    <td><img src="assets/Reef.png" alt="Reef Notification" width="300"></td>
    <td><img src="assets/Cichlids.png" alt="Cichlids Notification" width="300"></td>
  </tr>
</table>

**Notification Types:**

<table>
  <tr>
    <th>Condensed</th>
    <th>Minimal</th>
  </tr>
  <tr>
    <td><img src="assets/NotificationCondensed.png" alt="Condensed Notification" width="400"></td>
    <td><img src="assets/Noticationmin.png" alt="Minimal Notification" width="400"></td>
  </tr>
</table>

---

## Camera Visual Analysis

When a camera is configured, the AI will analyze images from your aquarium camera to provide additional insights:

### Visual Monitoring Capabilities

* **Water Quality Assessment**: Analyzes water clarity, color, and cloudiness without numerical measurements
* **Fish Health & Behavior**: Identifies fish species, counts visible fish, and observes behavioral patterns
* **Plant Health**: Monitors aquatic plant condition and growth patterns
* **Equipment Monitoring**: Checks visibility and apparent condition of equipment
* **Maintenance Alerts**: Identifies visible algae, debris, or cleanliness issues

### Integration with Sensor Data

Visual analysis complements sensor readings by providing context that numbers alone cannot capture. The AI combines both quantitative sensor data and qualitative visual observations to give you a complete picture of your aquarium's health.

**Note**: Camera analysis focuses on observable qualities rather than precise measurements, providing insights that enhance rather than replace your sensor monitoring.

---

## Advanced Usage: Service Call

The integration adds a service that allows you to trigger analysis updates manually. This is useful for creating automations based on specific events (e.g., after a water change).

**Service:** `aquarium_ai.run_analysis`

This service will:

* Update all AI analysis sensors with fresh analysis
* Update all status sensors with current readings  
* Send a notification (if notifications are enabled)

### Example Automations

#### Schedule Daily Analysis

This automation runs an analysis every day at 8:00 AM, overriding the schedule you chose in the config.

```yaml
automation:
  - alias: "Run Aquarium AI Analysis Daily at 8 AM"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: aquarium_ai.run_analysis
```

#### Water Change Reminder

Get notified when the AI recommends a water change:

```yaml
automation:
  - alias: "Notify When Water Change Needed"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_aquarium_water_change_needed
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "🐠 Aquarium Maintenance"
          message: >
            Water change recommended for {{ state_attr('binary_sensor.my_aquarium_water_change_needed', 'recommendation') }}
```

#### Update Last Water Change After Maintenance

Automatically update your water change tracker when you perform maintenance:

```yaml
automation:
  - alias: "Update Last Water Change"
    trigger:
      - platform: event
        event_type: call_service
        event_data:
          domain: input_boolean
          service: turn_on
          service_data:
            entity_id: input_boolean.water_change_completed
    action:
      - service: input_datetime.set_datetime
        target:
          entity_id: input_datetime.last_water_change
        data:
          datetime: "{{ now().strftime('%Y-%m-%d %H:%M:%S') }}"
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.water_change_completed
```

---

## Water Change Recommendations

The integration now includes intelligent water change recommendations based on:

* **Current Water Parameters**: Evaluates if parameters are trending towards unsafe levels
* **Tank Volume**: Calculates appropriate water change percentages
* **Bioload**: Considers fish/invertebrate population and waste production
* **Filtration Capacity**: Assesses if your filter can handle the current bioload
* **Water Change Schedule**: Factors in your maintenance frequency
* **Time Since Last Change**: Uses the elapsed time when the helper is configured

### How It Works

The AI analyzes all available information and provides:

1. **Binary Sensor** (`binary_sensor.[tank_name]_water_change_needed`): Simple on/off indicator
2. **Text Sensor** (`sensor.[tank_name]_water_change_recommendation`): Detailed recommendation with reasoning
3. **Notification Section**: Included in all notifications with specific guidance

**Example Recommendations:**
* "Yes - High nitrate levels suggest 40% change recommended within 2-3 days"
* "No - Parameters stable with current 25% weekly maintenance schedule"
* "Yes - It's been 10 days since last change, time for routine 30% water change"

---

### A Note on Development (Vibe Coding Disclaimer)

This integration is a passion project developed with a "just build it" philosophy. It's built iteratively as ideas and inspiration strike. While every effort is made to ensure it's stable and reliable, you might encounter unexpected quirks. Community feedback is a huge part of this process, so please don't hesitate to open an issue if you find a bug or have a great idea!

---

## Translations

Aquarium AI supports multiple languages to make it accessible to users worldwide! 

### Available Languages

- 🇬🇧 **English (en)** - Default
- 🇩🇪 **German (de)** - Deutsch

### Help Translate

We welcome community translations! If you'd like to translate Aquarium AI into your language:

1. Check the [Translation Guide](TRANSLATION_GUIDE.md) for detailed instructions
2. Copy the `custom_components/aquarium_ai/translations/template.json` file
3. Translate the strings to your language
4. Submit a Pull Request

Your translation will help make aquarium monitoring accessible to more users around the world! 🌍🐠

---

## Contributing

Contributions are welcome! Whether you want to translate the integration, report a bug, suggest a feature, or contribute code, we'd love your help!

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Links

- **🌍 Translations**: Help translate the integration into other languages → [Translation Guide](TRANSLATION_GUIDE.md)
- **🐛 Bug Reports**: Report issues → [Open an Issue](https://github.com/TheRealFalseReality/Aquarium-AI-Homeassistant/issues)
- **💡 Feature Requests**: Suggest new features → [Open an Issue](https://github.com/TheRealFalseReality/Aquarium-AI-Homeassistant/issues)
- **💻 Code Contributions**: Submit pull requests → [Contributing Guide](CONTRIBUTING.md)

## [AquaPi for ESPHome](https://github.com/TheRealFalseReality/aquapi)
<img width="120" alt="AquaPi Logo Blue" src="https://github.com/user-attachments/assets/762d1dad-4381-45a5-b74b-aac4bb446185" align="left"/>

The Aquarium meets the Smart Home! Add more sensors to Home Assisant! 

**[Setup Guide](https://github.com/TheRealFalseReality/aquapi/wiki/Setup-AquaPi)**  
**[Build It Yourself](https://github.com/TheRealFalseReality/aquapi/wiki/Build-It-Yourself)**  
**[Wiki](https://github.com/TheRealFalseReality/aquapi/wiki)**  

**[Join the conversation on Reef2Reef!](https://www.reef2reef.com/threads/aquapi-an-open-souce-aquarium-controller.1033171/)**  

### **[Buy Now!](https://www.capitalcityaquatics.com/store/aquapi)**

## [Aquarium AI App](https://play.google.com/store/apps/details?id=com.cca.fishai)
Your Intelligent Aquatic Assistant

Take the guesswork out of aquarium keeping with Aquarium AI! Our powerful, AI-driven tools help both new and seasoned aquarists create a thriving underwater ecosystem.

Unlock the Power of AI with Your Own API Key!

Aquarium AI is different from other AI-enabled aquarium apps. We empower you by allowing you to use your own AI API keys from Gemini, OpenAI, and Groq. This unique "Bring Your Own Key" model gives you:

Higher AI API Call Limits: Enjoy significantly more interactions with our AI, including the powerful Gemini 2.5 flash.

Unlimited Features: Get unrestricted access to all our features, including the ability to add and manage an unlimited number of tanks.

Key Features:

🤖 Intelligent AI Chatbot: Have a question about your tank? Get expert advice on water parameters, fish health, tank maintenance, and more, 24/7.

🧪 AI Fish Compatibility Tool: Instantly analyze the compatibility of different fish species with in-depth reports and personalized care guides.

🦐 AI Stocking Assistant: Plan your dream aquarium with confidence. Get custom stocking recommendations based on your tank size, experience level, and desired fish type.

🏠 My Tanks: Create and manage your custom tanks with inhabitants. Get personalized stocking recommendations for your tanks.

📸 Photo Analysis: Analyze photos of your fish and tank. Our AI can help identify species, detect potential health issues, and provide recommendations.

📐 Aquarium Calculators: Access essential tools for managing your aquarium's technical details, including a handy Tank Volume Calculator.

[<img width="413" height="122" alt="download" src="https://github.com/user-attachments/assets/24dc9415-94fa-4c65-bcef-f8d5897f7e09" />](https://play.google.com/store/apps/details?id=com.cca.fishai)

