"""Gear and equipment tools for Garmin Connect MCP server."""

from typing import Annotated

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder


async def query_gear(
    include_defaults: Annotated[bool, "Include default gear settings"] = True,
    include_stats: Annotated[bool, "Include gear usage statistics"] = True,
    ctx: Context | None = None,
) -> str:
    """
    Query gear and equipment.

    Get comprehensive gear information including defaults and usage stats.
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

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
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
