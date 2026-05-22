"""Constants for the Torbox integration."""

from datetime import timedelta

DOMAIN = "torbox"
CONF_API_KEY = "api_key"

API_BASE_URL = "https://api.torbox.app/v1/api"

# Default polling interval for updating data
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

# API Endpoints
ENDPOINT_USER_ME = "/user/me"
ENDPOINT_TORRENTS_MYLIST = "/torrents/mylist"
ENDPOINT_TORRENTS_CREATE = "/torrents/createtorrent"
ENDPOINT_TORRENTS_CONTROL = "/torrents/controltorrent"
ENDPOINT_USENET_MYLIST = "/usenet/mylist"
ENDPOINT_USENET_CREATE = "/usenet/createusenetdownload"
ENDPOINT_USENET_CONTROL = "/usenet/controlusenetdownload"
ENDPOINT_WEBDL_MYLIST = "/webdl/mylist"
ENDPOINT_WEBDL_CREATE = "/webdl/createwebdownload"
ENDPOINT_WEBDL_CONTROL = "/webdl/controlwebdownload"
