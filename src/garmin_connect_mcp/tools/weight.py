"""Weight management tools for Garmin Connect MCP server."""

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


async def query_weight_data(
    date: Annotated[str | None, "Specific date ('today', 'yesterday', or YYYY-MM-DD)"] = None,
    start_date: Annotated[str | None, "Range start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD)"] = None,
) -> str:
    """
    Query weight data.

    Get weight measurements for a specific date or date range.
    """
    try:
        client = _get_client()

        # Determine query type
        if date:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            weight_data = client.safe_call("get_daily_weigh_ins", date_str)
            return ResponseBuilder.build_response(
                data={"weigh_ins": weight_data, "date": date_str},
                metadata={"query_type": "single_date", "date": date_str},
            )
        elif start_date and end_date:
            weight_data = client.safe_call("get_weigh_ins", start_date, end_date)
            return ResponseBuilder.build_response(
                data={"weigh_ins": weight_data},
                metadata={"query_type": "range", "start_date": start_date, "end_date": end_date},
            )
        else:
            # Default to today
            date_str = parse_date_string("today").strftime("%Y-%m-%d")
            weight_data = client.safe_call("get_daily_weigh_ins", date_str)
            return ResponseBuilder.build_response(
                data={"weigh_ins": weight_data, "date": date_str},
                metadata={"query_type": "single_date", "date": date_str},
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message, "garmin_api_error", ["Check your Garmin Connect credentials"]
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")


async def manage_weight_data(
    action: Annotated[str, "Action: 'add' or 'delete'"],
    weight: Annotated[float | None, "Weight in kg (for add action)"] = None,
    date: Annotated[str | None, "Date for entry (YYYY-MM-DD, defaults to today)"] = None,
    weigh_in_ids: Annotated[str | None, "Comma-separated IDs to delete (for delete action)"] = None,
) -> str:
    """
    Add or delete weight entries.

    Actions:
    - add: Add a new weight entry (provide weight, optionally date)
    - delete: Delete weight entries (provide weigh_in_ids)
    """
    try:
        client = _get_client()

        if action == "add":
            if weight is None:
                return ResponseBuilder.build_error_response(
                    "Weight value required for add action",
                    "invalid_parameters",
                    ["Provide weight in kg", "Example: weight=75.5"],
                )

            date_str = (
                parse_date_string(date).strftime("%Y-%m-%d")
                if date
                else parse_date_string("today").strftime("%Y-%m-%d")
            )

            result = client.safe_call("add_weigh_in", weight, date_str)
            return ResponseBuilder.build_response(
                data={"result": result, "weight": weight, "date": date_str},
                analysis={"insights": [f"Added weight entry: {weight} kg on {date_str}"]},
                metadata={"action": "add"},
            )

        elif action == "delete":
            if not weigh_in_ids:
                return ResponseBuilder.build_error_response(
                    "Weigh-in IDs required for delete action",
                    "invalid_parameters",
                    ["Provide comma-separated IDs", "Example: weigh_in_ids='123,456'"],
                )

            ids = [int(id_str.strip()) for id_str in weigh_in_ids.split(",")]
            result = client.safe_call("delete_weigh_ins", ids)

            return ResponseBuilder.build_response(
                data={"result": result, "deleted_ids": ids},
                analysis={"insights": [f"Deleted {len(ids)} weight entries"]},
                metadata={"action": "delete"},
            )

        else:
            return ResponseBuilder.build_error_response(
                f"Invalid action: {action}",
                "invalid_parameters",
                ["Valid actions: 'add', 'delete'"],
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(e.message, "garmin_api_error")
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")
