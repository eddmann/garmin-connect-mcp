"""Device-related tools for Garmin Connect MCP server."""

from typing import Annotated

from ..auth import load_config, validate_credentials
from ..cache import cached_call
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..formatters import format_summary

# Global client instance
_garmin_wrapper: GarminClientWrapper | None = None


def _get_client() -> GarminClientWrapper:
    """Get or initialize the Garmin client."""
    global _garmin_wrapper

    if _garmin_wrapper is None:
        config = load_config()
        if not validate_credentials(config):
            raise GarminAPIError(
                "Garmin credentials not configured. "
                "Please set GARMIN_EMAIL and GARMIN_PASSWORD in .env file."
            )

        client = init_garmin_client(config)
        if client is None:
            raise GarminAPIError("Failed to initialize Garmin client")

        _garmin_wrapper = GarminClientWrapper(client)

    return _garmin_wrapper


@cached_call("devices", ttl_seconds=3600)  # Cache for 1 hour
async def get_devices() -> str:
    """Get all registered Garmin devices."""
    try:
        client = _get_client()
        devices = client.safe_call("get_devices")
        return format_summary("Registered Devices", devices)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_device_last_used() -> str:
    """Get the last used device."""
    try:
        client = _get_client()
        device = client.safe_call("get_device_last_used")
        return format_summary("Last Used Device", device)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_device_settings(
    device_id: Annotated[int, "Device ID"],
) -> str:
    """Get settings for a specific device."""
    try:
        client = _get_client()
        settings = client.safe_call("get_device_settings", device_id)
        return format_summary(f"Settings for Device {device_id}", settings)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_primary_training_device() -> str:
    """Get the primary training device."""
    try:
        client = _get_client()
        device = client.safe_call("get_primary_training_device")
        return format_summary("Primary Training Device", device)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_device_solar_data(
    device_id: Annotated[int, "Device ID"],
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get solar charging data for a specific device and date."""
    try:
        client = _get_client()
        solar_data = client.safe_call("get_device_solar", device_id, date)
        return format_summary(f"Solar Data for Device {device_id} on {date}", solar_data)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@cached_call("devices", ttl_seconds=1800)  # Cache for 30 minutes
async def get_device_alarms() -> str:
    """Get alarms for all devices."""
    try:
        client = _get_client()
        alarms = client.safe_call("get_device_alarms")
        return format_summary("Device Alarms", alarms)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
