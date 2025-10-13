"""Data management tools for Garmin Connect MCP server."""

from typing import Annotated

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


async def add_body_composition(
    timestamp: Annotated[int, "Timestamp"],
    weight: Annotated[float, "Weight in kg"],
    percent_fat: Annotated[float | None, "Body fat percentage"] = None,
    percent_hydration: Annotated[float | None, "Hydration percentage"] = None,
    bone_mass: Annotated[float | None, "Bone mass"] = None,
    muscle_mass: Annotated[float | None, "Muscle mass"] = None,
) -> str:
    """Add body composition data."""
    try:
        client = _get_client()
        client.safe_call(
            "add_body_composition",
            timestamp,
            weight,
            percent_fat,
            percent_hydration,
            bone_mass,
            muscle_mass,
        )
        return f"Successfully added body composition data for timestamp {timestamp}"
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def set_blood_pressure(
    systolic: Annotated[int, "Systolic pressure"],
    diastolic: Annotated[int, "Diastolic pressure"],
    pulse: Annotated[int, "Pulse rate"],
    notes: Annotated[str | None, "Optional notes"] = None,
) -> str:
    """Set blood pressure measurement."""
    try:
        client = _get_client()
        client.safe_call("set_blood_pressure", systolic, diastolic, pulse, notes)
        return f"Successfully recorded blood pressure: {systolic}/{diastolic}, pulse: {pulse}"
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def add_hydration_data(
    value_in_ml: Annotated[int, "Hydration value in milliliters"],
    cdate: Annotated[str, "Date in YYYY-MM-DD format"],
    timestamp: Annotated[int, "Timestamp"],
) -> str:
    """Add hydration data."""
    try:
        client = _get_client()
        client.safe_call("add_hydration_data", value_in_ml, cdate, timestamp)
        return f"Successfully added hydration data: {value_in_ml}ml for {cdate}"
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
