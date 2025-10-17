"""Activity-related tools for Garmin Connect MCP server."""

from typing import Annotated, Any

from fastmcp import Context

from ..client import GarminAPIError, GarminClientWrapper
from ..pagination import build_pagination_info, decode_cursor
from ..response_builder import ResponseBuilder
from ..time_utils import parse_date_string
from ..types import UnitSystem


async def _query_activities_paginated(
    client: GarminClientWrapper,
    start_date: str,
    end_date: str,
    activity_type: str,
    cursor: str | None,
    limit: int,
    unit: UnitSystem,
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
                "query_type": "activity_list",
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

    # Aggregate metrics
    aggregated = ResponseBuilder.aggregate_activities(activities, unit)

    return ResponseBuilder.build_response(
        data={"activities": formatted_activities, "aggregated": aggregated},
        metadata={
            "query_type": "activity_list",
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
    unit: UnitSystem,
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
            metadata={
                "query_type": "activity_list",
                "activity_type": activity_type or "all",
                "unit": unit,
            },
            pagination=pagination,
            analysis={"insights": [f"No activities found{type_msg}"]},
        )

    # Format activities
    formatted_activities = [ResponseBuilder.format_activity(act, unit) for act in activities]

    # Aggregate metrics
    aggregated = ResponseBuilder.aggregate_activities(activities, unit)

    return ResponseBuilder.build_response(
        data={"activities": formatted_activities, "aggregated": aggregated},
        metadata={
            "query_type": "activity_list",
            "activity_type": activity_type or "all",
            "unit": unit,
        },
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
        str | int | None,
        "Maximum activities per page (1-50). Default: 10. "
        "Use pagination cursor for large datasets.",
    ] = None,
    activity_type: Annotated[str, "Activity type filter (e.g., 'running', 'cycling')"] = "",
    unit: Annotated[UnitSystem, "Unit system: 'metric' or 'imperial'"] = "metric",
    ctx: Context | None = None,
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
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        # Coerce limit to int if passed as string
        if limit is not None and isinstance(limit, str):
            try:
                limit = int(limit)
            except ValueError:
                return ResponseBuilder.build_error_response(
                    f"Invalid limit value: '{limit}'. Must be a number between 1 and 50.",
                    error_type="validation_error",
                )

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
                metadata={
                    "query_type": "single_activity",
                    "activity_id": activity_id,
                    "unit": unit,
                },
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

            activities = client.safe_call(
                "get_activities_by_date",
                date_str,
                date_str,
                activity_type if activity_type else None,
            )

            if not activities:
                type_msg = f" of type '{activity_type}'" if activity_type else ""
                return ResponseBuilder.build_response(
                    data={"activities": [], "count": 0},
                    metadata={
                        "query_type": "activity_list",
                        "date": date_str,
                        "activity_type": activity_type or "all",
                        "unit": unit,
                    },
                    analysis={"insights": [f"No activities found{type_msg} for {date_str}"]},
                )

            formatted_activities = [
                ResponseBuilder.format_activity(act, unit) for act in activities
            ]

            # Aggregate metrics
            aggregated = ResponseBuilder.aggregate_activities(activities, unit)

            return ResponseBuilder.build_response(
                data={"activities": formatted_activities, "aggregated": aggregated},
                metadata={
                    "query_type": "activity_list",
                    "date": date_str,
                    "activity_type": activity_type or "all",
                    "unit": unit,
                },
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
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


def _compute_accurate_splits_from_details(
    activity_details: dict[str, Any], unit: UnitSystem = "metric"
) -> dict[str, Any]:
    """
    Compute accurate distance splits from time-series data in activity details.

    Uses actual GPS/sensor data to determine exact times when each km/mile was crossed.
    This provides real split times showing pace variation throughout the activity.

    Args:
        activity_details: Activity details from get_activity_details() API
        unit: Unit system - "metric" for 1km splits, "imperial" for 1 mile splits

    Returns:
        Dictionary with accurate splits information or error details
    """
    # Extract metric descriptors and data
    if "activityDetailMetrics" not in activity_details or "metricDescriptors" not in activity_details:
        return {"accurate": False, "reason": "No time-series metric data available"}

    metrics_data = activity_details["activityDetailMetrics"]
    if not metrics_data:
        return {"accurate": False, "reason": "Empty metrics data"}

    # Find indices for distance and time metrics
    # Index 12 = sumDistance (cumulative distance in meters)
    # Index 8 = sumDuration (cumulative time in seconds)
    DISTANCE_INDEX = 12
    TIME_INDEX = 8

    # Extract time/distance pairs
    time_distance_pairs = []
    for entry in metrics_data:
        metrics = entry.get("metrics", [])
        if len(metrics) > max(DISTANCE_INDEX, TIME_INDEX):
            distance = metrics[DISTANCE_INDEX]
            time = metrics[TIME_INDEX]
            if distance is not None and time is not None:
                time_distance_pairs.append((float(time), float(distance)))

    if len(time_distance_pairs) < 2:
        return {"accurate": False, "reason": "Insufficient time-series data points"}

    # Sort by time (should already be sorted, but ensure it)
    time_distance_pairs.sort(key=lambda x: x[0])

    # Determine split distance based on unit
    split_distance_meters = 1000 if unit == "metric" else 1609.34  # 1 mile
    split_label = "km" if unit == "metric" else "mi"

    # Get total distance from last data point
    total_distance = time_distance_pairs[-1][1]

    if total_distance < split_distance_meters:
        return {"accurate": False, "reason": f"Activity distance less than 1 {split_label}"}

    # Calculate number of complete splits
    num_complete_splits = int(total_distance // split_distance_meters)

    # Function to interpolate time for a given distance
    def find_time_at_distance(target_distance: float) -> float:
        """Find time when target distance was reached using linear interpolation."""
        for i in range(len(time_distance_pairs) - 1):
            time1, dist1 = time_distance_pairs[i]
            time2, dist2 = time_distance_pairs[i + 1]

            if dist1 <= target_distance <= dist2:
                # Linear interpolation
                if dist2 - dist1 == 0:
                    return time1
                ratio = (target_distance - dist1) / (dist2 - dist1)
                return time1 + ratio * (time2 - time1)

        # If not found, return last time (shouldn't happen)
        return time_distance_pairs[-1][0]

    # Calculate splits
    splits = []
    prev_time = 0.0

    for split_num in range(1, num_complete_splits + 1):
        split_distance = split_num * split_distance_meters
        split_time = find_time_at_distance(split_distance)
        segment_time = split_time - prev_time

        # Calculate pace for this segment
        pace_seconds = segment_time  # Time for 1km or 1 mile
        pace_minutes = int(pace_seconds // 60)
        pace_secs = int(pace_seconds % 60)

        # Format distance based on unit
        if unit == "metric":
            distance_display = split_distance_meters / 1000  # km
        else:
            distance_display = split_distance_meters / 1609.34  # miles

        splits.append({
            "split_number": split_num,
            "distance_meters": split_distance_meters,
            "distance_formatted": f"{distance_display:.2f} {split_label}",
            "time_seconds": segment_time,
            "cumulative_time_seconds": split_time,
            "time_formatted": ResponseBuilder._format_duration(segment_time),
            "pace_formatted": f"{pace_minutes}:{pace_secs:02d} /{split_label}",
        })

        prev_time = split_time

    # Add partial split if there's significant remaining distance
    remaining_distance = total_distance - (num_complete_splits * split_distance_meters)
    if remaining_distance >= 100:  # Only if >= 100m
        final_time = time_distance_pairs[-1][0]
        partial_segment_time = final_time - prev_time

        # Calculate pace (extrapolate to full km/mile)
        if remaining_distance > 0:
            pace_per_full_unit = (partial_segment_time / remaining_distance) * split_distance_meters
            pace_minutes = int(pace_per_full_unit // 60)
            pace_secs = int(pace_per_full_unit % 60)
            pace_str = f"{pace_minutes}:{pace_secs:02d} /{split_label}"
        else:
            pace_str = "N/A"

        # Format partial distance
        if unit == "metric":
            partial_distance_display = remaining_distance / 1000  # km
        else:
            partial_distance_display = remaining_distance / 1609.34  # miles

        splits.append({
            "split_number": num_complete_splits + 1,
            "distance_meters": remaining_distance,
            "distance_formatted": f"{partial_distance_display:.2f} {split_label}",
            "time_seconds": partial_segment_time,
            "cumulative_time_seconds": final_time,
            "time_formatted": ResponseBuilder._format_duration(partial_segment_time),
            "pace_formatted": pace_str,
            "partial": True,
        })

    # Calculate average pace
    total_time = time_distance_pairs[-1][0]
    avg_pace_per_km = (total_time / total_distance) * 1000

    return {
        "accurate": True,
        "note": f"Accurate {split_label} splits computed from GPS/sensor data (1398 data points)",
        "average_pace": {
            "seconds_per_km": avg_pace_per_km,
            "formatted": ResponseBuilder._format_pace(total_distance / total_time, unit),
        },
        "splits": splits,
        "total_distance_meters": total_distance,
        "total_duration_seconds": total_time,
        "data_points": len(time_distance_pairs),
    }


def _compute_estimated_splits(activity: dict[str, Any], unit: UnitSystem = "metric") -> dict[str, Any]:
    """
    Compute estimated distance splits when activity has only 1 lap.

    Computes 1km splits for metric units or 1 mile splits for imperial units.
    This provides estimated split times based on average pace,
    useful when the watch wasn't configured for auto-lap.

    Args:
        activity: Activity data containing distance and duration
        unit: Unit system - "metric" for 1km splits, "imperial" for 1 mile splits

    Returns:
        Dictionary with estimated splits information
    """
    distance_meters = activity.get("distance")
    duration_seconds = activity.get("duration")

    if not distance_meters or not duration_seconds:
        return {"estimated": False, "reason": "Missing distance or duration data"}

    # Only compute for activities >= 1km
    if distance_meters < 1000:
        return {"estimated": False, "reason": "Activity distance less than 1km"}

    # Calculate average pace (seconds per km)
    avg_pace_per_km = (duration_seconds / distance_meters) * 1000

    # Determine split distance based on unit system
    split_distance_meters = 1000 if unit == "metric" else 1609.34  # 1 mile
    split_label = "km" if unit == "metric" else "mi"

    # Calculate number of complete splits
    num_complete_splits = int(distance_meters // split_distance_meters)

    if num_complete_splits == 0:
        return {"estimated": False, "reason": f"Activity distance less than 1 {split_label}"}

    # Calculate remaining distance
    remaining_distance = distance_meters - (num_complete_splits * split_distance_meters)

    # Build estimated splits
    estimated_splits = []
    for i in range(1, num_complete_splits + 1):
        split_time_seconds = avg_pace_per_km * (split_distance_meters / 1000)

        # Format pace
        minutes = int(split_time_seconds // 60)
        seconds = int(split_time_seconds % 60)

        # Format distance based on unit
        if unit == "metric":
            distance_display = split_distance_meters / 1000  # km
        else:
            distance_display = split_distance_meters / 1609.34  # miles

        estimated_splits.append({
            "split_number": i,
            "distance_meters": split_distance_meters,
            "distance_formatted": f"{distance_display:.2f} {split_label}",
            "time_seconds": split_time_seconds,
            "time_formatted": ResponseBuilder._format_duration(split_time_seconds),
            "pace_formatted": f"{minutes}:{seconds:02d} /{split_label}",
        })

    # Add partial split if there's remaining distance
    if remaining_distance >= 100:  # Only include if >= 100m
        partial_split_time = avg_pace_per_km * (remaining_distance / 1000)

        # Format partial distance based on unit
        if unit == "metric":
            partial_distance_display = remaining_distance / 1000  # km
        else:
            partial_distance_display = remaining_distance / 1609.34  # miles

        estimated_splits.append({
            "split_number": num_complete_splits + 1,
            "distance_meters": remaining_distance,
            "distance_formatted": f"{partial_distance_display:.2f} {split_label}",
            "time_seconds": partial_split_time,
            "time_formatted": ResponseBuilder._format_duration(partial_split_time),
            "pace_formatted": f"{int(avg_pace_per_km // 60)}:{int(avg_pace_per_km % 60):02d} /{split_label} (avg)",
            "partial": True,
        })

    return {
        "estimated": True,
        "note": f"Estimated {split_label} splits based on average pace (activity had only 1 lap)",
        "average_pace": {
            "seconds_per_km": avg_pace_per_km,
            "formatted": ResponseBuilder._format_pace(distance_meters / duration_seconds, unit),
        },
        "splits": estimated_splits,
        "total_distance_meters": distance_meters,
        "total_duration_seconds": duration_seconds,
    }


async def get_activity_details(
    activity_id: Annotated[int, "Activity ID"],
    include_splits: Annotated[bool, "Include lap/split data"] = True,
    include_weather: Annotated[bool, "Include weather conditions"] = True,
    include_hr_zones: Annotated[bool, "Include heart rate zone data"] = True,
    include_gear: Annotated[bool, "Include gear information"] = True,
    include_exercise_sets: Annotated[bool, "Include exercise sets (for strength training)"] = False,
    unit: Annotated[UnitSystem, "Unit system: 'metric' or 'imperial'"] = "metric",
    ctx: Context | None = None,
) -> str:
    """
    Get comprehensive details for a specific activity.

    Fetch exactly the information you need about an activity with flexible
    detail options.

    By default, includes splits, weather, HR zones, and gear. Exercise sets
    are only included when explicitly requested (useful for strength training).

    When include_splits=True and the activity has only 1 lap, estimated km/mile
    splits will be computed based on average pace.
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

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

                # If only 1 lap, try to compute accurate splits from detailed time-series data
                if splits and "lapDTOs" in splits and len(splits["lapDTOs"]) == 1:
                    # Try to get accurate splits from activity details API
                    try:
                        activity_details = client.safe_call("get_activity_details", activity_id, maxchart=2000)
                        accurate_splits = _compute_accurate_splits_from_details(activity_details, unit)

                        if accurate_splits.get("accurate"):
                            # We got accurate splits from GPS/sensor data!
                            details["computed_splits"] = accurate_splits
                        else:
                            # Fall back to estimated even-pace splits
                            estimated_splits = _compute_estimated_splits(activity, unit)
                            if estimated_splits.get("estimated"):
                                details["computed_splits"] = estimated_splits
                    except Exception:
                        # If details API fails, fall back to estimated splits
                        estimated_splits = _compute_estimated_splits(activity, unit)
                        if estimated_splits.get("estimated"):
                            details["computed_splits"] = estimated_splits

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
        if details.get("computed_splits"):
            computed = details["computed_splits"]
            split_count = len(computed.get("splits", []))
            split_unit = "km" if unit == "metric" else "mile"

            if computed.get("accurate"):
                data_points = computed.get("data_points", 0)
                insights.append(
                    f"Accurate {split_count} × 1{split_unit} splits computed from {data_points} GPS/sensor data points"
                )
            elif computed.get("estimated"):
                insights.append(f"Estimated {split_count} × 1{split_unit} splits computed from average pace")
        if details.get("gear"):
            insights.append("Gear information recorded for this activity")

        return ResponseBuilder.build_response(
            data=details,
            analysis={"insights": insights} if insights else None,
            metadata={
                "query_type": "activity_details",
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
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


async def get_activity_social(
    activity_id: Annotated[int, "Activity ID to get social details for"],
    ctx: Context | None = None,
) -> str:
    """
    Get social details for an activity (likes, comments, kudos).

    Args:
        activity_id: The Garmin Connect activity ID

    Returns:
        Structured JSON with social data, analysis, and metadata
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

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
            metadata={"query_type": "activity_social", "activity_id": activity_id},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify the activity ID is correct"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
