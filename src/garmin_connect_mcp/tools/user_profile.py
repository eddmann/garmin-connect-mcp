"""User profile tools for Garmin Connect MCP server."""

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client

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


async def get_full_name() -> str:
    """Get the full name of the authenticated user."""
    try:
        client = _get_client()
        name = client.safe_call("get_full_name")
        return f"Full Name: {name}"
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
