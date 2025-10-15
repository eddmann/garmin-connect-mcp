"""Challenges, goals, and records tools for Garmin Connect MCP server."""

from typing import Annotated

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder


async def query_goals_and_records(
    include_goals: Annotated[bool, "Include activity goals"] = True,
    include_prs: Annotated[bool, "Include personal records"] = True,
    include_race_predictions: Annotated[bool, "Include race time predictions"] = True,
    ctx: Context | None = None,
) -> str:
    """
    Get goals, personal records, and race predictions.

    Returns your activity goals, personal best performances,
    and predicted race times based on recent training.
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        data = {}

        if include_goals:
            try:
                goals = client.safe_call("get_goals")
                data["goals"] = goals
            except Exception:
                data["goals"] = None

        if include_prs:
            try:
                prs = client.safe_call("get_personal_record")
                data["personal_records"] = prs
            except Exception:
                data["personal_records"] = None

        if include_race_predictions:
            try:
                predictions = client.safe_call("get_race_predictions")
                data["race_predictions"] = predictions
            except Exception:
                data["race_predictions"] = None

        # Generate insights
        insights = []
        available = [k for k, v in data.items() if v is not None]
        if available:
            insights.append(f"Available data: {', '.join(available)}")
        else:
            insights.append("No goals, PRs, or predictions data available")

        return ResponseBuilder.build_response(
            data=data,
            analysis={"insights": insights} if insights else None,
            metadata={
                "includes": {
                    "goals": include_goals,
                    "prs": include_prs,
                    "race_predictions": include_race_predictions,
                }
            },
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


async def query_challenges(
    status: Annotated[str, "Challenge status: 'active', 'available', 'earned', 'all'"] = "active",
    challenge_type: Annotated[str, "Challenge type: 'badge', 'adhoc', 'virtual', 'all'"] = "all",
    ctx: Context | None = None,
) -> str:
    """
    Query challenges and badges.

    Filters by status (active/available/earned) and type (badge/adhoc/virtual).
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        data = {}

        # Fetch based on type
        if challenge_type in ["badge", "all"]:
            # Badge challenges
            if status in ["available", "all"]:
                try:
                    available_badges = client.safe_call("get_available_badge_challenges")
                    data["available_badges"] = available_badges
                except Exception:
                    data["available_badges"] = None

            if status in ["active", "all"]:
                try:
                    non_completed = client.safe_call("get_non_completed_badge_challenges")
                    data["active_badges"] = non_completed
                except Exception:
                    data["active_badges"] = None

            if status in ["earned", "all"]:
                try:
                    earned = client.safe_call("get_earned_badges")
                    data["earned_badges"] = earned
                except Exception:
                    data["earned_badges"] = None

            # All badge challenges
            try:
                all_badges = client.safe_call("get_badge_challenges")
                data["all_badge_challenges"] = all_badges
            except Exception:
                data["all_badge_challenges"] = None

        if challenge_type in ["adhoc", "all"]:
            try:
                adhoc = client.safe_call("get_adhoc_challenges")
                data["adhoc_challenges"] = adhoc
            except Exception:
                data["adhoc_challenges"] = None

        if challenge_type in ["virtual", "all"]:
            if status in ["active", "all"]:
                try:
                    virtual = client.safe_call("get_inprogress_virtual_challenges")
                    data["active_virtual_challenges"] = virtual
                except Exception:
                    data["active_virtual_challenges"] = None

        # Generate insights
        insights = []
        available_data = [k for k, v in data.items() if v is not None]
        if available_data:
            insights.append(f"Retrieved: {', '.join(available_data)}")

            # Count insights
            if isinstance(data.get("earned_badges"), list):
                insights.append(f"Earned badges: {len(data['earned_badges'])}")
            if isinstance(data.get("active_badges"), list):
                insights.append(f"Active badge challenges: {len(data['active_badges'])}")
        else:
            insights.append("No challenge data available")

        return ResponseBuilder.build_response(
            data=data,
            analysis={"insights": insights} if insights else None,
            metadata={"status": status, "challenge_type": challenge_type},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
