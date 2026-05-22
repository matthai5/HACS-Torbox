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
            torrents_data = await self.client.get_torrents()

            return {
                "user": user_data.get("data", {}),
                "torrents": torrents_data.get("data", [])
            }
        except TorboxApiClientAuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except TorboxApiClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
