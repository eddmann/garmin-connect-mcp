"""Data management tools for Garmin Connect MCP server."""

from typing import Annotated

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..response_builder import ResponseBuilder
from ..time_utils import parse_date_string

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


async def log_health_data(
    data_type: Annotated[str, "Data type: 'body_composition', 'blood_pressure', 'hydration'"],
    date: Annotated[str | None, "Date (YYYY-MM-DD, defaults to today)"] = None,
    **kwargs,
) -> str:
    """
    Log health data entries.

    Data types:
    - body_composition: Requires weight, body_fat, etc. (type-specific params)
    - blood_pressure: Requires systolic, diastolic params
    - hydration: Requires volume_ml param
    """
    try:
        client = _get_client()

        date_str = (
            parse_date_string(date).strftime("%Y-%m-%d")
            if date
            else parse_date_string("today").strftime("%Y-%m-%d")
        )

        if data_type == "body_composition":
            # Body composition logging
            result = client.safe_call("add_body_composition", date_str, **kwargs)
            return ResponseBuilder.build_response(
                data={"result": result},
                analysis={"insights": [f"Body composition logged for {date_str}"]},
                metadata={"data_type": "body_composition", "date": date_str},
            )

        elif data_type == "blood_pressure":
            # Blood pressure logging
            systolic = kwargs.get("systolic")
            diastolic = kwargs.get("diastolic")

            if not systolic or not diastolic:
                return ResponseBuilder.build_error_response(
                    "Systolic and diastolic values required",
                    "invalid_parameters",
                    [
                        "Provide systolic and diastolic parameters",
                        "Example: systolic=120, diastolic=80",
                    ],
                )

            result = client.safe_call("set_blood_pressure", date_str, systolic, diastolic)
            return ResponseBuilder.build_response(
                data={"result": result, "systolic": systolic, "diastolic": diastolic},
                analysis={
                    "insights": [f"Blood pressure logged: {systolic}/{diastolic} on {date_str}"]
                },
                metadata={"data_type": "blood_pressure", "date": date_str},
            )

        elif data_type == "hydration":
            # Hydration logging
            volume_ml = kwargs.get("volume_ml")

            if not volume_ml:
                return ResponseBuilder.build_error_response(
                    "Volume in ml required",
                    "invalid_parameters",
                    ["Provide volume_ml parameter", "Example: volume_ml=500"],
                )

            result = client.safe_call("add_hydration_data", date_str, volume_ml)
            return ResponseBuilder.build_response(
                data={"result": result, "volume_ml": volume_ml},
                analysis={"insights": [f"Hydration logged: {volume_ml} ml on {date_str}"]},
                metadata={"data_type": "hydration", "date": date_str},
            )

        else:
            return ResponseBuilder.build_error_response(
                f"Invalid data type: {data_type}",
                "invalid_parameters",
                ["Valid types: 'body_composition', 'blood_pressure', 'hydration'"],
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(e.message, "garmin_api_error")
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")
