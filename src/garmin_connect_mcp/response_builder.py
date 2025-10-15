"""Response builder for structured Garmin Connect MCP responses."""

import json
from datetime import datetime
from typing import Any

from .types import JSONSerializable


class ResponseBuilder:
    """Build structured responses with data, analysis, and metadata."""

    @staticmethod
    def build_response(
        data: JSONSerializable,
        analysis: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Build a structured response with data, optional analysis, and metadata.

        Args:
            data: The primary data payload
            analysis: Optional analysis and insights about the data
            metadata: Optional metadata about the query/response

        Returns:
            JSON string with structured response
        """
        response: dict[str, Any] = {"data": data}

        if analysis:
            response["analysis"] = analysis

        if metadata:
            response["metadata"] = metadata

        # Add default metadata
        if "metadata" not in response:
            response["metadata"] = {}

        response["metadata"]["fetched_at"] = datetime.utcnow().isoformat() + "Z"

        return json.dumps(response, indent=2, default=str)

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
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }

        if suggestions:
            response["error"]["suggestions"] = suggestions

        return json.dumps(response, indent=2)

    @staticmethod
    def format_activity(activity_dict: dict[str, Any], unit: str = "metric") -> dict[str, Any]:
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

        # Format dates
        for date_field in ["startTimeLocal", "startTimeGMT", "endTimeLocal"]:
            if date_field in activity_dict and activity_dict[date_field]:
                formatted[date_field] = {
                    "timestamp": activity_dict[date_field],
                    "formatted": ResponseBuilder._format_datetime(activity_dict[date_field]),
                }

        return formatted

    @staticmethod
    def format_health_metric(metric_dict: dict[str, Any], unit: str = "metric") -> dict[str, Any]:
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
    def _format_distance(meters: float, unit: str = "metric") -> str:
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
    def _format_elevation(meters: float, unit: str = "metric") -> str:
        """Format elevation with units."""
        if unit == "imperial":
            feet = meters * 3.28084
            return f"{feet:.0f} ft"
        else:
            return f"{meters:.0f} m"

    @staticmethod
    def _format_speed(mps: float, unit: str = "metric") -> str:
        """Format speed from m/s."""
        if unit == "imperial":
            mph = mps * 2.23694
            return f"{mph:.2f} mph"
        else:
            kmh = mps * 3.6
            return f"{kmh:.2f} km/h"

    @staticmethod
    def _format_pace(mps: float, unit: str = "metric") -> str:
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
    def _format_weight(grams: float, unit: str = "metric") -> str:
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
