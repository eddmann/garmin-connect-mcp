"""Garmin Connect MCP Server - Main entry point."""

from textwrap import dedent

from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Garmin Connect")

# Import and register all tools
from .tools.activities import (
    get_activity_details,
    get_activity_social,
    query_activities,
)
from .tools.analysis import (
    compare_activities,
    find_similar_activities,
)
from .tools.challenges import (
    query_challenges,
    query_goals_and_records,
)
from .tools.data_management import log_health_data
from .tools.devices import query_devices
from .tools.gear import query_gear
from .tools.health_wellness import (
    query_activity_metrics,
    query_health_summary,
    query_heart_rate_data,
    query_sleep_data,
)
from .tools.training import (
    analyze_training_period,
    get_performance_metrics,
    get_training_effect,
)
from .tools.user_profile import get_user_profile
from .tools.weight import manage_weight_data, query_weight_data
from .tools.womens_health import query_womens_health
from .tools.workouts import manage_workouts

# Register activity tools
mcp.tool()(query_activities)
mcp.tool()(get_activity_details)
mcp.tool()(get_activity_social)

# Register analysis tools
mcp.tool()(compare_activities)
mcp.tool()(find_similar_activities)

# Register health & wellness tools
mcp.tool()(query_health_summary)
mcp.tool()(query_sleep_data)
mcp.tool()(query_heart_rate_data)
mcp.tool()(query_activity_metrics)

# Register device & gear tools
mcp.tool()(query_devices)
mcp.tool()(query_gear)

# Register user profile tools
mcp.tool()(get_user_profile)

# Register challenge tools
mcp.tool()(query_goals_and_records)
mcp.tool()(query_challenges)

# Register training tools
mcp.tool()(analyze_training_period)
mcp.tool()(get_performance_metrics)
mcp.tool()(get_training_effect)

# Register weight tools
mcp.tool()(query_weight_data)
mcp.tool()(manage_weight_data)

# Register workout tools
mcp.tool()(manage_workouts)

# Register data management tools
mcp.tool()(log_health_data)

# Register women's health tools
mcp.tool()(query_womens_health)


# ============================================================================
# MCP Resources - Provide ongoing context to the LLM
# ============================================================================


@mcp.resource("garmin://athlete/profile")
async def athlete_profile_resource() -> str:
    """Provide athlete profile with stats and zones for context-aware clients."""
    return await get_user_profile(
        include_stats=True,
        include_prs=True,
        include_devices=True,
    )


@mcp.resource("garmin://training/readiness")
async def training_readiness_resource() -> str:
    """Provide current training readiness, Body Battery, and recovery status."""
    return await query_health_summary(
        date="today",
        include_body_battery=True,
        include_training_readiness=True,
        include_training_status=True,
    )


@mcp.resource("garmin://health/today")
async def health_today_resource() -> str:
    """Provide today's health snapshot (steps, sleep, stress, HR)."""
    return await query_activity_metrics(
        date="today",
        metrics="steps,stress,heart_rate,body_battery",
    )


# ============================================================================
# MCP Prompts - Pre-built query templates for common tasks
# ============================================================================


@mcp.prompt()
async def analyze_recent_training(period: str = "30d") -> str:
    """Analyze Garmin training for a given period."""
    return dedent(
        f"""
        Analyze my Garmin training over the past {period}.

        Focus on:
        1. Total volume (distance, time, elevation)
        2. Training distribution by activity type
        3. Weekly trends and patterns
        4. Performance metrics (VO2 max, training load)
        5. Key insights and recommendations

        Use the analyze-training-period tool with period="{period}" to get comprehensive analysis,
        then present the findings in a clear, actionable format.
        """
    ).strip()


@mcp.prompt()
async def sleep_quality_report(period: str = "7d") -> str:
    """Analyze sleep quality over a period."""
    return dedent(
        f"""
        Analyze my sleep quality over the past {period}.

        Include:
        1. Average sleep duration and quality scores
        2. Sleep stage breakdown (deep, light, REM)
        3. Sleep consistency and patterns
        4. HRV and resting heart rate trends
        5. Recommendations for improvement

        Use query-sleep-data with a date range to get sleep data,
        then provide actionable insights.
        """
    ).strip()


@mcp.prompt()
async def training_readiness_check() -> str:
    """Check if I'm ready to train today."""
    return dedent(
        """
        Assess my current training readiness.

        Include:
        1. Today's Body Battery and recovery status
        2. Last night's sleep quality and HRV
        3. Recent training load and fatigue
        4. Stress levels and recovery time
        5. Recommendation: train hard, train easy, or rest

        Use query-health-summary for today, query-sleep-data for last night,
        and get-performance-metrics for recent training status.
        """
    ).strip()


@mcp.prompt()
async def activity_deep_dive(activity_id: int) -> str:
    """Provide comprehensive analysis of an activity."""
    return dedent(
        f"""
        Provide a comprehensive analysis of activity {activity_id}.

        Include:
        1. Basic metrics (distance, time, pace, elevation)
        2. Heart rate zones and training effect
        3. Lap-by-lap breakdown
        4. Weather conditions
        5. Gear used
        6. Comparison to similar activities
        7. Performance insights

        Use get-activity-details with activity_id={activity_id} for enriched data,
        then use find-similar-activities to compare with past performances.
        """
    ).strip()


@mcp.prompt()
async def compare_recent_runs() -> str:
    """Compare recent runs to identify trends."""
    return dedent(
        """
        Compare my most recent runs to identify trends and improvements.

        Steps:
        1. Use query-activities to get my last 5-10 runs (activity_type="running")
        2. Extract the activity IDs from the most recent runs
        3. Use compare-activities to do side-by-side comparison
        4. Highlight improvements in pace, heart rate efficiency, or consistency
        5. Provide actionable feedback

        Focus on progress and areas for improvement.
        """
    ).strip()


@mcp.prompt()
async def health_summary(period: str = "7d") -> str:
    """Provide comprehensive health overview."""
    return dedent(
        f"""
        Provide a comprehensive health overview for the past {period}.

        Include:
        1. Daily steps and activity levels
        2. Sleep quality and consistency
        3. Stress levels and recovery
        4. Heart rate and HRV trends
        5. Body Battery patterns
        6. Overall health insights and recommendations

        Use query-activity-metrics for steps/stress, query-sleep-data for sleep,
        query-heart-rate-data for HR/HRV, and synthesize into actionable insights.
        """
    ).strip()


def main():
    """Main entry point for the Garmin Connect MCP server."""
    # Run the server with stdio transport (default)
    mcp.run()


if __name__ == "__main__":
    main()
