"""The Aquarium AI integration."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import AquariumAIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aquarium AI from a config entry."""
    _LOGGER.debug("Setting up Aquarium AI integration with entry: %s", entry.data)
    
    coordinator = AquariumAIDataUpdateCoordinator(hass, entry)
    
    _LOGGER.debug("Performing initial coordinator refresh")
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    _LOGGER.debug("Coordinator stored in hass.data")

    _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the custom service
    async def update_analysis_service(service: ServiceCall):
        """Service to trigger an update of the Aquarium AI data."""
        _LOGGER.debug("Manual update service called")
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "update_analysis", update_analysis_service
    )
    _LOGGER.debug("Registered update_analysis service")

    # Trigger an immediate update to populate sensors right after setup
    _LOGGER.debug("Triggering immediate data update after setup")
    try:
        await coordinator.async_request_refresh()
        _LOGGER.debug("Initial data update completed successfully")
    except Exception as e:
        _LOGGER.warning("Initial data update failed, will retry on schedule: %s", e)

    _LOGGER.info("Aquarium AI integration setup completed successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Aquarium AI integration")
    
    # Unregister the service
    hass.services.async_remove(DOMAIN, "update_analysis")
    _LOGGER.debug("Removed update_analysis service")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Successfully unloaded Aquarium AI integration")

    return unload_ok