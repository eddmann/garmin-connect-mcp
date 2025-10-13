"""Workout management tools for Garmin Connect MCP server."""

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


async def get_workouts() -> str:
    """Get all workouts."""
    try:
        client = _get_client()
        workouts = client.safe_call("get_workouts")
        return format_summary("Workouts", workouts)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_workout_by_id(
    workout_id: Annotated[int, "Workout ID"],
) -> str:
    """Get detailed information about a specific workout."""
    try:
        client = _get_client()
        workout = client.safe_call("get_workout", workout_id)
        return format_summary(f"Workout {workout_id}", workout)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def download_workout(
    workout_id: Annotated[int, "Workout ID"],
) -> str:
    """Download workout data (returns information about FIT data availability)."""
    try:
        _get_client()
        # Note: The actual garminconnect library may not support direct FIT download
        # This is a placeholder matching the original implementation
        return (
            f"Workout {workout_id} information:\n\n"
            "FIT data for workouts is available through the Garmin Connect web interface. "
            "This tool provides workout metadata but does not support direct FIT file download. "
            "Use get_workout_by_id to retrieve workout details."
        )
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def upload_workout(
    workout_json: Annotated[str, "Workout JSON data"],
) -> str:
    """Upload a workout to Garmin Connect."""
    try:
        _get_client()
        # This would require parsing the JSON and calling the appropriate Garmin API
        # Implementation depends on the garminconnect library capabilities
        return "Workout upload functionality is not yet implemented in the garminconnect library."
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
