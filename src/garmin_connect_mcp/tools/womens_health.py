"""Women's health tools for Garmin Connect MCP server."""

from typing import Annotated

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder
from ..time_utils import parse_date_string


async def query_womens_health(
    data_type: Annotated[str, "Data type: 'pregnancy' or 'menstrual'"],
    date: Annotated[str | None, "Specific date (YYYY-MM-DD)"] = None,
    start_date: Annotated[
        str | None, "Range start date (YYYY-MM-DD, for menstrual calendar)"
    ] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD, for menstrual calendar)"] = None,
    ctx: Context | None = None,
) -> str:
    """
    Query women's health data.

    Data types:
    - pregnancy: Get pregnancy tracking summary
    - menstrual: Get menstrual cycle data (for specific date or date range)
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        if data_type == "pregnancy":
            # Pregnancy summary
            summary = client.safe_call("get_pregnancy_summary")
            return ResponseBuilder.build_response(
                data={"pregnancy_summary": summary},
                metadata={"data_type": "pregnancy"},
            )

        elif data_type == "menstrual":
            # Menstrual data
            if date:
                # Specific date
                date_str = parse_date_string(date).strftime("%Y-%m-%d")
                menstrual_data = client.safe_call("get_menstrual_data_for_date", date_str)
                return ResponseBuilder.build_response(
                    data={"menstrual_data": menstrual_data, "date": date_str},
                    metadata={
                        "data_type": "menstrual",
                        "query_type": "single_date",
                        "date": date_str,
                    },
                )
            elif start_date and end_date:
                # Date range (calendar)
                calendar_data = client.safe_call(
                    "get_menstrual_calendar_data", start_date, end_date
                )
                return ResponseBuilder.build_response(
                    data={"menstrual_calendar": calendar_data},
                    metadata={
                        "data_type": "menstrual",
                        "query_type": "calendar",
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                )
            else:
                return ResponseBuilder.build_error_response(
                    "Date or date range required for menstrual data",
                    "invalid_parameters",
                    [
                        "Provide date for single day",
                        "Or provide start_date and end_date for calendar view",
                    ],
                )

        else:
            return ResponseBuilder.build_error_response(
                f"Invalid data type: {data_type}",
                "invalid_parameters",
                ["Valid types: 'pregnancy', 'menstrual'"],
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(e.message, "api_error")
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
