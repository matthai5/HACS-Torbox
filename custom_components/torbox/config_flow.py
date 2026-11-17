"""Config flow for Torbox integration."""

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TorboxApiClient, TorboxApiClientAuthenticationError, TorboxApiClientCommunicationError
from .const import DOMAIN, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    client = TorboxApiClient(data[CONF_API_KEY], session)

    try:
        user_data = await client.get_user_data()
        email = user_data.get("data", {}).get("email", "Torbox Account")
        return {"title": email}
    except TorboxApiClientAuthenticationError:
        raise InvalidAuth
    except TorboxApiClientCommunicationError:
        raise CannotConnect


class TorboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Torbox."""

    VERSION = 1

    async def async_step_reauth(self, entry_data):
        """Start replacing an expired or rejected API key."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Validate a replacement key and reload the existing entry."""
        errors = {}
        if user_input is not None:
            user_input = {**user_input, CONF_API_KEY: user_input[CONF_API_KEY].strip()}
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during reauthentication")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates=user_input
                )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            user_input = {**user_input, CONF_API_KEY: user_input[CONF_API_KEY].strip()}
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
