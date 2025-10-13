"""Gear management tools for Garmin Connect MCP server."""

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


@cached_call("gear", ttl_seconds=1800)  # Cache for 30 minutes
async def get_gear(
    user_profile_id: Annotated[int, "User profile ID"],
) -> str:
    """Get all gear for a user profile."""
    try:
        client = _get_client()
        gear = client.safe_call("get_gear", user_profile_id)
        return format_summary(f"Gear for User Profile {user_profile_id}", gear)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@cached_call("gear", ttl_seconds=1800)  # Cache for 30 minutes
async def get_gear_defaults(
    user_profile_id: Annotated[int, "User profile ID"],
) -> str:
    """Get default gear settings for a user profile."""
    try:
        client = _get_client()
        defaults = client.safe_call("get_gear_defaults", user_profile_id)
        return format_summary(f"Gear Defaults for User Profile {user_profile_id}", defaults)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_gear_stats(
    gear_uuid: Annotated[str, "Gear UUID"],
) -> str:
    """Get statistics for a specific piece of gear."""
    try:
        client = _get_client()
        stats = client.safe_call("get_gear_stats", gear_uuid)
        return format_summary(f"Stats for Gear {gear_uuid}", stats)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
