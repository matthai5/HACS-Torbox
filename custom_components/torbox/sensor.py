"""Sensor platform for Torbox."""

import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
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
        Torbox30DayUsageSensor(coordinator),
        TorboxExpiresAtSensor(coordinator),
        TorboxCooldownSensor(coordinator),
        TorboxServerSensor(coordinator),
        TorboxTotalUsenetSensor(coordinator),
        TorboxActiveUsenetSensor(coordinator),
        TorboxTotalWebdlSensor(coordinator),
        TorboxActiveWebdlSensor(coordinator),
    ]

    async_add_entities(sensors)


class TorboxSensorBase(CoordinatorEntity[TorboxDataUpdateCoordinator], SensorEntity):
    """Base class for Torbox sensors."""

    _attr_has_entity_name = True

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

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the user properties as extra state attributes."""
        return self.coordinator.data.get("user", {})



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


class Torbox30DayUsageSensor(TorboxSensorBase):
    """Sensor for the Torbox 30-day usage."""

    _attr_translation_key = "usage_30_day"
    _attr_icon = "mdi:chart-donut"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.BYTES

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_usage_30_day"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("user", {}).get("total_downloaded")


class TorboxExpiresAtSensor(TorboxSensorBase):
    """Sensor for Premium Expiration Date."""

    _attr_translation_key = "premium_expires_at"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_premium_expires_at"

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        from homeassistant.util import dt as dt_util
        val = self.coordinator.data.get("user", {}).get("premium_expires_at")
        if not val or val == "null":
            return None
        return dt_util.parse_datetime(val)


class TorboxCooldownSensor(TorboxSensorBase):
    """Sensor for Cooldown Expiration Date."""

    _attr_translation_key = "cooldown_until"
    _attr_icon = "mdi:timer-sand"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_cooldown_until"

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        from homeassistant.util import dt as dt_util
        val = self.coordinator.data.get("user", {}).get("cooldown_until")
        if not val or val == "null":
            return None
        return dt_util.parse_datetime(val)


class TorboxServerSensor(TorboxSensorBase):
    """Sensor for Assigned Server."""

    _attr_translation_key = "server"
    _attr_icon = "mdi:server"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_server"

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        server_val = self.coordinator.data.get("user", {}).get("server")
        if server_val is None or server_val == "null":
            return None
        return str(server_val)


class TorboxTotalUsenetSensor(TorboxSensorBase):
    """Sensor for Total Usenet Downloads."""

    _attr_translation_key = "total_usenet"
    _attr_icon = "mdi:cloud-download"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_total_usenet"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        usenet = self.coordinator.data.get("usenet", [])
        return len(usenet)


class TorboxActiveUsenetSensor(TorboxSensorBase):
    """Sensor for Active Usenet Downloads."""

    _attr_translation_key = "active_usenet"
    _attr_icon = "mdi:download-network"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_active_usenet"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        usenet = self.coordinator.data.get("usenet", [])
        active = sum(
            1
            for item in usenet
            if item.get("download_state", "").lower()
            not in ("completed", "failed", "error")
        )
        return active


class TorboxTotalWebdlSensor(TorboxSensorBase):
    """Sensor for Total WebDL Downloads."""

    _attr_translation_key = "total_webdl"
    _attr_icon = "mdi:cloud-download"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_total_webdl"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        webdl = self.coordinator.data.get("webdl", [])
        return len(webdl)


class TorboxActiveWebdlSensor(TorboxSensorBase):
    """Sensor for Active WebDL Downloads."""

    _attr_translation_key = "active_webdl"
    _attr_icon = "mdi:download-network"

    def __init__(self, coordinator: TorboxDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._email}_active_webdl"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        webdl = self.coordinator.data.get("webdl", [])
        active = sum(
            1
            for item in webdl
            if item.get("download_state", "").lower()
            not in ("completed", "failed", "error")
        )
        return active

