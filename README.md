# Torbox Home Assistant Integration

This custom integration integrates [Torbox](https://torbox.app) into Home Assistant.

## Features
- Sensor for your current Torbox plan.
- Sensor for total number of torrents in your account.
- Sensor for active torrent downloads.
- Sensor for your 30-day usage statistics.

## Installation

### HACS (Recommended)
1. Add this repository to your HACS custom repositories.
2. Search for "Torbox" in HACS and install it.
3. Restart Home Assistant.
4. Go to Configuration -> Integrations and click "Add Integration". Search for Torbox.

### Manual
1. Copy the `custom_components/torbox` directory to your `custom_components` directory in Home Assistant.
2. Restart Home Assistant.
3. Go to Configuration -> Integrations and click "Add Integration". Search for Torbox.

## Configuration
When adding the integration, you will be prompted for your Torbox API Key. You can find this in your Torbox account settings.
