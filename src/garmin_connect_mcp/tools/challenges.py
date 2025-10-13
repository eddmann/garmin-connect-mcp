"""Challenge and goal tools for Garmin Connect MCP server."""

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


async def get_goals(
    goal_type: Annotated[str, "Goal type (e.g., 'active')"] = "active",
) -> str:
    """Get goals of a specific type."""
    try:
        client = _get_client()
        goals = client.safe_call("get_goals", goal_type)
        return format_summary(f"Goals ({goal_type})", goals)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_personal_record() -> str:
    """Get personal records."""
    try:
        client = _get_client()
        records = client.safe_call("get_personal_record")
        return format_summary("Personal Records", records)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_earned_badges() -> str:
    """Get earned badges."""
    try:
        client = _get_client()
        badges = client.safe_call("get_earned_badges")
        return format_summary("Earned Badges", badges)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_adhoc_challenges(
    start: Annotated[int, "Start index"] = 0,
    limit: Annotated[int, "Number of challenges to return"] = 100,
) -> str:
    """Get ad-hoc challenges."""
    try:
        client = _get_client()
        challenges = client.safe_call("get_adhoc_challenges", start, limit)
        return format_summary("Ad-hoc Challenges", challenges)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_available_badge_challenges(
    start: Annotated[int, "Start index"] = 1,
    limit: Annotated[int, "Number of challenges to return"] = 100,
) -> str:
    """Get available badge challenges."""
    try:
        client = _get_client()
        challenges = client.safe_call("get_available_badge_challenges", start, limit)
        return format_summary("Available Badge Challenges", challenges)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_badge_challenges(
    start: Annotated[int, "Start index"] = 1,
    limit: Annotated[int, "Number of challenges to return"] = 100,
) -> str:
    """Get all badge challenges."""
    try:
        client = _get_client()
        challenges = client.safe_call("get_badge_challenges", start, limit)
        return format_summary("Badge Challenges", challenges)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_non_completed_badge_challenges(
    start: Annotated[int, "Start index"] = 1,
    limit: Annotated[int, "Number of challenges to return"] = 100,
) -> str:
    """Get non-completed badge challenges."""
    try:
        client = _get_client()
        challenges = client.safe_call("get_non_completed_badge_challenges", start, limit)
        return format_summary("Non-Completed Badge Challenges", challenges)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_race_predictions() -> str:
    """Get race time predictions."""
    try:
        client = _get_client()
        predictions = client.safe_call("get_race_predictions")
        return format_summary("Race Predictions", predictions)
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_inprogress_virtual_challenges(
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"],
) -> str:
    """Get in-progress virtual challenges for a date range."""
    try:
        client = _get_client()
        challenges = client.safe_call("get_inprogress_virtual_challenges", start_date, end_date)
        return format_summary(
            f"In-Progress Virtual Challenges ({start_date} to {end_date})", challenges
        )
    except GarminAPIError as e:
        return f"Error: {e.message}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
