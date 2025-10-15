"""Pagination utilities for Garmin Connect MCP server."""

import base64
import json
from typing import Any, Required, TypedDict


class PaginationCursor(TypedDict, total=False):
    """Cursor data structure."""

    page: Required[int]
    filters: dict[str, Any]


class PaginationInfo(TypedDict):
    """Pagination metadata."""

    cursor: str | None
    has_more: bool
    limit: int
    returned: int


def encode_cursor(page: int, filters: dict[str, Any] | None = None) -> str:
    """Encode pagination cursor to opaque string.

    Args:
        page: Page number (1-indexed)
        filters: Optional query filters to preserve in cursor

    Returns:
        Base64-encoded cursor string
    """
    data: PaginationCursor = {"page": page}
    if filters:
        data["filters"] = filters

    json_str = json.dumps(data, sort_keys=True)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> PaginationCursor:
    """Decode pagination cursor from opaque string.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Decoded cursor data

    Raises:
        ValueError: If cursor is invalid
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid pagination cursor: {e}") from e


def build_pagination_info(
    *,
    returned_count: int,
    limit: int,
    current_page: int,
    has_more: bool,
    filters: dict[str, Any] | None = None,
) -> PaginationInfo:
    """Build pagination metadata for response.

    Args:
        returned_count: Number of items in current response
        limit: Maximum items per page
        current_page: Current page number (1-indexed)
        has_more: Whether more pages are available
        filters: Query filters to encode in next cursor

    Returns:
        Pagination metadata dict
    """
    next_cursor = None
    if has_more:
        next_cursor = encode_cursor(current_page + 1, filters)

    return {
        "cursor": next_cursor,
        "has_more": has_more,
        "limit": limit,
        "returned": returned_count,
    }
