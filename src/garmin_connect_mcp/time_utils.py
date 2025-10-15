"""Time and date utilities for Garmin Connect MCP."""

from datetime import datetime, timedelta
from typing import Literal

PeriodType = Literal["7d", "30d", "90d", "ytd", "this-week", "this-month", "this-year"]


def parse_time_range(period: str) -> tuple[datetime, datetime]:
    """
    Parse a time period string into start and end datetimes.

    Supports:
    - Relative periods: "7d", "30d", "90d", "ytd"
    - Named periods: "this-week", "this-month", "this-year"
    - Absolute ranges: "YYYY-MM-DD:YYYY-MM-DD"

    Args:
        period: Period string to parse

    Returns:
        Tuple of (start_date, end_date) as datetime objects

    Raises:
        ValueError: If period format is invalid
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Relative periods (days back from today)
    if period.endswith("d"):
        try:
            days = int(period[:-1])
            start_date = today - timedelta(days=days)
            end_date = today
            return start_date, end_date
        except ValueError as e:
            raise ValueError(f"Invalid relative period format: {period}") from e

    # Year-to-date
    if period == "ytd":
        start_date = datetime(today.year, 1, 1)
        end_date = today
        return start_date, end_date

    # This week (Monday to today)
    if period == "this-week":
        days_since_monday = today.weekday()
        start_date = today - timedelta(days=days_since_monday)
        end_date = today
        return start_date, end_date

    # This month
    if period == "this-month":
        start_date = datetime(today.year, today.month, 1)
        end_date = today
        return start_date, end_date

    # This year
    if period == "this-year":
        start_date = datetime(today.year, 1, 1)
        end_date = today
        return start_date, end_date

    # Absolute date range (YYYY-MM-DD:YYYY-MM-DD)
    if ":" in period:
        try:
            start_str, end_str = period.split(":", 1)
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")

            if start_date > end_date:
                raise ValueError("Start date must be before or equal to end date")

            return start_date, end_date
        except ValueError as e:
            raise ValueError(
                f"Invalid absolute date range format: {period}. Use YYYY-MM-DD:YYYY-MM-DD"
            ) from e

    raise ValueError(
        f"Invalid period format: {period}. "
        "Supported formats: '7d', '30d', '90d', 'ytd', 'this-week', 'this-month', 'this-year', or 'YYYY-MM-DD:YYYY-MM-DD'"
    )


def get_range_description(period: str) -> str:
    """
    Get a human-readable description of a time period.

    Args:
        period: Period string (same format as parse_time_range)

    Returns:
        Human-readable description of the period
    """
    try:
        start_date, end_date = parse_time_range(period)
        days = (end_date - start_date).days + 1

        # Check if it matches a named period
        if period.endswith("d"):
            return f"Last {period[:-1]} days"
        elif period == "ytd":
            return f"Year to date ({start_date.year})"
        elif period == "this-week":
            return "This week"
        elif period == "this-month":
            return f"{start_date.strftime('%B %Y')}"
        elif period == "this-year":
            return f"Year {start_date.year}"
        else:
            # Absolute range
            return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days} days)"

    except ValueError:
        return period


def format_date_for_api(dt: datetime) -> str:
    """
    Format a datetime object for Garmin Connect API calls.

    Args:
        dt: Datetime object to format

    Returns:
        Date string in YYYY-MM-DD format
    """
    return dt.strftime("%Y-%m-%d")


def get_week_ranges(start_date: datetime, end_date: datetime) -> list[tuple[datetime, datetime]]:
    """
    Split a date range into weekly ranges (Monday to Sunday).

    Args:
        start_date: Range start date
        end_date: Range end date

    Returns:
        List of (week_start, week_end) tuples
    """
    weeks = []
    current = start_date

    while current <= end_date:
        # Find Monday of current week
        days_since_monday = current.weekday()
        week_start = current - timedelta(days=days_since_monday)

        # Find Sunday of current week
        week_end = week_start + timedelta(days=6)

        # Clamp to actual range
        if week_start < start_date:
            week_start = start_date
        if week_end > end_date:
            week_end = end_date

        weeks.append((week_start, week_end))

        # Move to next week
        current = week_end + timedelta(days=1)

    return weeks


def get_today_date_string() -> str:
    """
    Get today's date as a string in YYYY-MM-DD format.

    Returns:
        Today's date string
    """
    return datetime.now().strftime("%Y-%m-%d")


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string in various formats to a datetime object.

    Supports:
    - "today"
    - "yesterday"
    - "YYYY-MM-DD"
    - ISO format strings

    Args:
        date_str: Date string to parse

    Returns:
        Datetime object

    Raises:
        ValueError: If date string format is invalid
    """
    date_str = date_str.strip().lower()

    if date_str == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    try:
        # Try YYYY-MM-DD format
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass

    try:
        # Try ISO format
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Use 'today', 'yesterday', or 'YYYY-MM-DD'"
        ) from e
