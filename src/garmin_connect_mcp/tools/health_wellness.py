"""Health and wellness tools for Garmin Connect MCP server."""

from datetime import datetime, timedelta
from typing import Annotated

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..formatters import (
    format_heart_rate_summary,
    format_heart_rate_summary_range,
    format_sleep_summary,
    format_sleep_summary_range,
    format_steps_summary,
    format_steps_summary_range,
    format_stress_summary,
    format_stress_summary_range,
    format_summary,
)

# Global client instance
_garmin_wrapper: GarminClientWrapper | None = None


def _get_client() -> GarminClientWrapper:
    """Get or initialize the Garmin client."""
    global _garmin_wrapper

    if _garmin_wrapper is None:
        config = load_config()
        if not validate_credentials(config):
            raise GarminAPIError(
                "Garmin credentials not configured. "
                "Please set GARMIN_EMAIL and GARMIN_PASSWORD in .env file."
            )

        client = init_garmin_client(config)
        if client is None:
            raise GarminAPIError("Failed to initialize Garmin client")

        _garmin_wrapper = GarminClientWrapper(client)

    return _garmin_wrapper


async def get_stats(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get daily stats for a specific date."""
    try:
        client = _get_client()
        stats = client.safe_call("get_stats", date)
        return format_summary(f"Stats for {date}", stats)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_user_summary(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get user summary for a specific date."""
    try:
        client = _get_client()
        summary = client.safe_call("get_user_summary", date)
        return format_summary(f"User Summary for {date}", summary)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_body_composition(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str | None, "End date in YYYY-MM-DD format (optional)"] = None,
) -> str:
    """Get body composition data for a date range."""
    try:
        client = _get_client()
        data = client.safe_call("get_body_composition", start_date, end_date)
        return format_summary(
            f"Body Composition from {start_date} to {end_date or start_date}", data
        )
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_stats_and_body(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get combined stats and body composition for a specific date."""
    try:
        client = _get_client()
        data = client.safe_call("get_stats_and_body", date)
        return format_summary(f"Stats & Body Composition for {date}", data)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_steps_data(
    date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[
        str | None, "End date in YYYY-MM-DD format (optional, for date ranges)"
    ] = None,
    verbosity: Annotated[str, "Output verbosity: 'summary' (default) or 'full'"] = "summary",
) -> str:
    """
    Get detailed steps data for a specific date or date range.

    Returns a concise summary by default with total steps, goal completion,
    distance, and calories. Use verbosity='full' to get the complete data
    including step counts broken down by time periods.

    For date ranges, shows a table with daily steps and range summary.
    """
    try:
        client = _get_client()

        # Handle date range
        if end_date:
            # Use the built-in daily_steps API which supports ranges
            steps_data = client.safe_call("get_daily_steps", date, end_date)

            if verbosity == "full":
                # Return combined JSON for all dates
                return format_summary(f"Steps Data: {date} to {end_date}", steps_data)
            else:
                # Use range formatter
                summary = format_steps_summary_range(steps_data)
                return f"Steps Data: {date} to {end_date}\n{'=' * 60}\n\n{summary}"

        # Handle single date
        else:
            steps = client.safe_call("get_steps_data", date)

            if verbosity == "full":
                return format_summary(f"Steps Data for {date}", steps)
            else:
                # Use summary formatter by default
                summary = format_steps_summary(steps)
                return f"Steps Data for {date}\n{'=' * 40}\n\n{summary}"

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_daily_steps(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get daily steps for a date range."""
    try:
        client = _get_client()
        steps = client.safe_call("get_daily_steps", start_date, end_date)
        return format_summary(f"Daily Steps from {start_date} to {end_date}", steps)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_training_readiness(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get training readiness for a specific date."""
    try:
        client = _get_client()
        readiness = client.safe_call("get_training_readiness", date)
        return format_summary(f"Training Readiness for {date}", readiness)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_body_battery(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get Body Battery data for a date range."""
    try:
        client = _get_client()
        battery = client.safe_call("get_body_battery", start_date, end_date)
        return format_summary(f"Body Battery from {start_date} to {end_date}", battery)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_body_battery_events(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get Body Battery events for a specific date."""
    try:
        client = _get_client()
        events = client.safe_call("get_body_battery_events", date)
        return format_summary(f"Body Battery Events for {date}", events)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_blood_pressure(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get blood pressure data for a date range."""
    try:
        client = _get_client()
        bp = client.safe_call("get_blood_pressure", start_date, end_date)
        return format_summary(f"Blood Pressure from {start_date} to {end_date}", bp)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_floors(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get floors climbed data for a specific date."""
    try:
        client = _get_client()
        floors = client.safe_call("get_floors", date)
        return format_summary(f"Floors Climbed for {date}", floors)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_training_status(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get training status for a specific date."""
    try:
        client = _get_client()
        status = client.safe_call("get_training_status", date)
        return format_summary(f"Training Status for {date}", status)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_rhr_day(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get resting heart rate for a specific date."""
    try:
        client = _get_client()
        rhr = client.safe_call("get_rhr_day", date)
        return format_summary(f"Resting Heart Rate for {date}", rhr)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_heart_rates(
    date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[
        str | None, "End date in YYYY-MM-DD format (optional, for date ranges)"
    ] = None,
    verbosity: Annotated[str, "Output verbosity: 'summary' (default) or 'full'"] = "summary",
) -> str:
    """
    Get heart rate data for a specific date or date range.

    Returns a concise summary by default with average, min, and max heart rates.
    Use verbosity='full' to get the complete data including minute-by-minute readings.

    For date ranges, shows a table with daily heart rate stats and range summary.
    """
    try:
        client = _get_client()

        # Handle date range
        if end_date:
            # Parse dates and generate range
            start = datetime.strptime(date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            # Collect data for each date
            data_by_date = {}
            current = start
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                try:
                    hr_data = client.safe_call("get_heart_rates", date_str)
                    data_by_date[date_str] = hr_data
                except Exception:
                    # Skip dates with no data
                    pass
                current += timedelta(days=1)

            if verbosity == "full":
                # Return combined JSON for all dates
                return format_summary(f"Heart Rate Data: {date} to {end_date}", data_by_date)
            else:
                # Use range formatter
                summary = format_heart_rate_summary_range(data_by_date)
                return f"Heart Rate Data: {date} to {end_date}\n{'=' * 60}\n\n{summary}"

        # Handle single date
        else:
            hr = client.safe_call("get_heart_rates", date)

            if verbosity == "full":
                return format_summary(f"Heart Rate Data for {date}", hr)
            else:
                # Use summary formatter by default
                summary = format_heart_rate_summary(hr)
                return f"Heart Rate Data for {date}\n{'=' * 40}\n\n{summary}"

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_hydration_data(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get hydration data for a specific date."""
    try:
        client = _get_client()
        hydration = client.safe_call("get_hydration_data", date)
        return format_summary(f"Hydration Data for {date}", hydration)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_sleep_data(
    date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[
        str | None, "End date in YYYY-MM-DD format (optional, for date ranges)"
    ] = None,
    verbosity: Annotated[str, "Output verbosity: 'summary' (default) or 'full'"] = "summary",
) -> str:
    """
    Get sleep data for a specific date or date range.

    Returns a concise summary by default with key metrics like sleep duration,
    sleep stages, sleep score, and restless moments. Use verbosity='full' to
    get the complete data including detailed time-series arrays.

    For date ranges, shows a table with daily sleep stats and range averages.
    """
    try:
        client = _get_client()

        # Handle date range
        if end_date:
            # Parse dates and generate range
            start = datetime.strptime(date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            # Collect data for each date
            data_by_date = {}
            current = start
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                try:
                    sleep_data = client.safe_call("get_sleep_data", date_str)
                    data_by_date[date_str] = sleep_data
                except Exception:
                    # Skip dates with no data
                    pass
                current += timedelta(days=1)

            if verbosity == "full":
                # Return combined JSON for all dates
                return format_summary(f"Sleep Data: {date} to {end_date}", data_by_date)
            else:
                # Use range formatter
                summary = format_sleep_summary_range(data_by_date)
                return f"Sleep Data: {date} to {end_date}\n{'=' * 60}\n\n{summary}"

        # Handle single date
        else:
            sleep = client.safe_call("get_sleep_data", date)

            if verbosity == "full":
                return format_summary(f"Sleep Data for {date}", sleep)
            else:
                # Use summary formatter by default
                summary = format_sleep_summary(sleep)
                return f"Sleep Data for {date}\n{'=' * 40}\n\n{summary}"

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_stress_data(
    date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[
        str | None, "End date in YYYY-MM-DD format (optional, for date ranges)"
    ] = None,
    verbosity: Annotated[str, "Output verbosity: 'summary' (default) or 'full'"] = "summary",
) -> str:
    """
    Get stress data for a specific date or date range.

    Returns a concise summary by default with average/max stress levels.
    Use verbosity='full' to get the complete data including detailed
    time-series stress and body battery readings.

    For date ranges, shows a table with daily stress stats and range summary.
    """
    try:
        client = _get_client()

        # Handle date range
        if end_date:
            # Parse dates and generate range
            start = datetime.strptime(date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            # Collect data for each date
            data_by_date = {}
            current = start
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                try:
                    stress_data = client.safe_call("get_stress_data", date_str)
                    data_by_date[date_str] = stress_data
                except Exception:
                    # Skip dates with no data
                    pass
                current += timedelta(days=1)

            if verbosity == "full":
                # Return combined JSON for all dates
                return format_summary(f"Stress Data: {date} to {end_date}", data_by_date)
            else:
                # Use range formatter
                summary = format_stress_summary_range(data_by_date)
                return f"Stress Data: {date} to {end_date}\n{'=' * 60}\n\n{summary}"

        # Handle single date
        else:
            stress = client.safe_call("get_stress_data", date)

            if verbosity == "full":
                return format_summary(f"Stress Data for {date}", stress)
            else:
                # Use summary formatter by default
                summary = format_stress_summary(stress)
                return f"Stress Data for {date}\n{'=' * 40}\n\n{summary}"

    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_respiration_data(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get respiration data for a specific date."""
    try:
        client = _get_client()
        respiration = client.safe_call("get_respiration_data", date)
        return format_summary(f"Respiration Data for {date}", respiration)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_spo2_data(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get SpO2 (blood oxygen) data for a specific date."""
    try:
        client = _get_client()
        spo2 = client.safe_call("get_spo2_data", date)
        return format_summary(f"SpO2 Data for {date}", spo2)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_all_day_stress(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get all-day stress data for a specific date."""
    try:
        client = _get_client()
        stress = client.safe_call("get_all_day_stress", date)
        return format_summary(f"All-Day Stress for {date}", stress)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_all_day_events(date: Annotated[str, "Date in YYYY-MM-DD format"]) -> str:
    """Get all-day events for a specific date."""
    try:
        client = _get_client()
        events = client.safe_call("get_max_metrics", date)
        return format_summary(f"All-Day Events for {date}", events)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
