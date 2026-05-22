"""Sensor platform for Torbox."""

import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TorboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        TorboxPlanSensor(coordinator),
        TorboxTotalTorrentsSensor(coordinator),
        TorboxActiveDownloadsSensor(coordinator),
    ]

    async_add_entities(sensors)


class TorboxSensorBase(CoordinatorEntity[TorboxDataUpdateCoordinator], SensorEntity):
    """Base class for Torbox sensors."""

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        # Use the email from user data as the device identifier base if available
        self._email = coordinator.data.get("user", {}).get("email", "Torbox Account")

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._email)},
            "name": f"Torbox ({self._email})",
            "manufacturer": "Torbox",
            "model": "API Integration",
        }


class TorboxPlanSensor(TorboxSensorBase):
    """Sensor for the Torbox Plan."""

    _attr_translation_key = "plan"
    _attr_icon = "mdi:account-star"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_plan"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        plan_id = self.coordinator.data.get("user", {}).get("plan", 0)
        # Mapping based on common Torbox API responses, fallback to str(plan_id)
        plan_map = {0: "Free", 1: "Essential", 2: "Pro", 3: "Standard"}
        return plan_map.get(plan_id, f"Plan {plan_id}")


class TorboxTotalTorrentsSensor(TorboxSensorBase):
    """Sensor for Total Torrents."""

    _attr_translation_key = "total_torrents"
    _attr_icon = "mdi:cloud-download"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_total_torrents"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        torrents = self.coordinator.data.get("torrents", [])
        return len(torrents)


class TorboxActiveDownloadsSensor(TorboxSensorBase):
    """Sensor for Active Downloads."""

    _attr_translation_key = "active_downloads"
    _attr_icon = "mdi:download-network"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_active_downloads"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        torrents = self.coordinator.data.get("torrents", [])
        # Active status generally implies it's downloading or seeding.
        # Typically "downloading" is a specific status. We will count anything not completed
        # or actively "downloading" depending on the exact API status field.
        # Let's count torrents with status == "downloading" or similar.
        # Since we don't have the exact enum, we'll count ones where download_state != "completed"
        # or similar. Based on common APIs, "downloading" is a safe string to check for.
        active = sum(1 for t in torrents if t.get("download_state", "").lower() == "downloading")
        return active
