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
