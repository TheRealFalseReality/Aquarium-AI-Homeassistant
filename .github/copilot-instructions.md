# Copilot Instructions for Aquarium AI Home Assistant Integration

## Project Overview

This is a **Home Assistant custom integration** called **Aquarium AI** (domain: `aquarium_ai`). It uses Home Assistant's built-in `ai_task` service to perform AI-powered analysis of aquarium sensor data and optional camera feeds, providing natural-language health assessments, water change recommendations, and persistent notifications.

The integration is distributed via **HACS** (Home Assistant Community Store) and has no Python package dependencies beyond Home Assistant itself.

---

## Repository Structure

```
custom_components/aquarium_ai/   # Main integration code
├── __init__.py                  # Integration setup, core AI analysis logic, helper functions
├── config_flow.py               # Multi-step UI configuration flow (ConfigFlow + OptionsFlow)
├── const.py                     # All constants, defaults, and default AI prompts
├── manifest.json                # Integration metadata (domain, version, dependencies)
├── sensor.py                    # Sensor entities (AI analysis text sensors, per-parameter + overall)
├── binary_sensor.py             # Binary sensors (water change needed, parameter problem)
├── button.py                    # Button entity (Run Analysis)
├── select.py                    # Select entities (Update Frequency, Notification Format)
├── switch.py                    # Switch entities (auto-notifications, per-parameter analysis toggles)
├── services.yaml                # Service definitions (run_analysis, run_analysis_for_aquarium)
├── strings.json                 # Default English UI strings
└── translations/
    ├── en.json                  # English translations
    ├── de.json                  # German translations
    └── template.json            # Template for new translations

.github/
├── workflows/
│   ├── hassfest.yaml            # Validates integration against Home Assistant standards
│   └── validate.yml             # HACS validation + hassfest
└── ISSUE_TEMPLATE/
    ├── bug_report.md
    └── feature_request.md

hacs.json                        # HACS metadata
README.md                        # User-facing documentation
CONTRIBUTING.md                  # Contribution guidelines
TRANSLATION_GUIDE.md             # Instructions for adding translations
```

---

## Key Architecture Concepts

### Integration Setup Flow
1. `async_setup_entry` in `__init__.py` is the main entry point
2. It forwards setup to all platforms: `sensor`, `binary_sensor`, `switch`, `select`, `button`
3. Schedules periodic AI analysis using `async_track_time_interval`
4. Optionally runs analysis on startup (60-second delay via `async_call_later`)
5. Registers `run_analysis` and `run_analysis_for_aquarium` services

### AI Analysis Pipeline (`__init__.py: send_ai_aquarium_analysis`)
1. Collects sensor data from configured HA sensor entities using `get_sensor_info()`
2. Checks per-parameter analysis toggle switches (stored in `entry.data`)
3. Builds a structured prompt using configurable AI prompt templates from `const.py`
4. Calls `ai_task.generate_data` service with a structured response schema
5. Stores the AI response in `hass.data[DOMAIN][entry_id]["sensor_analysis"]`
6. Sends a `persistent_notification` (if auto-notifications enabled)
7. Triggers state updates on sensor entities via `async_write_ha_state()`

### Shared Data Pattern
Entities read AI analysis results from `hass.data[DOMAIN][entry_id]["sensor_analysis"]` — a dict populated after each AI call. Sensor entities poll this dict on `async_update()`.

### Config Entry Data Storage
All configuration (sensors, toggles, AI prompts, tank info) is stored directly in `config_entry.data`. The options flow updates `entry.data` directly via `hass.config_entries.async_update_entry()` — it does **not** use `entry.options`.

---

## Entity Naming Conventions

All entities are named with the tank name as a prefix:
- `{tank_name} Temperature Analysis` (sensor)
- `{tank_name} Water Change Needed` (binary sensor)
- `{tank_name} Run Analysis` (button)
- `{tank_name} Update Frequency` (select)
- `{tank_name} Analyze Temperature` (switch)

Unique IDs follow the pattern: `{entry_id}_{descriptor}` (e.g., `{entry_id}_temperature_analysis`).

All entities share the same device under:
```python
{"identifiers": {(DOMAIN, config_entry.entry_id)}, "name": f"Aquarium AI - {tank_name}"}
```

---

## AI Response Structure

The AI call uses `ai_task.generate_data` with a `structure` dict. Response keys follow these patterns:
- `{param_name_snake_case}_analysis` — brief (≤200 chars), used for sensor state
- `{param_name_snake_case}_notification_analysis` — detailed, used in notifications
- `overall_analysis` / `overall_notification_analysis` — overall health
- `water_change_recommended` — `"Yes/No + brief reason"` (drives binary sensor state)
- `water_change_recommendation` — detailed recommendation for notifications
- `camera_visual_analysis` / `camera_visual_notification_analysis` — visual analysis (only if camera configured and toggle enabled)

Sensor states are capped at 255 characters (truncated with `...`).

---

## Adding New Parameters or Sensors

When adding a new sensor type (e.g., Ammonia), you must update **all** of the following:
1. `const.py` — Add `CONF_*_SENSOR`, `CONF_ANALYZE_*`, `DEFAULT_ANALYZE_*`
2. `__init__.py` — Add to `sensor_mappings` list in `async_setup_entry`
3. `sensor.py` — Add to `sensor_mappings` in `async_setup_entry`
4. `binary_sensor.py` — Add to `sensor_mappings`
5. `switch.py` — Add to `parameter_switches` list
6. `config_flow.py` — Add `EntitySelector` to sensors step schema in both `AquariumAIConfigFlow` and `AquariumAIOptionsFlow._get_sensors_schema()`
7. `strings.json` — Add label and description for the new sensor field
8. `translations/en.json` — Mirror the strings.json changes
9. `translations/template.json` — Add the translation key

---

## Validation and CI

There are **no unit tests** in this repository. All testing is done manually in a real Home Assistant environment.

CI runs two checks via GitHub Actions:
- **`hassfest`** (`hassfest.yaml`): Validates integration metadata, manifest, translations, and strings against HA standards
- **`HACS validation`** (`validate.yml`): Validates HACS-specific requirements

To validate locally, you can run hassfest in a Home Assistant dev environment:
```bash
python -m script.hassfest
```

There is no `requirements.txt`, `pyproject.toml`, or linting configuration — the project relies on HA's built-in validation.

---

## Translation System

- `strings.json` is the source of truth for UI text keys
- `translations/en.json` must mirror `strings.json` exactly
- `translations/template.json` is a template for translators
- New translation files go in `translations/{lang_code}.json`
- Hassfest validates that translations match the structure defined in `strings.json`

When modifying UI-visible text (config flow steps, labels, descriptions, error messages):
1. Update `strings.json`
2. Update `translations/en.json` with the same change
3. Update `translations/template.json`
4. Update any other existing translation files if the key structure changes

---

## Debug Logging

To enable debug logging in Home Assistant, add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.aquarium_ai: debug
```

All modules use `_LOGGER = logging.getLogger(__name__)`.

---

## Common Errors and Workarounds

- **`sensor_not_found` error in config flow**: The sensor entity provided does not exist in HA states. Validate that the entity is available before saving.
- **`ai_task_required` error**: The `ai_task` entity ID was not provided. It is mandatory for the integration to function.
- **`at_least_one_sensor` error**: At least one sensor entity must be configured.
- **Sensor state truncation**: AI responses longer than 255 characters are automatically truncated to 252 chars + `...` before storing in sensor state.
- **Options flow saves to `entry.data` directly**: Unlike typical HA patterns that use `entry.options`, this integration saves all settings directly into `entry.data` via `async_update_entry`. Do not introduce `entry.options` usage without updating all consumers.
- **No `PLATFORMS` list**: Platform names are hardcoded as a list `["sensor", "binary_sensor", "switch", "select", "button"]` in `async_setup_entry` and `async_unload_entry`.
- **Hassfest validation failures**: Commonly caused by mismatched keys between `strings.json` and `translations/en.json`, or invalid `manifest.json` fields. Always sync these files after changes.

---

## Version and Release

The integration version is defined in `manifest.json` (`"version": "1.2.1"`). Update this when releasing new versions. HACS uses GitHub releases — create a release tag matching the version string.

---

## Home Assistant Coding Conventions

- All setup functions are `async` and prefixed with `async_`
- `async_setup_entry` / `async_unload_entry` are the standard HA entry points
- Use `entry.data.get(KEY, DEFAULT)` pattern for safe config access
- `hass.config_entries.async_update_entry()` is used for runtime config changes
- Entity state must be written via `self.async_write_ha_state()` after mutations
- `_LOGGER` is module-level, not class-level
- Use `vol.Schema` with `voluptuous` for config validation
- Selectors come from `homeassistant.helpers.selector`
