"""Response builder for structured Garmin Connect MCP responses."""

import json
from datetime import UTC, datetime
from typing import Any, cast

from .pagination import PaginationInfo
from .types import JSONSerializable, UnitSystem


def _convert_datetimes(obj: Any) -> Any:  # type: ignore[misc]
    """Recursively convert datetime objects to ISO strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {str(k): _convert_datetimes(v) for k, v in obj.items()}  # type: ignore[misc]
    elif isinstance(obj, list):
        return [_convert_datetimes(item) for item in obj]  # type: ignore[misc]
    return obj


class ResponseBuilder:
    """Build structured responses with data, analysis, and metadata."""

    @staticmethod
    def format_date_with_day(dt: datetime | str | None) -> dict[str, str] | None:
        """Format a date/datetime with explicit day-of-week information.

        Args:
            dt: datetime object or ISO string or None

        Returns:
            Dict with datetime, date, day_of_week, and formatted string, or None if input is None

        Examples:
            >>> ResponseBuilder.format_date_with_day(datetime(2025, 10, 15, 14, 30))
            {
                "datetime": "2025-10-15T14:30:00",
                "date": "2025-10-15",
                "day_of_week": "Wednesday",
                "formatted": "Wednesday, October 15, 2025 at 02:30 PM"
            }
        """
        if dt is None:
            return None

        # Parse the datetime if it's a string, otherwise use it directly
        if isinstance(dt, str):
            parsed_dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        else:
            parsed_dt = dt

        return {
            "datetime": dt if isinstance(dt, str) else dt.isoformat(),
            "date": parsed_dt.strftime("%Y-%m-%d"),
            "day_of_week": parsed_dt.strftime("%A"),  # e.g., "Monday"
            "formatted": parsed_dt.strftime(
                "%A, %B %d, %Y at %I:%M %p"
            ),  # e.g., "Monday, October 15, 2025 at 02:30 PM"
        }

    @staticmethod
    def build_response(
        data: JSONSerializable,
        analysis: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        pagination: PaginationInfo | dict[str, Any] | None = None,
    ) -> str:
        """
        Build a structured response with data, optional analysis, and metadata.

        Args:
            data: The primary data payload
            analysis: Optional analysis and insights about the data
            metadata: Optional metadata about the query/response
            pagination: Optional pagination metadata

        Returns:
            JSON string with structured response
        """
        # Convert datetime objects to ISO strings
        converted_data = cast(JSONSerializable, _convert_datetimes(data))
        converted_analysis: dict[str, Any] | None = None
        if analysis:
            converted_analysis = cast(dict[str, Any], _convert_datetimes(analysis))

        response: dict[str, Any] = {"data": converted_data}

        if converted_analysis:
            response["analysis"] = converted_analysis

        if pagination:
            response["pagination"] = pagination

        # Build metadata with timestamp
        meta = metadata or {}
        converted_meta = cast(dict[str, Any], _convert_datetimes(meta))
        converted_meta["fetched_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        response["metadata"] = converted_meta

        return json.dumps(response, separators=(",", ":"))

    @staticmethod
    def build_error_response(
        message: str, error_type: str = "error", suggestions: list[str] | None = None
    ) -> str:
        """
        Build a structured error response.

        Args:
            message: Error message
            error_type: Type of error (error, warning, etc.)
            suggestions: Optional list of suggestions to resolve the error

        Returns:
            JSON string with error response
        """
        response: dict[str, Any] = {
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
        }

        if suggestions:
            response["error"]["suggestions"] = suggestions

        return json.dumps(response, separators=(",", ":"))

    @staticmethod
    def format_activity(
        activity_dict: dict[str, Any], unit: UnitSystem = "metric"
    ) -> dict[str, Any]:
        """
        Format an activity with rich formatting (raw + human-readable).

        Args:
            activity_dict: Raw activity data
            unit: Unit system ('metric' or 'imperial')

        Returns:
            Formatted activity dictionary with enhanced fields
        """
        formatted = activity_dict.copy()

        # Format distance
        if "distance" in activity_dict and activity_dict["distance"] is not None:
            meters = activity_dict["distance"]
            formatted["distance"] = {
                "meters": meters,
                "formatted": ResponseBuilder._format_distance(meters, unit),
            }

        # Format duration
        if "duration" in activity_dict and activity_dict["duration"] is not None:
            seconds = activity_dict["duration"]
            formatted["duration"] = {
                "seconds": seconds,
                "formatted": ResponseBuilder._format_duration(seconds),
            }

        # Format elevation
        if "elevationGain" in activity_dict and activity_dict["elevationGain"] is not None:
            meters = activity_dict["elevationGain"]
            formatted["elevationGain"] = {
                "meters": meters,
                "formatted": ResponseBuilder._format_elevation(meters, unit),
            }

        # Format pace/speed
        if "averageSpeed" in activity_dict and activity_dict["averageSpeed"] is not None:
            mps = activity_dict["averageSpeed"]
            formatted["averageSpeed"] = {
                "mps": mps,
                "formatted_speed": ResponseBuilder._format_speed(mps, unit),
                "formatted_pace": ResponseBuilder._format_pace(mps, unit),
            }

        # Format dates with day-of-week information
        for date_field in ["startTimeLocal", "startTimeGMT", "endTimeLocal"]:
            if date_field in activity_dict and activity_dict[date_field]:
                formatted[date_field] = ResponseBuilder.format_date_with_day(
                    activity_dict[date_field]
                )

        # Format heart rate
        if "averageHR" in activity_dict and activity_dict["averageHR"] is not None:
            formatted["heart_rate"] = {"avg_bpm": round(activity_dict["averageHR"])}

        if "maxHR" in activity_dict and activity_dict["maxHR"] is not None:
            if "heart_rate" not in formatted:
                formatted["heart_rate"] = {}
            formatted["heart_rate"]["max_bpm"] = round(activity_dict["maxHR"])

        # Format power
        if "avgPower" in activity_dict and activity_dict["avgPower"] is not None:
            formatted["power"] = {"avg_watts": round(activity_dict["avgPower"])}

        if "maxPower" in activity_dict and activity_dict["maxPower"] is not None:
            if "power" not in formatted:
                formatted["power"] = {}
            formatted["power"]["max_watts"] = round(activity_dict["maxPower"])

        # Format cadence
        if "avgRunCadence" in activity_dict and activity_dict["avgRunCadence"] is not None:
            formatted["cadence"] = {"avg_spm": round(activity_dict["avgRunCadence"])}
        elif (
            "averageBikingCadenceInRevPerMinute" in activity_dict
            and activity_dict["averageBikingCadenceInRevPerMinute"] is not None
        ):
            formatted["cadence"] = {
                "avg_rpm": round(activity_dict["averageBikingCadenceInRevPerMinute"])
            }

        # Format calories
        if "calories" in activity_dict and activity_dict["calories"] is not None:
            formatted["calories"] = activity_dict["calories"]

        return formatted

    @staticmethod
    def format_health_metric(
        metric_dict: dict[str, Any], unit: UnitSystem = "metric"
    ) -> dict[str, Any]:
        """
        Format a health metric with rich formatting.

        Args:
            metric_dict: Raw health metric data
            unit: Unit system ('metric' or 'imperial')

        Returns:
            Formatted metric dictionary
        """
        formatted = metric_dict.copy()

        # Format weight
        if "weight" in metric_dict and metric_dict["weight"] is not None:
            grams = metric_dict["weight"]
            formatted["weight"] = {
                "grams": grams,
                "formatted": ResponseBuilder._format_weight(grams, unit),
            }

        # Format steps
        if "steps" in metric_dict and metric_dict["steps"] is not None:
            steps = metric_dict["steps"]
            formatted["steps"] = {
                "value": steps,
                "formatted": f"{steps:,}",
            }

        # Format heart rate
        if "heartRate" in metric_dict and metric_dict["heartRate"] is not None:
            hr = metric_dict["heartRate"]
            formatted["heartRate"] = {
                "bpm": hr,
                "formatted": f"{hr} bpm",
            }

        return formatted

    # Helper formatting methods
    @staticmethod
    def _format_distance(meters: float, unit: UnitSystem = "metric") -> str:
        """Format distance with units."""
        if unit == "imperial":
            miles = meters / 1609.34
            return f"{miles:.2f} mi"
        else:
            km = meters / 1000
            return f"{km:.2f} km"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    @staticmethod
    def _format_elevation(meters: float, unit: UnitSystem = "metric") -> str:
        """Format elevation with units."""
        if unit == "imperial":
            feet = meters * 3.28084
            return f"{feet:.0f} ft"
        else:
            return f"{meters:.0f} m"

    @staticmethod
    def _format_speed(mps: float, unit: UnitSystem = "metric") -> str:
        """Format speed from m/s."""
        if unit == "imperial":
            mph = mps * 2.23694
            return f"{mph:.2f} mph"
        else:
            kmh = mps * 3.6
            return f"{kmh:.2f} km/h"

    @staticmethod
    def _format_pace(mps: float, unit: UnitSystem = "metric") -> str:
        """Format pace from m/s."""
        if mps == 0:
            return "N/A"

        if unit == "imperial":
            # min/mile
            seconds_per_mile = 1609.34 / mps
            minutes = int(seconds_per_mile // 60)
            seconds = int(seconds_per_mile % 60)
            return f"{minutes}:{seconds:02d} /mi"
        else:
            # min/km
            seconds_per_km = 1000 / mps
            minutes = int(seconds_per_km // 60)
            seconds = int(seconds_per_km % 60)
            return f"{minutes}:{seconds:02d} /km"

    @staticmethod
    def _format_weight(grams: float, unit: UnitSystem = "metric") -> str:
        """Format weight with units."""
        if unit == "imperial":
            lbs = grams / 453.592
            return f"{lbs:.2f} lbs"
        else:
            kg = grams / 1000
            return f"{kg:.2f} kg"

    @staticmethod
    def _format_datetime(date_str: str | datetime | None) -> str:
        """Format a datetime string or datetime object."""
        if date_str is None:
            return "N/A"

        if isinstance(date_str, str):
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return date_str

        if isinstance(date_str, datetime):
            return date_str.strftime("%Y-%m-%d %H:%M:%S")

        return str(date_str)

    @staticmethod
    def aggregate_activities(
        activities: list[dict[str, Any]], unit: UnitSystem = "metric"
    ) -> dict[str, Any]:
        """Aggregate metrics across multiple activities.

        Args:
            activities: List of activity data dictionaries
            unit: Unit preference for formatting

        Returns:
            Dict with aggregated metrics (totals, averages, counts)
        """
        if not activities:
            return {}

        total_distance = sum(a.get("distance", 0) for a in activities)
        total_time = sum(a.get("duration", 0) for a in activities)
        total_elevation = sum(a.get("elevationGain", 0) for a in activities)
        total_calories = sum(a.get("calories", 0) for a in activities)

        aggregated: dict[str, Any] = {
            "count": len(activities),
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
        }

        if total_calories > 0:
            aggregated["total_calories"] = total_calories

        # Average distance per activity
        if len(activities) > 0:
            avg_distance = total_distance / len(activities)
            aggregated["avg_distance_per_activity"] = {
                "meters": avg_distance,
                "formatted": ResponseBuilder._format_distance(avg_distance, unit),
            }

        # Average pace/speed (if applicable)
        if total_time > 0 and total_distance > 0:
            avg_speed = total_distance / total_time
            aggregated["avg_speed"] = {
                "mps": avg_speed,
                "formatted_speed": ResponseBuilder._format_speed(avg_speed, unit),
                "formatted_pace": ResponseBuilder._format_pace(avg_speed, unit),
            }

        return aggregated
