"""API client for Torbox."""

import logging
import aiohttp
from typing import Any, Dict

from .const import API_BASE_URL, ENDPOINT_USER_ME, ENDPOINT_TORRENTS_MYLIST

_LOGGER = logging.getLogger(__name__)

class TorboxApiClientError(Exception):
    """Exception to indicate a general API error."""

class TorboxApiClientAuthenticationError(TorboxApiClientError):
    """Exception to indicate an authentication error."""

class TorboxApiClientCommunicationError(TorboxApiClientError):
    """Exception to indicate a communication error."""

class TorboxApiClient:
    """Torbox API Client."""

    def __init__(self, api_key: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._api_key = api_key
        self._session = session

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a request to the Torbox API."""
        url = f"{API_BASE_URL}{endpoint}"
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._api_key}"
        kwargs["headers"] = headers

        try:
            async with self._session.request(method, url, **kwargs) as response:
                if response.status in (401, 403):
                    raise TorboxApiClientAuthenticationError(
                        "Invalid credentials for Torbox API"
                    )
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            raise TorboxApiClientCommunicationError(f"Error communicating with Torbox API: {err}") from err
        except Exception as err:
            raise TorboxApiClientError(f"Unexpected error from Torbox API: {err}") from err

    async def get_user_data(self) -> Dict[str, Any]:
        """Get user data."""
        return await self._request("GET", ENDPOINT_USER_ME)

    async def get_torrents(self) -> Dict[str, Any]:
        """Get list of torrents."""
        return await self._request("GET", ENDPOINT_TORRENTS_MYLIST)
