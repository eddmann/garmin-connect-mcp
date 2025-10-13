"""Tests for formatter functions."""

from datetime import datetime

from garmin_connect_mcp.formatters import (
    format_date,
    format_datetime,
    format_distance,
    format_duration,
    format_elevation,
    format_heart_rate_summary,
    format_json,
    format_pace,
    format_sleep_summary,
    format_speed,
    format_steps_summary,
    format_stress_summary,
    format_weight,
)


def test_format_json_dict():
    """Test formatting a dictionary as JSON."""
    data = {"key": "value", "number": 42}
    result = format_json(data)

    assert '"key": "value"' in result
    assert '"number": 42' in result


def test_format_json_list():
    """Test formatting a list as JSON."""
    data = [1, 2, 3, "test"]
    result = format_json(data)

    assert "[" in result
    assert "1" in result
    assert '"test"' in result


def test_format_json_none():
    """Test formatting None."""
    result = format_json(None)
    assert result == "No data available"


def test_format_date_string():
    """Test formatting ISO date string."""
    result = format_date("2024-01-15T10:30:00Z")
    assert result == "2024-01-15"


def test_format_date_datetime():
    """Test formatting datetime object."""
    dt = datetime(2024, 1, 15, 10, 30, 0)
    result = format_date(dt)
    assert result == "2024-01-15"


def test_format_date_none():
    """Test formatting None date."""
    result = format_date(None)
    assert result == "N/A"


def test_format_datetime_string():
    """Test formatting ISO datetime string."""
    result = format_datetime("2024-01-15T10:30:00Z")
    assert "2024-01-15" in result
    assert "10:30:00" in result


def test_format_datetime_datetime():
    """Test formatting datetime object."""
    dt = datetime(2024, 1, 15, 10, 30, 0)
    result = format_datetime(dt)
    assert "2024-01-15" in result
    assert "10:30:00" in result


def test_format_datetime_none():
    """Test formatting None datetime."""
    result = format_datetime(None)
    assert result == "N/A"


def test_format_distance_meters():
    """Test formatting distance from meters to km."""
    result = format_distance(5000)
    assert result == "5.00 km"


def test_format_distance_float():
    """Test formatting float distance."""
    result = format_distance(7850.5)
    assert result == "7.85 km"


def test_format_distance_none():
    """Test formatting None distance."""
    result = format_distance(None)
    assert result == "N/A"


def test_format_duration_hours():
    """Test formatting duration with hours."""
    result = format_duration(3665)  # 1h 1m 5s
    assert "1h" in result
    assert "1m" in result
    assert "5s" in result


def test_format_duration_minutes():
    """Test formatting duration with only minutes."""
    result = format_duration(125)  # 2m 5s
    assert "2m" in result
    assert "5s" in result
    assert "h" not in result


def test_format_duration_seconds():
    """Test formatting duration with only seconds."""
    result = format_duration(45)
    assert result == "45s"


def test_format_duration_none():
    """Test formatting None duration."""
    result = format_duration(None)
    assert result == "N/A"


def test_format_elevation():
    """Test formatting elevation."""
    result = format_elevation(125.7)
    assert result == "126 m"


def test_format_elevation_none():
    """Test formatting None elevation."""
    result = format_elevation(None)
    assert result == "N/A"


def test_format_speed():
    """Test formatting speed from m/s to km/h."""
    result = format_speed(2.78)  # ~10 km/h
    assert "10.0" in result
    assert "km/h" in result


def test_format_speed_zero():
    """Test formatting zero speed."""
    result = format_speed(0)
    assert result == "N/A"


def test_format_speed_none():
    """Test formatting None speed."""
    result = format_speed(None)
    assert result == "N/A"


def test_format_pace():
    """Test formatting pace from m/s to min/km."""
    result = format_pace(2.78)  # ~6:00/km
    assert ":" in result
    assert "/km" in result


def test_format_pace_zero():
    """Test formatting zero pace."""
    result = format_pace(0)
    assert result == "N/A"


def test_format_pace_none():
    """Test formatting None pace."""
    result = format_pace(None)
    assert result == "N/A"


def test_format_weight():
    """Test formatting weight from grams to kg."""
    result = format_weight(75000)
    assert result == "75.00 kg"


def test_format_weight_none():
    """Test formatting None weight."""
    result = format_weight(None)
    assert result == "N/A"


def test_format_sleep_summary(sample_sleep_data):
    """Test formatting sleep data summary."""
    result = format_sleep_summary(sample_sleep_data)

    assert "Sleep Period" in result
    assert "Total Sleep: 8.0h" in result
    assert "Deep:" in result
    assert "Light:" in result
    assert "REM:" in result
    assert "Sleep Score: 85/100" in result


def test_format_sleep_summary_empty():
    """Test formatting empty sleep data."""
    result = format_sleep_summary({})
    assert "No sleep data available" in result


def test_format_stress_summary(sample_stress_data):
    """Test formatting stress data summary."""
    result = format_stress_summary(sample_stress_data)

    assert "Date: 2024-01-15" in result
    assert "Average Stress: 35" in result
    assert "Maximum Stress: 72" in result
    assert "Moderate stress" in result or "Low stress" in result


def test_format_stress_summary_empty():
    """Test formatting empty stress data."""
    result = format_stress_summary({})
    assert "No stress data available" in result


def test_format_heart_rate_summary_list(sample_heart_rate_list):
    """Test formatting heart rate data (list format)."""
    result = format_heart_rate_summary(sample_heart_rate_list)

    assert "Heart Rate Summary" in result
    assert "Average:" in result
    assert "Minimum:" in result
    assert "Maximum:" in result
    assert "bpm" in result


def test_format_heart_rate_summary_dict(sample_heart_rate_data):
    """Test formatting heart rate data (dictionary format)."""
    result = format_heart_rate_summary(sample_heart_rate_data)

    assert "Heart Rate Summary" in result
    assert "Resting: 58 bpm" in result
    assert "Average: 75 bpm" in result


def test_format_heart_rate_summary_empty():
    """Test formatting empty heart rate data."""
    result = format_heart_rate_summary([])
    assert "No heart rate data available" in result


def test_format_steps_summary_dict(sample_steps_data):
    """Test formatting steps data (dictionary format)."""
    result = format_steps_summary(sample_steps_data)

    assert "Total Steps: 10,543" in result
    assert "Daily Goal: 10,000" in result
    assert "105%" in result or "complete" in result
    assert "Distance:" in result


def test_format_steps_summary_list():
    """Test formatting steps data (list format)."""
    steps_list = [
        {"steps": 1200, "startGMT": "2024-01-15T08:00:00"},
        {"steps": 2300, "startGMT": "2024-01-15T09:00:00"},
    ]
    result = format_steps_summary(steps_list)

    assert "Total Steps: 3,500" in result
    assert "Time Periods:" in result


def test_format_steps_summary_empty():
    """Test formatting empty steps data."""
    result = format_steps_summary({})
    assert "No steps data available" in result
