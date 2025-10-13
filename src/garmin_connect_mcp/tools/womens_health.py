"""Women's health tools for Garmin Connect MCP server."""

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


async def get_pregnancy_summary() -> str:
    """Get pregnancy summary data."""
    try:
        client = _get_client()
        summary = client.safe_call("get_pregnancy_summary")
        return format_summary("Pregnancy Summary", summary)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_menstrual_data_for_date(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get menstrual cycle data for a specific date."""
    try:
        client = _get_client()
        data = client.safe_call("get_menstrual_day_data", date)
        return format_summary(f"Menstrual Data for {date}", data)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_menstrual_calendar_data(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get menstrual calendar data for a date range."""
    try:
        client = _get_client()
        data = client.safe_call("get_menstrual_calendar", start_date, end_date)
        return format_summary(f"Menstrual Calendar ({start_date} to {end_date})", data)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
