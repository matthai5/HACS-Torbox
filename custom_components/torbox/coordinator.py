"""DataUpdateCoordinator for Torbox."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TorboxApiClient, TorboxApiClientAuthenticationError, TorboxApiClientError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class TorboxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Torbox data."""

    def __init__(self, hass: HomeAssistant, client: TorboxApiClient) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            user_data = await self.client.get_user_data()
        except TorboxApiClientAuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except TorboxApiClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        torrents = []
        try:
            torrents_data = await self.client.get_torrents()
            torrents = torrents_data.get("data", [])
            if not isinstance(torrents, list):
                torrents = []
        except Exception as err:
            _LOGGER.warning("Failed to fetch Torrents list: %s", err)

        usenet = []
        try:
            usenet_data = await self.client.get_usenet()
            usenet = usenet_data.get("data", [])
            if not isinstance(usenet, list):
                usenet = []
        except Exception as err:
            _LOGGER.warning("Failed to fetch Usenet list: %s", err)

        webdl = []
        try:
            webdl_data = await self.client.get_web_downloads()
            webdl = webdl_data.get("data", [])
            if not isinstance(webdl, list):
                webdl = []
        except Exception as err:
            _LOGGER.warning("Failed to fetch WebDL list: %s", err)

        return {
            "user": user_data.get("data", {}) if isinstance(user_data, dict) else {},
            "torrents": torrents,
            "usenet": usenet,
            "webdl": webdl,
        }
