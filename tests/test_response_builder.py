"""Tests for ResponseBuilder."""

import json
from datetime import datetime

from garmin_connect_mcp.response_builder import ResponseBuilder


def test_format_date_with_day_datetime():
    """Test formatting datetime object with day-of-week information."""
    dt = datetime(2025, 10, 15, 14, 30, 0)
    result = ResponseBuilder.format_date_with_day(dt)

    assert result is not None
    assert result["datetime"] == "2025-10-15T14:30:00"
    assert result["date"] == "2025-10-15"
    assert result["day_of_week"] == "Wednesday"
    assert result["formatted"] == "Wednesday, October 15, 2025 at 02:30 PM"


def test_format_date_with_day_iso_string():
    """Test formatting ISO datetime string with day-of-week information."""
    dt_str = "2025-10-15T14:30:00"
    result = ResponseBuilder.format_date_with_day(dt_str)

    assert result is not None
    assert result["datetime"] == "2025-10-15T14:30:00"
    assert result["date"] == "2025-10-15"
    assert result["day_of_week"] == "Wednesday"
    assert result["formatted"] == "Wednesday, October 15, 2025 at 02:30 PM"


def test_format_date_with_day_iso_string_with_z():
    """Test formatting ISO datetime string with Z timezone."""
    dt_str = "2025-10-15T14:30:00Z"
    result = ResponseBuilder.format_date_with_day(dt_str)

    assert result is not None
    assert result["datetime"] == "2025-10-15T14:30:00Z"
    assert result["date"] == "2025-10-15"
    assert result["day_of_week"] == "Wednesday"
    assert "Wednesday, October 15, 2025" in result["formatted"]


def test_format_date_with_day_none():
    """Test formatting None returns None."""
    result = ResponseBuilder.format_date_with_day(None)
    assert result is None


def test_format_date_with_day_monday():
    """Test formatting a Monday."""
    dt = datetime(2025, 10, 13, 9, 0, 0)
    result = ResponseBuilder.format_date_with_day(dt)

    assert result is not None
    assert result["day_of_week"] == "Monday"
    assert "Monday" in result["formatted"]


def test_build_response_with_datetime_conversion():
    """Test that build_response converts datetime objects to ISO strings."""
    data = {
        "activity_date": datetime(2025, 10, 15, 14, 30, 0),
        "name": "Morning Run",
    }

    result = ResponseBuilder.build_response(data)
    parsed = json.loads(result)

    assert "2025-10-15T14:30:00" in parsed["data"]["activity_date"]
    assert parsed["data"]["name"] == "Morning Run"
    assert "metadata" in parsed
    assert "fetched_at" in parsed["metadata"]


def test_format_activity_with_date_fields():
    """Test that format_activity uses format_date_with_day for date fields."""
    activity = {
        "activityId": 12345,
        "activityName": "Morning Run",
        "startTimeLocal": "2025-10-15T06:30:00",
        "distance": 5000,
        "duration": 1800,
    }

    result = ResponseBuilder.format_activity(activity)

    assert "startTimeLocal" in result
    assert isinstance(result["startTimeLocal"], dict)
    assert result["startTimeLocal"]["date"] == "2025-10-15"
    assert result["startTimeLocal"]["day_of_week"] == "Wednesday"
    assert "Wednesday" in result["startTimeLocal"]["formatted"]


def test_format_activity_with_all_date_fields():
    """Test that all date fields get formatted with day-of-week."""
    activity = {
        "activityId": 12345,
        "startTimeLocal": "2025-10-15T06:30:00",
        "startTimeGMT": "2025-10-15T10:30:00Z",
        "endTimeLocal": "2025-10-15T07:00:00",
    }

    result = ResponseBuilder.format_activity(activity)

    # All date fields should be formatted
    for field in ["startTimeLocal", "startTimeGMT", "endTimeLocal"]:
        assert field in result
        assert isinstance(result[field], dict)
        assert "date" in result[field]
        assert "day_of_week" in result[field]
        assert "formatted" in result[field]
        assert "datetime" in result[field]


def test_format_activity_with_missing_dates():
    """Test that format_activity handles missing date fields gracefully."""
    activity = {
        "activityId": 12345,
        "activityName": "Morning Run",
        "distance": 5000,
    }

    result = ResponseBuilder.format_activity(activity)

    # Should not have date fields if they weren't in the original
    assert "startTimeLocal" not in result or result.get("startTimeLocal") is None
