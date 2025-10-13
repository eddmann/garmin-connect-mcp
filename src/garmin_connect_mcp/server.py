"""Garmin Connect MCP Server - Main entry point."""

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Garmin Connect")

# Import and register all tools
from .tools.activities import (
    get_activities,
    get_activities_by_date,
    get_activities_fordate,
    get_activity,
    get_activity_exercise_sets,
    get_activity_gear,
    get_activity_hr_in_timezones,
    get_activity_split_summaries,
    get_activity_splits,
    get_activity_typed_splits,
    get_activity_weather,
    get_last_activity,
)
from .tools.challenges import (
    get_adhoc_challenges,
    get_available_badge_challenges,
    get_badge_challenges,
    get_earned_badges,
    get_goals,
    get_inprogress_virtual_challenges,
    get_non_completed_badge_challenges,
    get_personal_record,
    get_race_predictions,
)
from .tools.data_management import (
    add_body_composition,
    add_hydration_data,
    set_blood_pressure,
)
from .tools.devices import (
    get_device_alarms,
    get_device_last_used,
    get_device_settings,
    get_device_solar_data,
    get_devices,
    get_primary_training_device,
)
from .tools.gear import get_gear, get_gear_defaults, get_gear_stats
from .tools.health_wellness import (
    get_all_day_events,
    get_all_day_stress,
    get_blood_pressure,
    get_body_battery,
    get_body_battery_events,
    get_body_composition,
    get_daily_steps,
    get_floors,
    get_heart_rates,
    get_hydration_data,
    get_respiration_data,
    get_rhr_day,
    get_sleep_data,
    get_spo2_data,
    get_stats,
    get_stats_and_body,
    get_steps_data,
    get_stress_data,
    get_training_readiness,
    get_training_status,
    get_user_summary,
)
from .tools.training import (
    get_endurance_score,
    get_fitnessage_data,
    get_hill_score,
    get_hrv_data,
    get_max_metrics,
    get_progress_summary_between_dates,
    get_training_effect,
)
from .tools.user_profile import get_full_name
from .tools.weight import (
    add_weigh_in,
    delete_weigh_ins,
    get_daily_weigh_ins,
    get_weigh_ins,
)
from .tools.womens_health import (
    get_menstrual_calendar_data,
    get_menstrual_data_for_date,
    get_pregnancy_summary,
)
from .tools.workouts import (
    download_workout,
    get_workout_by_id,
    get_workouts,
    upload_workout,
)

# Register activity tools
mcp.tool()(get_activities)
mcp.tool()(get_activities_by_date)
mcp.tool()(get_activities_fordate)
mcp.tool()(get_activity)
mcp.tool()(get_activity_splits)
mcp.tool()(get_activity_typed_splits)
mcp.tool()(get_activity_split_summaries)
mcp.tool()(get_activity_weather)
mcp.tool()(get_activity_hr_in_timezones)
mcp.tool()(get_activity_gear)
mcp.tool()(get_activity_exercise_sets)
mcp.tool()(get_last_activity)

# Register health & wellness tools
mcp.tool()(get_stats)
mcp.tool()(get_user_summary)
mcp.tool()(get_body_composition)
mcp.tool()(get_stats_and_body)
mcp.tool()(get_steps_data)
mcp.tool()(get_daily_steps)
mcp.tool()(get_training_readiness)
mcp.tool()(get_body_battery)
mcp.tool()(get_body_battery_events)
mcp.tool()(get_blood_pressure)
mcp.tool()(get_floors)
mcp.tool()(get_training_status)
mcp.tool()(get_rhr_day)
mcp.tool()(get_heart_rates)
mcp.tool()(get_hydration_data)
mcp.tool()(get_sleep_data)
mcp.tool()(get_stress_data)
mcp.tool()(get_respiration_data)
mcp.tool()(get_spo2_data)
mcp.tool()(get_all_day_stress)
mcp.tool()(get_all_day_events)

# Register device tools
mcp.tool()(get_devices)
mcp.tool()(get_device_last_used)
mcp.tool()(get_device_settings)
mcp.tool()(get_primary_training_device)
mcp.tool()(get_device_solar_data)
mcp.tool()(get_device_alarms)

# Register user profile tools
mcp.tool()(get_full_name)

# Register gear tools
mcp.tool()(get_gear)
mcp.tool()(get_gear_defaults)
mcp.tool()(get_gear_stats)

# Register weight tools
mcp.tool()(get_weigh_ins)
mcp.tool()(get_daily_weigh_ins)
mcp.tool()(delete_weigh_ins)
mcp.tool()(add_weigh_in)

# Register challenge tools
mcp.tool()(get_goals)
mcp.tool()(get_personal_record)
mcp.tool()(get_earned_badges)
mcp.tool()(get_adhoc_challenges)
mcp.tool()(get_available_badge_challenges)
mcp.tool()(get_badge_challenges)
mcp.tool()(get_non_completed_badge_challenges)
mcp.tool()(get_race_predictions)
mcp.tool()(get_inprogress_virtual_challenges)

# Register training tools
mcp.tool()(get_progress_summary_between_dates)
mcp.tool()(get_hill_score)
mcp.tool()(get_endurance_score)
mcp.tool()(get_training_effect)
mcp.tool()(get_max_metrics)
mcp.tool()(get_hrv_data)
mcp.tool()(get_fitnessage_data)

# Register workout tools
mcp.tool()(get_workouts)
mcp.tool()(get_workout_by_id)
mcp.tool()(download_workout)
mcp.tool()(upload_workout)

# Register data management tools
mcp.tool()(add_body_composition)
mcp.tool()(set_blood_pressure)
mcp.tool()(add_hydration_data)

# Register women's health tools
mcp.tool()(get_pregnancy_summary)
mcp.tool()(get_menstrual_data_for_date)
mcp.tool()(get_menstrual_calendar_data)


def main():
    """Main entry point for the Garmin Connect MCP server."""
    # Run the server with stdio transport (default)
    mcp.run()


if __name__ == "__main__":
    main()
