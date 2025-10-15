"""Tests for pagination utilities."""

import pytest

from garmin_connect_mcp.pagination import (
    PaginationCursor,
    build_pagination_info,
    decode_cursor,
    encode_cursor,
)


def test_encode_cursor_basic():
    """Test basic cursor encoding."""
    cursor = encode_cursor(page=1)
    assert isinstance(cursor, str)
    assert len(cursor) > 0


def test_encode_cursor_with_filters():
    """Test cursor encoding with filters."""
    filters = {"start_date": "2024-01-01", "activity_type": "running"}
    cursor = encode_cursor(page=2, filters=filters)
    assert isinstance(cursor, str)


def test_decode_cursor_basic():
    """Test basic cursor decoding."""
    cursor = encode_cursor(page=3)
    decoded = decode_cursor(cursor)
    assert decoded["page"] == 3
    assert decoded.get("filters") is None


def test_decode_cursor_with_filters():
    """Test cursor decoding with filters."""
    filters = {"start_date": "2024-01-01", "end_date": "2024-12-31"}
    cursor = encode_cursor(page=2, filters=filters)
    decoded = decode_cursor(cursor)
    assert decoded["page"] == 2
    assert decoded.get("filters") == filters


def test_decode_invalid_cursor():
    """Test decoding invalid cursor raises ValueError."""
    with pytest.raises(ValueError, match="Invalid pagination cursor"):
        decode_cursor("invalid-cursor-data")


def test_cursor_round_trip():
    """Test encoding and decoding round trip."""
    original: PaginationCursor = {
        "page": 5,
        "filters": {"start_date": "2024-01-01", "activity_type": "cycling"},
    }
    cursor = encode_cursor(original["page"], original.get("filters"))
    decoded = decode_cursor(cursor)
    assert decoded["page"] == original["page"]
    assert decoded.get("filters") == original.get("filters")


def test_build_pagination_info_no_more():
    """Test building pagination info when no more pages."""
    info = build_pagination_info(
        returned_count=10, limit=20, current_page=1, has_more=False, filters=None
    )
    assert info["cursor"] is None
    assert info["has_more"] is False
    assert info["limit"] == 20
    assert info["returned"] == 10


def test_build_pagination_info_has_more():
    """Test building pagination info when more pages available."""
    filters = {"start_date": "2024-01-01"}
    info = build_pagination_info(
        returned_count=20, limit=20, current_page=1, has_more=True, filters=filters
    )
    assert info["cursor"] is not None
    assert info["has_more"] is True
    assert info["limit"] == 20
    assert info["returned"] == 20

    # Verify cursor contains next page
    decoded = decode_cursor(info["cursor"])
    assert decoded["page"] == 2
    assert decoded.get("filters") == filters


def test_build_pagination_info_preserves_filters():
    """Test that pagination info preserves filters in cursor."""
    filters = {"start_date": "2024-01-01", "end_date": "2024-12-31", "activity_type": "running"}
    info = build_pagination_info(
        returned_count=20, limit=20, current_page=3, has_more=True, filters=filters
    )

    decoded = decode_cursor(info["cursor"])
    assert decoded["page"] == 4  # Next page
    assert decoded.get("filters") == filters
