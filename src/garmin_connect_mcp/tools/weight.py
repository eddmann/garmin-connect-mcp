"""Weight management tools for Garmin Connect MCP server."""

from typing import Annotated, Any

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder
from ..time_utils import parse_date_string

# Fields to keep from weight entries in summary mode.
_WEIGHT_SUMMARY_KEYS = {
    "samplePk",
    "date",
    "calendarDate",
    "weight",
    "bmi",
    "bodyFat",
    "bodyWater",
    "boneMass",
    "muscleMass",
}


def _summarize_weight_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Keep only essential fields from a single weight measurement."""
    return {k: v for k, v in entry.items() if k in _WEIGHT_SUMMARY_KEYS}


def _summarize_weigh_ins(weigh_ins: Any) -> Any:
    """Strip device metadata from weight data in summary mode.

    Handles both flat lists of entries and the nested dailyWeightSummaries structure.
    """
    if isinstance(weigh_ins, list):
        return [_summarize_weight_entry(e) for e in weigh_ins if isinstance(e, dict)]

    if isinstance(weigh_ins, dict):
        result = {}
        # Handle dailyWeightSummaries structure
        if "dailyWeightSummaries" in weigh_ins:
            summaries = []
            for day in weigh_ins["dailyWeightSummaries"]:
                summary = {"summaryDate": day.get("summaryDate")}
                if "latestWeight" in day and isinstance(day["latestWeight"], dict):
                    summary["latestWeight"] = _summarize_weight_entry(day["latestWeight"])
                summaries.append(summary)
            result["dailyWeightSummaries"] = summaries
        if "totalAverage" in weigh_ins and isinstance(weigh_ins["totalAverage"], dict):
            result["totalAverage"] = _summarize_weight_entry(weigh_ins["totalAverage"])
        return result

    return weigh_ins


async def query_weight_data(
    date: Annotated[str | None, "Specific date ('today', 'yesterday', or YYYY-MM-DD)"] = None,
    start_date: Annotated[str | None, "Range start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD)"] = None,
    summary_only: Annotated[
        bool,
        "Return only key weight fields (weight, BMI, date) without "
        "device metadata and source details. Included for API consistency.",
    ] = False,
    ctx: Context | None = None,
) -> str:
    """
    Query weight data.

    Get weight measurements for a specific date or date range.

    Use summary_only=True to get streamlined weight entries
    without device metadata and source details.
    """
    assert ctx is not None
    try:
        client = await ctx.get_state("client")

        # Determine query type
        if date:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            weight_data = client.safe_call("get_daily_weigh_ins", date_str)
            if summary_only:
                weight_data = _summarize_weigh_ins(weight_data)
            return ResponseBuilder.build_response(
                data={"weigh_ins": weight_data, "date": date_str},
                metadata={"query_type": "single_date", "date": date_str},
            )
        elif start_date and end_date:
            weight_data = client.safe_call("get_weigh_ins", start_date, end_date)
            if summary_only:
                weight_data = _summarize_weigh_ins(weight_data)
            return ResponseBuilder.build_response(
                data={"weigh_ins": weight_data},
                metadata={"query_type": "range", "start_date": start_date, "end_date": end_date},
            )
        else:
            # Default to today
            date_str = parse_date_string("today").strftime("%Y-%m-%d")
            weight_data = client.safe_call("get_daily_weigh_ins", date_str)
            if summary_only:
                weight_data = _summarize_weigh_ins(weight_data)
            return ResponseBuilder.build_response(
                data={"weigh_ins": weight_data, "date": date_str},
                metadata={"query_type": "single_date", "date": date_str},
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message, "api_error", ["Check your Garmin Connect credentials"]
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


async def manage_weight_data(
    action: Annotated[str, "Action: 'add' or 'delete'"],
    weight: Annotated[float | None, "Weight in kg (for add action)"] = None,
    date: Annotated[str | None, "Date for entry (YYYY-MM-DD, defaults to today)"] = None,
    weigh_in_ids: Annotated[str | None, "Comma-separated IDs to delete (for delete action)"] = None,
    ctx: Context | None = None,
) -> str:
    """
    Add or delete weight entries.

    Actions:
    - add: Add a new weight entry (provide weight, optionally date)
    - delete: Delete weight entries (provide weigh_in_ids)
    """
    assert ctx is not None
    try:
        client = await ctx.get_state("client")

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
        return ResponseBuilder.build_error_response(e.message, "api_error")
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
