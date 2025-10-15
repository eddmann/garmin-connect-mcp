"""Gear and equipment tools for Garmin Connect MCP server."""

from typing import Annotated

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..response_builder import ResponseBuilder

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


async def query_gear(
    include_defaults: Annotated[bool, "Include default gear settings"] = True,
    include_stats: Annotated[bool, "Include gear usage statistics"] = True,
) -> str:
    """
    Query gear and equipment.

    Get comprehensive gear information including defaults and usage stats.
    """
    try:
        client = _get_client()

        data = {}

        # Get all gear
        try:
            gear = client.safe_call("get_gear")
            data["gear"] = gear
        except Exception:
            data["gear"] = None

        # Gear defaults
        if include_defaults:
            try:
                defaults = client.safe_call("get_gear_defaults")
                data["defaults"] = defaults
            except Exception:
                data["defaults"] = None

        # Gear stats
        if include_stats:
            try:
                stats = client.safe_call("get_gear_stats")
                data["stats"] = stats
            except Exception:
                data["stats"] = None

        # Generate insights
        insights = []
        if isinstance(data.get("gear"), list):
            insights.append(f"Total gear items: {len(data['gear'])}")
        if data.get("defaults"):
            insights.append("Default gear configured")
        if data.get("stats"):
            insights.append("Usage statistics available")

        return ResponseBuilder.build_response(
            data=data,
            analysis={"insights": insights} if insights else None,
            metadata={"includes": {"defaults": include_defaults, "stats": include_stats}},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "garmin_api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")
