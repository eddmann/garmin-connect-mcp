"""Activity-related tools for Garmin Connect MCP server."""

from typing import Annotated, Any

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..pagination import build_pagination_info, decode_cursor
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
                "Please set GARMIN_EMAIL and GARMIN_PASSWORD in .env file, "
                "or run 'garmin-connect-mcp-auth' to set up authentication."
            )

        client = init_garmin_client(config)
        if client is None:
            raise GarminAPIError("Failed to initialize Garmin client")

        _garmin_wrapper = GarminClientWrapper(client)

    return _garmin_wrapper


async def _query_activities_paginated(
    client: GarminClientWrapper,
    start_date: str,
    end_date: str,
    activity_type: str,
    cursor: str | None,
    limit: int,
    unit: str,
) -> str:
    """Query activities by date range with cursor-based pagination."""
    # Parse cursor to get current page
    current_page = 1
    if cursor:
        try:
            cursor_data = decode_cursor(cursor)
            current_page = cursor_data.get("page", 1)
        except ValueError:
            return ResponseBuilder.build_error_response(
                "Invalid pagination cursor",
                error_type="validation_error",
            )

    # Validate limit
    if limit < 1 or limit > 50:
        return ResponseBuilder.build_error_response(
            f"Invalid limit: {limit}. Must be between 1 and 50.",
            error_type="validation_error",
        )

    # Fetch all activities in date range (Garmin API doesn't support offset pagination directly)
    # So we fetch all and slice in memory
    all_activities = client.safe_call("get_activities_by_date", start_date, end_date, activity_type)

    # Calculate offset for current page
    offset = (current_page - 1) * limit

    # Fetch limit+1 to detect if there are more pages
    fetch_limit = limit + 1
    activities = all_activities[offset : offset + fetch_limit]

    # Check if there are more results
    has_more = len(activities) > limit
    activities = activities[:limit]

    # Build pagination filters
    pagination_filters: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
    }
    if activity_type:
        pagination_filters["activity_type"] = activity_type

    # Build pagination info
    pagination = build_pagination_info(
        returned_count=len(activities),
        limit=limit,
        current_page=current_page,
        has_more=has_more,
        filters=pagination_filters,
    )

    if not activities:
        type_msg = f" of type '{activity_type}'" if activity_type else ""
        return ResponseBuilder.build_response(
            data={"activities": [], "count": 0},
            metadata={
                "start_date": start_date,
                "end_date": end_date,
                "activity_type": activity_type or "all",
                "unit": unit,
            },
            pagination=pagination,
            analysis={
                "insights": [f"No activities found{type_msg} between {start_date} and {end_date}"]
            },
        )

    # Format activities
    formatted_activities = [ResponseBuilder.format_activity(act, unit) for act in activities]

    return ResponseBuilder.build_response(
        data={"activities": formatted_activities, "count": len(activities)},
        metadata={
            "start_date": start_date,
            "end_date": end_date,
            "activity_type": activity_type or "all",
            "unit": unit,
        },
        pagination=pagination,
    )


async def _query_activities_general_paginated(
    client: GarminClientWrapper,
    activity_type: str,
    cursor: str | None,
    limit: int,
    unit: str,
) -> str:
    """Query activities with general pagination (no date filter)."""
    # Parse cursor to get current page
    current_page = 1
    if cursor:
        try:
            cursor_data = decode_cursor(cursor)
            current_page = cursor_data.get("page", 1)
        except ValueError:
            return ResponseBuilder.build_error_response(
                "Invalid pagination cursor",
                error_type="validation_error",
            )

    # Validate limit
    if limit < 1 or limit > 50:
        return ResponseBuilder.build_error_response(
            f"Invalid limit: {limit}. Must be between 1 and 50.",
            error_type="validation_error",
        )

    # Calculate start index for Garmin API (0-based)
    start_index = (current_page - 1) * limit

    # Fetch limit+1 to detect if there are more pages
    fetch_limit = limit + 1
    activities = client.safe_call("get_activities", start_index, fetch_limit, activity_type)

    # Check if there are more results
    has_more = len(activities) > limit
    activities = activities[:limit]

    # Build pagination filters
    pagination_filters: dict[str, Any] = {}
    if activity_type:
        pagination_filters["activity_type"] = activity_type

    # Build pagination info
    pagination = build_pagination_info(
        returned_count=len(activities),
        limit=limit,
        current_page=current_page,
        has_more=has_more,
        filters=pagination_filters,
    )

    if not activities:
        type_msg = f" of type '{activity_type}'" if activity_type else ""
        return ResponseBuilder.build_response(
            data={"activities": [], "count": 0},
            metadata={"activity_type": activity_type or "all", "unit": unit},
            pagination=pagination,
            analysis={"insights": [f"No activities found{type_msg}"]},
        )

    # Format activities
    formatted_activities = [ResponseBuilder.format_activity(act, unit) for act in activities]

    return ResponseBuilder.build_response(
        data={"activities": formatted_activities, "count": len(activities)},
        metadata={"activity_type": activity_type or "all", "unit": unit},
        pagination=pagination,
    )


async def query_activities(
    activity_id: Annotated[int | None, "Specific activity ID to retrieve"] = None,
    start_date: Annotated[str | None, "Start date in YYYY-MM-DD format for range query"] = None,
    end_date: Annotated[str | None, "End date in YYYY-MM-DD format for range query"] = None,
    date: Annotated[str | None, "Specific date in YYYY-MM-DD format or 'today'/'yesterday'"] = None,
    cursor: Annotated[
        str | None, "Pagination cursor from previous response (for continuing multi-page queries)"
    ] = None,
    limit: Annotated[
        int | None,
        "Maximum activities per page (1-50). Default: 10. "
        "Use pagination cursor for large datasets.",
    ] = None,
    activity_type: Annotated[str, "Activity type filter (e.g., 'running', 'cycling')"] = "",
    unit: Annotated[str, "Unit system: 'metric' or 'imperial'"] = "metric",
) -> str:
    """
    Query activities with flexible parameters and pagination support.

    This unified tool supports multiple query patterns:
    1. Get specific activity: provide activity_id
    2. Get activities by date range: provide start_date and end_date (paginated)
    3. Get activities for specific date: provide date
    4. Get paginated activities: use cursor and limit
    5. Get last activity: no parameters

    All queries can be filtered by activity_type (e.g., 'running', 'cycling').

    Pagination:
    For large time ranges, use pagination to retrieve all activities:
    1. Make initial request without cursor
    2. Check response["pagination"]["has_more"]
    3. Use response["pagination"]["cursor"] for next page

    Returns: JSON string with structure:
    {
        "data": {
            "activity": {...}       // Single activity mode
            OR
            "activities": [...],    // List mode
            "count": N
        },
        "pagination": {             // List mode only (when paginated)
            "cursor": "...",        // Use for next page (null if no more)
            "has_more": true,
            "limit": 20,
            "returned": 20
        },
        "metadata": {...}
    }
    """
    try:
        client = _get_client()

        # Pattern 1: Specific activity by ID
        if activity_id is not None:
            activity = client.safe_call("get_activity", activity_id)

            if not activity:
                return ResponseBuilder.build_error_response(
                    f"Activity {activity_id} not found",
                    "not_found",
                    [
                        "Check that the activity ID is correct",
                        "Try query_activities() to list recent activities",
                    ],
                )

            # Format the activity with rich data
            formatted_activity = ResponseBuilder.format_activity(activity, unit)

            return ResponseBuilder.build_response(
                data={"activity": formatted_activity},
                metadata={"activity_id": activity_id, "unit": unit},
            )

        # Pattern 2: Date range query (with pagination)
        if start_date and end_date:
            return await _query_activities_paginated(
                client=client,
                start_date=start_date,
                end_date=end_date,
                activity_type=activity_type,
                cursor=cursor,
                limit=limit or 10,
                unit=unit,
            )

        # Pattern 3: Specific date query
        if date:
            # Parse date string (supports 'today', 'yesterday', or YYYY-MM-DD)
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")

            activities = client.safe_call("get_activities_fordate", date_str)

            if not activities:
                return ResponseBuilder.build_response(
                    data={"activities": [], "count": 0},
                    metadata={"date": date_str},
                    analysis={"insights": [f"No activities found for {date_str}"]},
                )

            formatted_activities = [
                ResponseBuilder.format_activity(act, unit) for act in activities
            ]

            return ResponseBuilder.build_response(
                data={"activities": formatted_activities, "count": len(activities)},
                metadata={"date": date_str, "unit": unit},
            )

        # Pattern 4: Pagination query (general pagination using Garmin's start/limit API)
        if cursor is not None or limit is not None:
            # Use cursor-based pagination for general queries
            return await _query_activities_general_paginated(
                client=client,
                activity_type=activity_type,
                cursor=cursor,
                limit=limit or 10,
                unit=unit,
            )

        # Pattern 5: Last activity (default)
        activity = client.safe_call("get_last_activity")

        if not activity:
            return ResponseBuilder.build_response(
                data={"activity": None},
                analysis={"insights": ["No activities found"]},
            )

        formatted_activity = ResponseBuilder.format_activity(activity, unit)

        return ResponseBuilder.build_response(
            data={"activity": formatted_activity},
            metadata={"query_type": "last_activity", "unit": unit},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "garmin_api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")


async def get_activity_details(
    activity_id: Annotated[int, "Activity ID"],
    include_splits: Annotated[bool, "Include lap/split data"] = True,
    include_weather: Annotated[bool, "Include weather conditions"] = True,
    include_hr_zones: Annotated[bool, "Include heart rate zone data"] = True,
    include_gear: Annotated[bool, "Include gear information"] = True,
    include_exercise_sets: Annotated[bool, "Include exercise sets (for strength training)"] = False,
    unit: Annotated[str, "Unit system: 'metric' or 'imperial'"] = "metric",
) -> str:
    """
    Get comprehensive details for a specific activity.

    Fetch exactly the information you need about an activity with flexible
    detail options.

    By default, includes splits, weather, HR zones, and gear. Exercise sets
    are only included when explicitly requested (useful for strength training).
    """
    try:
        client = _get_client()

        # Start with base activity data
        activity = client.safe_call("get_activity", activity_id)

        if not activity:
            return ResponseBuilder.build_error_response(
                f"Activity {activity_id} not found",
                "not_found",
                [
                    "Check that the activity ID is correct",
                    "Try query_activities() to list recent activities",
                ],
            )

        # Format base activity
        formatted_activity = ResponseBuilder.format_activity(activity, unit)
        details: dict = {"activity": formatted_activity}

        # Fetch optional details
        if include_splits:
            try:
                splits = client.safe_call("get_activity_splits", activity_id)
                details["splits"] = splits
            except Exception:
                details["splits"] = None

        if include_weather:
            try:
                weather = client.safe_call("get_activity_weather", activity_id)
                details["weather"] = weather
            except Exception:
                details["weather"] = None

        if include_hr_zones:
            try:
                hr_zones = client.safe_call("get_activity_hr_in_timezones", activity_id)
                details["hr_zones"] = hr_zones
            except Exception:
                details["hr_zones"] = None

        if include_gear:
            try:
                gear = client.safe_call("get_activity_gear", activity_id)
                details["gear"] = gear
            except Exception:
                details["gear"] = None

        if include_exercise_sets:
            try:
                sets = client.safe_call("get_activity_exercise_sets", activity_id)
                details["exercise_sets"] = sets
            except Exception:
                details["exercise_sets"] = None

        # Generate insights based on available data
        insights = []
        if details.get("weather"):
            insights.append("Weather data available for this activity")
        if details.get("hr_zones"):
            insights.append("Heart rate zone distribution available")
        if details.get("splits"):
            insights.append("Lap/split data available for pace analysis")
        if details.get("gear"):
            insights.append("Gear information recorded for this activity")

        return ResponseBuilder.build_response(
            data=details,
            analysis={"insights": insights} if insights else None,
            metadata={
                "activity_id": activity_id,
                "unit": unit,
                "includes": {
                    "splits": include_splits,
                    "weather": include_weather,
                    "hr_zones": include_hr_zones,
                    "gear": include_gear,
                    "exercise_sets": include_exercise_sets,
                },
            },
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "garmin_api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")


async def get_activity_social(
    activity_id: Annotated[int, "Activity ID to get social details for"],
) -> str:
    """
    Get social details for an activity (likes, comments, kudos).

    Args:
        activity_id: The Garmin Connect activity ID

    Returns:
        Structured JSON with social data, analysis, and metadata
    """
    try:
        client = _get_client()

        # Get activity social details
        social = client.safe_call("get_activity_social", activity_id)

        # Generate insights
        insights = []
        if social:
            # Count likes/kudos
            likes_count = 0
            if isinstance(social, dict):
                if "likes" in social and isinstance(social["likes"], list):
                    likes_count = len(social["likes"])
                elif "kudos" in social and isinstance(social["kudos"], list):
                    likes_count = len(social["kudos"])

            if likes_count > 0:
                insights.append(f"Received {likes_count} like(s)/kudo(s)")

            # Count comments
            comments_count = 0
            if (
                isinstance(social, dict)
                and "comments" in social
                and isinstance(social["comments"], list)
            ):
                comments_count = len(social["comments"])

            if comments_count > 0:
                insights.append(f"Has {comments_count} comment(s)")

            if likes_count == 0 and comments_count == 0:
                insights.append("No social interactions yet")

        return ResponseBuilder.build_response(
            data={"activity_id": activity_id, "social": social},
            analysis={"insights": insights} if insights else None,
            metadata={"activity_id": activity_id},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "garmin_api_error",
            ["Check your Garmin Connect credentials", "Verify the activity ID is correct"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")
