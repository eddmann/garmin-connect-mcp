"""Tests to verify response sizes are within MCP limits."""

import json

from garmin_connect_mcp.pagination import build_pagination_info
from garmin_connect_mcp.response_builder import ResponseBuilder


def test_json_is_compact():
    """Test that JSON responses are compact (no indentation)."""
    data = {"activities": [{"id": 1, "name": "Test"}], "count": 1}
    response = ResponseBuilder.build_response(data=data)

    # Parse and verify it's valid JSON
    parsed = json.loads(response)
    assert parsed["data"] == data

    # Verify no indentation (compact)
    assert "\n" not in response  # No newlines
    assert "  " not in response  # No double spaces (indent=2 would create these)


def test_pagination_response_is_compact():
    """Test that paginated responses are compact."""
    data = {"activities": [{"id": i} for i in range(10)], "count": 10}
    pagination = build_pagination_info(
        returned_count=10, limit=10, current_page=1, has_more=True, filters={"test": "value"}
    )

    response = ResponseBuilder.build_response(data=data, pagination=pagination)

    # Verify it's compact
    assert "\n" not in response
    assert "  " not in response

    # Verify structure is intact
    parsed = json.loads(response)
    assert parsed["pagination"]["has_more"] is True
    assert parsed["pagination"]["limit"] == 10


def test_error_response_is_compact():
    """Test that error responses are compact."""
    response = ResponseBuilder.build_error_response(
        "Test error", error_type="test_error", suggestions=["Try this", "Try that"]
    )

    # Verify it's compact
    assert "\n" not in response
    assert "  " not in response

    # Verify structure
    parsed = json.loads(response)
    assert parsed["error"]["message"] == "Test error"
    assert len(parsed["error"]["suggestions"]) == 2


def test_response_size_with_default_limits():
    """Test that responses with default limits are reasonable size."""
    # Simulate 10 activities (default limit)
    activities = []
    for i in range(10):
        activities.append(
            {
                "activityId": i,
                "activityName": f"Test Activity {i}",
                "distance": 5000.0,
                "duration": 1800,
                "elevationGain": 100,
                "startTimeLocal": "2024-01-01T08:00:00",
            }
        )

    data = {"activities": activities, "count": 10}
    pagination = build_pagination_info(
        returned_count=10, limit=10, current_page=1, has_more=True, filters={}
    )

    response = ResponseBuilder.build_response(
        data=data,
        pagination=pagination,
        metadata={"query_type": "activity_list"},
    )

    # Check size (should be well under 100k characters for 10 activities)
    size = len(response)
    assert size < 100_000, f"Response size {size} exceeds 100k characters"

    # For 10 activities, should be much smaller
    assert size < 10_000, f"Response size {size} is larger than expected for 10 activities"
