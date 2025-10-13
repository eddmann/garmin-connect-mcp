"""Training and performance tools for Garmin Connect MCP server."""

from typing import Annotated

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..formatters import format_summary

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


async def get_progress_summary_between_dates(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
    metric: Annotated[str, "Metric to track"],
) -> str:
    """Get progress summary for a specific metric between dates."""
    try:
        client = _get_client()
        summary = client.safe_call(
            "get_progress_summary_between_dates", start_date, end_date, metric
        )
        return format_summary(
            f"Progress Summary for {metric} ({start_date} to {end_date})", summary
        )
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_hill_score(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get hill score for a date range."""
    try:
        client = _get_client()
        score = client.safe_call("get_hill_score", start_date, end_date)
        return format_summary(f"Hill Score ({start_date} to {end_date})", score)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_endurance_score(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get endurance score for a date range."""
    try:
        client = _get_client()
        score = client.safe_call("get_endurance_score", start_date, end_date)
        return format_summary(f"Endurance Score ({start_date} to {end_date})", score)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_training_effect(
    activity_id: Annotated[int, "Activity ID"],
) -> str:
    """Get training effect for a specific activity."""
    try:
        client = _get_client()
        effect = client.safe_call("get_training_effect", activity_id)
        return format_summary(f"Training Effect for Activity {activity_id}", effect)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_max_metrics(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get max metrics for a specific date."""
    try:
        client = _get_client()
        metrics = client.safe_call("get_max_metrics", date)
        return format_summary(f"Max Metrics for {date}", metrics)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_hrv_data(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get heart rate variability (HRV) data for a specific date."""
    try:
        client = _get_client()
        hrv = client.safe_call("get_hrv_data", date)
        return format_summary(f"HRV Data for {date}", hrv)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_fitnessage_data(
    date: Annotated[str, "Date in YYYY-MM-DD format"],
) -> str:
    """Get fitness age data for a specific date."""
    try:
        client = _get_client()
        fitness_age = client.safe_call("get_fitness_age", date)
        return format_summary(f"Fitness Age for {date}", fitness_age)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
