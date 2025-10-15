"""Data management tools for Garmin Connect MCP server."""

import json
from typing import Annotated

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder
from ..time_utils import parse_date_string


async def log_health_data(
    data_type: Annotated[str, "Data type: 'body_composition', 'blood_pressure', 'hydration'"],
    data: Annotated[
        str,
        "JSON object with the health data fields. "
        "For body_composition: {'weight': 70.5, 'body_fat': 15.2, 'body_water': 60.0}. "
        "For blood_pressure: {'systolic': 120, 'diastolic': 80}. "
        "For hydration: {'volume_ml': 500}",
    ],
    date: Annotated[str | None, "Date (YYYY-MM-DD, defaults to today)"] = None,
    ctx: Context | None = None,
) -> str:
    """
    Log health data entries.

    Data types:
    - body_composition: Requires data with weight, body_fat, etc.
    - blood_pressure: Requires data with systolic, diastolic
    - hydration: Requires data with volume_ml

    All data should be provided as a JSON string.
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        date_str = (
            parse_date_string(date).strftime("%Y-%m-%d")
            if date
            else parse_date_string("today").strftime("%Y-%m-%d")
        )

        # Parse the JSON data
        try:
            params = json.loads(data)
        except json.JSONDecodeError as e:
            return ResponseBuilder.build_error_response(
                f"Invalid JSON in data parameter: {e}",
                "invalid_parameters",
                ["Provide valid JSON object with the required fields"],
            )

        if data_type == "body_composition":
            # Body composition logging
            result = client.safe_call("add_body_composition", date_str, **params)
            return ResponseBuilder.build_response(
                data={"result": result, "body_composition": params},
                analysis={"insights": [f"Body composition logged for {date_str}"]},
                metadata={"data_type": "body_composition", "date": date_str},
            )

        elif data_type == "blood_pressure":
            # Blood pressure logging
            systolic = params.get("systolic")
            diastolic = params.get("diastolic")

            if not systolic or not diastolic:
                return ResponseBuilder.build_error_response(
                    "Systolic and diastolic values required",
                    "invalid_parameters",
                    [
                        "Provide data with systolic and diastolic fields",
                        'Example: {"systolic": 120, "diastolic": 80}',
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
            volume_ml = params.get("volume_ml")

            if not volume_ml:
                return ResponseBuilder.build_error_response(
                    "Volume in ml required",
                    "invalid_parameters",
                    [
                        "Provide data with volume_ml field",
                        'Example: {"volume_ml": 500}',
                    ],
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
        return ResponseBuilder.build_error_response(e.message, "api_error")
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
