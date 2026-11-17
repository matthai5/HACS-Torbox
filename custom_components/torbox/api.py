"""API client for Torbox."""

import logging
import aiohttp
from typing import Any, Dict

from .const import (
    API_BASE_URL,
    ENDPOINT_USER_ME,
    ENDPOINT_TORRENTS_MYLIST,
    ENDPOINT_TORRENTS_CREATE,
    ENDPOINT_TORRENTS_CONTROL,
    ENDPOINT_USENET_MYLIST,
    ENDPOINT_USENET_CREATE,
    ENDPOINT_USENET_CONTROL,
    ENDPOINT_WEBDL_MYLIST,
    ENDPOINT_WEBDL_CREATE,
    ENDPOINT_WEBDL_CONTROL,
)

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
        self._api_key = api_key.strip()
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
                result = await response.json()
                if isinstance(result, dict) and result.get("success") is False:
                    error = result.get("error")
                    if error in ("BAD_TOKEN", "AUTH_ERROR", "INVALID_API_KEY", "UNAUTHORIZED"):
                        raise TorboxApiClientAuthenticationError(
                            "Invalid credentials for Torbox API"
                        )
                    raise TorboxApiClientError("Torbox API reported an unsuccessful request")
                return result
        except TorboxApiClientError:
            raise
        except TimeoutError as err:
            raise TorboxApiClientCommunicationError("Torbox API request timed out") from err
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

    async def get_usenet(self) -> Dict[str, Any]:
        """Get list of Usenet downloads."""
        return await self._request("GET", ENDPOINT_USENET_MYLIST)

    async def get_web_downloads(self) -> Dict[str, Any]:
        """Get list of web downloads."""
        return await self._request("GET", ENDPOINT_WEBDL_MYLIST)

    async def add_torrent(
        self,
        magnet: str = None,
        file_name: str = None,
        file_bytes: bytes = None,
    ) -> Dict[str, Any]:
        """Add a torrent via magnet link or file."""
        data = aiohttp.FormData()
        if magnet:
            data.add_field("magnet", magnet)
        elif file_bytes:
            data.add_field(
                "file",
                file_bytes,
                filename=file_name or "torrent.torrent",
                content_type="application/x-bittorrent",
            )
        else:
            raise TorboxApiClientError("Either magnet link or torrent file must be provided")

        data.add_field("seed", "1")
        data.add_field("allow_zip", "true")

        return await self._request("POST", ENDPOINT_TORRENTS_CREATE, data=data)

    async def control_torrent(self, torrent_id: Any, operation: str) -> Dict[str, Any]:
        """Control an existing torrent."""
        payload = {
            "torrent_id": torrent_id,
            "operation": operation,
        }
        return await self._request("POST", ENDPOINT_TORRENTS_CONTROL, json=payload)

    async def add_usenet(
        self,
        link: str = None,
        file_name: str = None,
        file_bytes: bytes = None,
    ) -> Dict[str, Any]:
        """Add a Usenet download via link or NZB file."""
        if file_bytes:
            data = aiohttp.FormData()
            data.add_field(
                "file",
                file_bytes,
                filename=file_name or "usenet.nzb",
                content_type="application/x-nzb",
            )
            # Default post_processing to repair, unpack and delete (-1 or 3)
            data.add_field("post_processing", "3")
            return await self._request("POST", ENDPOINT_USENET_CREATE, data=data)
        
        if link:
            payload = {
                "link": link,
                "post_processing": 3,
            }
            return await self._request("POST", ENDPOINT_USENET_CREATE, json=payload)

        raise TorboxApiClientError("Either link or NZB file must be provided")

    async def control_usenet(self, usenet_id: Any, operation: str) -> Dict[str, Any]:
        """Control an existing Usenet download."""
        payload = {
            "usenet_id": usenet_id,
            "operation": operation,
        }
        return await self._request("POST", ENDPOINT_USENET_CONTROL, json=payload)

    async def add_webdl(self, url: str, name: str = None) -> Dict[str, Any]:
        """Add a web download."""
        payload = {"url": url}
        if name:
            payload["name"] = name
        return await self._request("POST", ENDPOINT_WEBDL_CREATE, json=payload)

    async def control_webdl(self, webdl_id: Any, operation: str) -> Dict[str, Any]:
        """Control an existing web download."""
        payload = {
            "webdl_id": webdl_id,
            "operation": operation,
        }
        return await self._request("POST", ENDPOINT_WEBDL_CONTROL, json=payload)
