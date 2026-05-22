"""The Torbox integration."""

import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TorboxApiClient
from .const import DOMAIN, CONF_API_KEY
from .coordinator import TorboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Torbox from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_key = entry.data[CONF_API_KEY]
    session = async_get_clientsession(hass)
    client = TorboxApiClient(api_key, session)

    coordinator = TorboxDataUpdateCoordinator(hass, client)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services if not already registered
    if not hass.data[DOMAIN].get("services_registered"):
        await async_setup_services(hass)
        hass.data[DOMAIN]["services_registered"] = True

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    # If no more entries remain, remove services and cleanup domain data
    if not any(
        isinstance(val, TorboxDataUpdateCoordinator)
        for val in hass.data[DOMAIN].values()
    ):
        for service in [
            "add_torrent",
            "control_torrent",
            "add_usenet",
            "control_usenet",
            "add_webdl",
            "control_webdl",
        ]:
            hass.services.async_remove(DOMAIN, service)
        hass.data.pop(DOMAIN)

    return unload_ok


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Torbox services."""

    def get_client() -> TorboxApiClient:
        """Get the active Torbox API client."""
        for value in hass.data[DOMAIN].values():
            if isinstance(value, TorboxDataUpdateCoordinator):
                return value.client
        raise ValueError("Torbox integration not configured or active")

    async def handle_add_torrent(call: ServiceCall) -> None:
        """Add a torrent to Torbox."""
        client = get_client()
        magnet = call.data.get("magnet")
        torrent_url = call.data.get("torrent_url")
        file_path = call.data.get("file_path")

        file_bytes = None
        file_name = None

        if torrent_url:
            session = async_get_clientsession(hass)
            async with session.get(torrent_url) as resp:
                resp.raise_for_status()
                file_bytes = await resp.read()
            file_name = torrent_url.split("/")[-1] or "torrent.torrent"
        elif file_path:
            if not os.path.isfile(file_path):
                raise ValueError(f"Local torrent file not found at path: {file_path}")

            def _read_file():
                with open(file_path, "rb") as f:
                    return f.read()

            file_bytes = await hass.async_add_executor_job(_read_file)
            file_name = os.path.basename(file_path)

        await client.add_torrent(
            magnet=magnet, file_name=file_name, file_bytes=file_bytes
        )

    async def handle_control_torrent(call: ServiceCall) -> None:
        """Control a torrent on Torbox."""
        client = get_client()
        torrent_id = call.data.get("torrent_id")
        operation = call.data.get("operation")
        await client.control_torrent(torrent_id=torrent_id, operation=operation)

    async def handle_add_usenet(call: ServiceCall) -> None:
        """Add a Usenet download."""
        client = get_client()
        link = call.data.get("link")
        file_path = call.data.get("file_path")

        file_bytes = None
        file_name = None

        if link and (link.startswith("http://") or link.startswith("https://")):
            session = async_get_clientsession(hass)
            async with session.get(link) as resp:
                resp.raise_for_status()
                file_bytes = await resp.read()
            file_name = link.split("/")[-1] or "usenet.nzb"
            link = None  # Force file upload if downloaded from URL
        elif file_path:
            if not os.path.isfile(file_path):
                raise ValueError(f"Local NZB file not found at path: {file_path}")

            def _read_file():
                with open(file_path, "rb") as f:
                    return f.read()

            file_bytes = await hass.async_add_executor_job(_read_file)
            file_name = os.path.basename(file_path)

        await client.add_usenet(link=link, file_name=file_name, file_bytes=file_bytes)

    async def handle_control_usenet(call: ServiceCall) -> None:
        """Control a Usenet download on Torbox."""
        client = get_client()
        usenet_id = call.data.get("usenet_id")
        operation = call.data.get("operation")
        await client.control_usenet(usenet_id=usenet_id, operation=operation)

    async def handle_add_webdl(call: ServiceCall) -> None:
        """Add a web download to Torbox."""
        client = get_client()
        url = call.data.get("url")
        name = call.data.get("name")
        await client.add_webdl(url=url, name=name)

    async def handle_control_webdl(call: ServiceCall) -> None:
        """Control a web download on Torbox."""
        client = get_client()
        webdl_id = call.data.get("webdl_id")
        operation = call.data.get("operation")
        await client.control_webdl(webdl_id=webdl_id, operation=operation)

    hass.services.async_register(DOMAIN, "add_torrent", handle_add_torrent)
    hass.services.async_register(DOMAIN, "control_torrent", handle_control_torrent)
    hass.services.async_register(DOMAIN, "add_usenet", handle_add_usenet)
    hass.services.async_register(DOMAIN, "control_usenet", handle_control_usenet)
    hass.services.async_register(DOMAIN, "add_webdl", handle_add_webdl)
    hass.services.async_register(DOMAIN, "control_webdl", handle_control_webdl)
