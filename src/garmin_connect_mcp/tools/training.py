"""Training and performance tools for Garmin Connect MCP server."""

from collections import defaultdict
from datetime import datetime
from typing import Annotated, Any

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder
from ..time_utils import (
    format_date_for_api,
    get_range_description,
    get_week_ranges,
    parse_time_range,
)
from ..types import UnitSystem


async def analyze_training_period(
    period: Annotated[
        str, "Time period: '7d', '30d', '90d', 'ytd', 'this-month', or 'YYYY-MM-DD:YYYY-MM-DD'"
    ] = "30d",
    activity_type: Annotated[
        str, "Filter by activity type (e.g., 'running', 'cycling'). Empty for all."
    ] = "",
    unit: Annotated[UnitSystem, "Unit system: 'metric' or 'imperial'"] = "metric",
    ctx: Context | None = None,
) -> str:
    """
    Analyze training over a specified period with comprehensive insights.

    Provides:
    - Total volume (activities, distance, time, elevation)
    - Activity type breakdown
    - Weekly trends
    - Performance insights

    Example periods: "30d", "this-month", "2024-01-01:2024-01-31"
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        # Parse period
        start_date, end_date = parse_time_range(period)
        period_description = get_range_description(period)

        # Fetch activities for period
        start_str = format_date_for_api(start_date)
        end_str = format_date_for_api(end_date)

        activities = client.safe_call("get_activities_by_date", start_str, end_str, activity_type)

        if not activities or len(activities) == 0:
            return ResponseBuilder.build_response(
                data={
                    "period": {
                        "description": period_description,
                        "start_date": start_str,
                        "end_date": end_str,
                        "days": (end_date - start_date).days + 1,
                    },
                    "summary": {
                        "total_activities": 0,
                    },
                },
                analysis={"insights": ["No activities found in this period"]},
                metadata={"period": period, "activity_type": activity_type or "all"},
            )

        # Calculate summary metrics
        total_distance = sum(act.get("distance", 0) or 0 for act in activities)
        total_time = sum(act.get("duration", 0) or 0 for act in activities)
        total_elevation = sum(act.get("elevationGain", 0) or 0 for act in activities)

        # Group by activity type
        by_type: dict[str, Any] = defaultdict(lambda: {"count": 0, "distance": 0, "time": 0})
        for act in activities:
            act_type = act.get("activityType", {}).get("typeKey", "unknown")
            by_type[act_type]["count"] += 1
            by_type[act_type]["distance"] += act.get("distance", 0) or 0
            by_type[act_type]["time"] += act.get("duration", 0) or 0

        # Format by_type for output
        by_type_list = []
        for type_key, data in sorted(by_type.items(), key=lambda x: x[1]["count"], reverse=True):
            percentage = (data["count"] / len(activities) * 100) if activities else 0
            by_type_list.append(
                {
                    "type": type_key,
                    "count": data["count"],
                    "percentage": round(percentage, 1),
                    "distance": {
                        "meters": data["distance"],
                        "formatted": ResponseBuilder._format_distance(data["distance"], unit),
                    },
                    "time": {
                        "seconds": data["time"],
                        "formatted": ResponseBuilder._format_duration(data["time"]),
                    },
                }
            )

        # Weekly breakdown
        weeks = get_week_ranges(start_date, end_date)
        weekly_trends = []

        for week_start, week_end in weeks:
            week_start_str = format_date_for_api(week_start)
            week_end_str = format_date_for_api(week_end)

            # Filter activities for this week
            week_activities = [
                act
                for act in activities
                if week_start_str <= act.get("startTimeLocal", "")[:10] <= week_end_str
            ]

            week_distance = sum(act.get("distance", 0) or 0 for act in week_activities)
            week_time = sum(act.get("duration", 0) or 0 for act in week_activities)

            weekly_trends.append(
                {
                    "week_start": ResponseBuilder.format_date_with_day(week_start),
                    "week_end": ResponseBuilder.format_date_with_day(week_end),
                    "activities": len(week_activities),
                    "distance": {
                        "meters": week_distance,
                        "formatted": ResponseBuilder._format_distance(week_distance, unit),
                    },
                    "time": {
                        "seconds": week_time,
                        "formatted": ResponseBuilder._format_duration(week_time),
                    },
                }
            )

        # Build data structure
        days_in_period = (end_date - start_date).days + 1
        data = {
            "period": {
                "description": period_description,
                "start_date": start_str,
                "end_date": end_str,
                "days": days_in_period,
            },
            "summary": {
                "total_activities": len(activities),
                "total_distance": {
                    "meters": total_distance,
                    "formatted": ResponseBuilder._format_distance(total_distance, unit),
                },
                "total_time": {
                    "seconds": total_time,
                    "formatted": ResponseBuilder._format_duration(total_time),
                },
                "total_elevation": {
                    "meters": total_elevation,
                    "formatted": ResponseBuilder._format_elevation(total_elevation, unit),
                },
                "averages": {
                    "distance_per_activity": {
                        "meters": total_distance / len(activities) if activities else 0,
                        "formatted": ResponseBuilder._format_distance(
                            total_distance / len(activities) if activities else 0, unit
                        ),
                    },
                    "activities_per_week": round(len(activities) / (days_in_period / 7), 1)
                    if days_in_period > 0
                    else 0,
                },
            },
            "by_activity_type": by_type_list,
            "trends": {"weekly": weekly_trends},
        }

        # Generate insights
        insights = []

        # Activity volume insight
        if len(activities) >= 15:
            insights.append(
                f"High training volume: {len(activities)} activities in {days_in_period} days"
            )
        elif len(activities) >= 8:
            insights.append(
                f"Moderate training volume: {len(activities)} activities in {days_in_period} days"
            )
        else:
            insights.append(
                f"Light training volume: {len(activities)} activities in {days_in_period} days"
            )

        # Trend insight
        if len(weekly_trends) >= 2:
            first_half = weekly_trends[: len(weekly_trends) // 2]
            second_half = weekly_trends[len(weekly_trends) // 2 :]
            first_half_count = sum(w["activities"] for w in first_half)
            second_half_count = sum(w["activities"] for w in second_half)

            if second_half_count > first_half_count * 1.2:
                insights.append("Training volume increasing over time")
            elif second_half_count < first_half_count * 0.8:
                insights.append("Training volume decreasing over time")
            else:
                insights.append("Training volume relatively consistent")

        # Activity type insight
        if by_type_list:
            dominant_type = by_type_list[0]
            if dominant_type["percentage"] > 70:
                insights.append(f"Training heavily focused on {dominant_type['type']}")
            elif dominant_type["percentage"] > 50:
                insights.append(f"Training primarily focused on {dominant_type['type']}")
            else:
                insights.append("Varied training across multiple activity types")

        return ResponseBuilder.build_response(
            data=data,
            analysis={"insights": insights},
            metadata={"period": period, "activity_type": activity_type or "all", "unit": unit},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


async def get_performance_metrics(
    date: Annotated[str | None, "Specific date (YYYY-MM-DD) for single-day metrics"] = None,
    start_date: Annotated[str | None, "Start date (YYYY-MM-DD) for range metrics"] = None,
    end_date: Annotated[str | None, "End date (YYYY-MM-DD) for range metrics"] = None,
    include_vo2_max: Annotated[bool, "Include VO2 max data"] = True,
    include_hill_score: Annotated[bool, "Include hill climbing score"] = True,
    include_endurance_score: Annotated[bool, "Include endurance score"] = True,
    include_hrv: Annotated[bool, "Include heart rate variability"] = True,
    include_fitness_age: Annotated[bool, "Include fitness age calculation"] = True,
    ctx: Context | None = None,
) -> str:
    """
    Get comprehensive performance metrics.

    Includes VO2 max, hill score, endurance score, heart rate variability,
    and fitness age data.

    Supports both single-date and date-range queries.
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        # Determine query type
        if date:
            # Single date query
            is_range = False
            query_date = date
        elif start_date and end_date:
            # Range query
            is_range = True
            query_start = start_date
            query_end = end_date
        else:
            # Default to today
            is_range = False
            query_date = datetime.now().strftime("%Y-%m-%d")

        metrics_data: dict[str, Any] = {}

        # Single-date metrics
        if not is_range:
            # VO2 max (max metrics)
            if include_vo2_max:
                try:
                    vo2_max = client.safe_call("get_max_metrics", query_date)
                    metrics_data["vo2_max"] = vo2_max
                except Exception:
                    metrics_data["vo2_max"] = None

            # HRV
            if include_hrv:
                try:
                    hrv = client.safe_call("get_hrv_data", query_date)
                    metrics_data["hrv"] = hrv
                except Exception:
                    metrics_data["hrv"] = None

            # Fitness age
            if include_fitness_age:
                try:
                    fitness_age = client.safe_call("get_fitness_age", query_date)
                    metrics_data["fitness_age"] = fitness_age
                except Exception:
                    metrics_data["fitness_age"] = None

            metadata = {"date": query_date}
        else:
            # Range metrics
            # Hill score
            if include_hill_score:
                try:
                    hill_score = client.safe_call("get_hill_score", query_start, query_end)
                    metrics_data["hill_score"] = hill_score
                except Exception:
                    metrics_data["hill_score"] = None

            # Endurance score
            if include_endurance_score:
                try:
                    endurance_score = client.safe_call(
                        "get_endurance_score", query_start, query_end
                    )
                    metrics_data["endurance_score"] = endurance_score
                except Exception:
                    metrics_data["endurance_score"] = None

            metadata = {"start_date": query_start, "end_date": query_end}

        # Generate insights
        insights = []
        available_metrics = [k for k, v in metrics_data.items() if v is not None]
        if available_metrics:
            insights.append(f"Available performance metrics: {', '.join(available_metrics)}")
        else:
            insights.append("No performance metrics available for this period")

        return ResponseBuilder.build_response(
            data=metrics_data,
            analysis={"insights": insights} if insights else None,
            metadata=metadata,
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


async def get_training_effect(
    activity_id: Annotated[int | None, "Activity ID for training effect"] = None,
    start_date: Annotated[str | None, "Start date (YYYY-MM-DD) for progress summary"] = None,
    end_date: Annotated[str | None, "End date (YYYY-MM-DD) for progress summary"] = None,
    metric: Annotated[str, "Metric to track for progress summary"] = "distance",
    ctx: Context | None = None,
) -> str:
    """
    Get training effect and progress summary.

    Supports:
    1. Training effect for specific activity (provide activity_id)
    2. Progress summary over date range (provide start_date, end_date, metric)
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        # Pattern 1: Training effect for activity
        if activity_id is not None:
            effect = client.safe_call("get_training_effect", activity_id)

            return ResponseBuilder.build_response(
                data={"training_effect": effect},
                metadata={"activity_id": activity_id},
            )

        # Pattern 2: Progress summary
        elif start_date and end_date:
            summary = client.safe_call(
                "get_progress_summary_between_dates", start_date, end_date, metric
            )

            return ResponseBuilder.build_response(
                data={"progress_summary": summary},
                metadata={"start_date": start_date, "end_date": end_date, "metric": metric},
            )

        else:
            return ResponseBuilder.build_error_response(
                "Must provide either activity_id OR (start_date + end_date)",
                "invalid_parameters",
                [
                    "For training effect: provide activity_id",
                    "For progress summary: provide start_date, end_date, and optionally metric",
                ],
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
