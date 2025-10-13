"""Activity-related tools for Garmin Connect MCP server."""

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
                "Please set GARMIN_EMAIL and GARMIN_PASSWORD in .env file, "
                "or run 'garmin-connect-mcp-auth' to set up authentication."
            )

        client = init_garmin_client(config)
        if client is None:
            raise GarminAPIError("Failed to initialize Garmin client")

        _garmin_wrapper = GarminClientWrapper(client)

    return _garmin_wrapper


async def get_activities_by_date(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
    activity_type: Annotated[str, "Activity type filter (optional)"] = "",
) -> str:
    """Get activities between two dates with optional activity type filter."""
    try:
        client = _get_client()
        activities = client.safe_call("get_activities_by_date", start_date, end_date, activity_type)

        if not activities:
            return f"No activities found between {start_date} and {end_date}"

        return format_summary(
            f"Activities from {start_date} to {end_date} ({len(activities)} found)", activities
        )

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activities_fordate(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get all activities for a specific date."""
    try:
        client = _get_client()
        activities = client.safe_call("get_activities_fordate", date)

        if not activities:
            return f"No activities found for {date}"

        return format_summary(f"Activities for {date} ({len(activities)} found)", activities)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get detailed information about a specific activity."""
    try:
        client = _get_client()
        activity = client.safe_call("get_activity", activity_id)

        if not activity:
            return f"Activity {activity_id} not found"

        return format_summary(f"Activity {activity_id}", activity)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_splits(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get split data for a specific activity."""
    try:
        client = _get_client()
        splits = client.safe_call("get_activity_splits", activity_id)

        if not splits:
            return f"No split data found for activity {activity_id}"

        return format_summary(f"Splits for Activity {activity_id}", splits)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_typed_splits(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get typed split data for a specific activity."""
    try:
        client = _get_client()
        splits = client.safe_call("get_activity_split_summaries", activity_id)

        if not splits:
            return f"No typed split data found for activity {activity_id}"

        return format_summary(f"Typed Splits for Activity {activity_id}", splits)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_split_summaries(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get split summaries for a specific activity."""
    try:
        client = _get_client()
        summaries = client.safe_call("get_activity_split_summaries", activity_id)

        if not summaries:
            return f"No split summaries found for activity {activity_id}"

        return format_summary(f"Split Summaries for Activity {activity_id}", summaries)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_weather(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get weather data for a specific activity."""
    try:
        client = _get_client()
        weather = client.safe_call("get_activity_weather", activity_id)

        if not weather:
            return f"No weather data found for activity {activity_id}"

        return format_summary(f"Weather for Activity {activity_id}", weather)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_hr_in_timezones(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get heart rate time in zones for a specific activity."""
    try:
        client = _get_client()
        hr_zones = client.safe_call("get_activity_hr_in_timezones", activity_id)

        if not hr_zones:
            return f"No heart rate zone data found for activity {activity_id}"

        return format_summary(f"Heart Rate Zones for Activity {activity_id}", hr_zones)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_gear(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get gear information for a specific activity."""
    try:
        client = _get_client()
        gear = client.safe_call("get_activity_gear", activity_id)

        if not gear:
            return f"No gear data found for activity {activity_id}"

        return format_summary(f"Gear for Activity {activity_id}", gear)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activity_exercise_sets(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get exercise sets for a specific activity (strength training)."""
    try:
        client = _get_client()
        sets = client.safe_call("get_activity_exercise_sets", activity_id)

        if not sets:
            return f"No exercise sets found for activity {activity_id}"

        return format_summary(f"Exercise Sets for Activity {activity_id}", sets)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_activities(
    start: Annotated[int, "Starting index (0-based)"],
    limit: Annotated[int, "Maximum number of activities to return"],
    activity_type: Annotated[str, "Activity type filter (optional)"] = "",
) -> str:
    """
    Get activities with pagination support.

    This method provides paginated access to activities, useful for queries like
    "show me my last 20 runs" or browsing through activity history.
    """
    try:
        client = _get_client()
        activities = client.safe_call("get_activities", start, limit, activity_type)

        if not activities:
            type_msg = f" of type '{activity_type}'" if activity_type else ""
            return f"No activities found{type_msg}"

        type_msg = f" ({activity_type})" if activity_type else ""
        return format_summary(
            f"Activities {start} to {start + len(activities)}{type_msg} ({len(activities)} found)",
            activities,
        )

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_last_activity() -> str:
    """
    Get the most recent activity.

    Convenience method for quick access to the latest recorded activity.
    """
    try:
        client = _get_client()
        activity = client.safe_call("get_last_activity")

        if not activity:
            return "No activities found"

        return format_summary("Latest Activity", activity)

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
