"""Weight management tools for Garmin Connect MCP server."""

from typing import Annotated

from ..auth import load_config, validate_credentials
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


async def get_weigh_ins(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get weigh-in data for a date range."""
    try:
        client = _get_client()
        weigh_ins = client.safe_call("get_weigh_ins", start_date, end_date)
        return format_summary(f"Weigh-ins from {start_date} to {end_date}", weigh_ins)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_daily_weigh_ins(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get weigh-in data for a specific date."""
    try:
        client = _get_client()
        weigh_ins = client.safe_call("get_weigh_ins", date, date)
        return format_summary(f"Weigh-ins for {date}", weigh_ins)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def delete_weigh_ins(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
    delete_all: Annotated[bool, "Delete all weigh-ins for the date"] = True,
) -> str:
    """Delete weigh-in data for a specific date."""
    try:
        client = _get_client()
        client.safe_call("delete_weigh_ins", date, delete_all)
        return f"Successfully deleted weigh-ins for {date}"
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def add_weigh_in(
    weight: Annotated[float, "Weight value"],
    unit_key: Annotated[str, "Unit of measurement (kg or lbs)"] = "kg",
) -> str:
    """Add a new weigh-in entry."""
    try:
        client = _get_client()
        client.safe_call("add_weigh_in", weight, unit=unit_key)
        return f"Successfully added weigh-in: {weight} {unit_key}"
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
