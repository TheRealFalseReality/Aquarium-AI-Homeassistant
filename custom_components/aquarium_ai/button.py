"""Button platform for Aquarium AI integration."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquarium AI buttons from a config entry."""
    tank_name = config_entry.data["tank_name"]
    
    entities = []
    
    # Create run analysis button
    entities.append(
        RunAnalysisButton(
            hass,
            config_entry,
            tank_name,
        )
    )
    
    async_add_entities(entities)


class RunAnalysisButton(ButtonEntity):
    """Button to trigger AI analysis for the aquarium."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        tank_name: str,
    ):
        """Initialize the button."""
        self._hass = hass
        self._config_entry = config_entry
        self._tank_name = tank_name
        self._attr_name = f"{tank_name} Run Analysis"
        self._attr_unique_id = f"{config_entry.entry_id}_run_analysis"
        self._attr_icon = "mdi:brain"
        
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
    
    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Running manual AI analysis for %s", self._tank_name)
        
        # Get the analysis function from hass.data
        if (
            DOMAIN in self._hass.data
            and self._config_entry.entry_id in self._hass.data[DOMAIN]
        ):
            entry_data = self._hass.data[DOMAIN][self._config_entry.entry_id]
            analysis_function = entry_data.get("analysis_function")
            
            if analysis_function:
                try:
                    # Send notification by default when button is pressed
                    await analysis_function(None, override_notification=True)
                    _LOGGER.info("Successfully triggered analysis for %s", self._tank_name)
                except Exception as err:
                    _LOGGER.error(
                        "Failed to run analysis for %s: %s",
                        self._tank_name,
                        err
                    )
            else:
                _LOGGER.error(
                    "Analysis function not found for %s",
                    self._tank_name
                )
        else:
            _LOGGER.error(
                "Entry data not found for %s",
                self._tank_name
            )
