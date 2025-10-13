"""Formatting utilities for Garmin Connect data."""

import json
from datetime import datetime

from .types import (
    HeartRateData,
    HeartRateListData,
    JSONSerializable,
    SleepData,
    StepsData,
    StepsListData,
    StepsRangeItem,
    StressData,
)


def format_json(data: JSONSerializable, indent: int = 2) -> str:
    """Format data as pretty-printed JSON."""
    if data is None:
        return "No data available"

    try:
        return json.dumps(data, indent=indent, default=str)
    except Exception as e:
        return f"Error formatting data: {str(e)}"


def format_date(date_str: str | datetime | None) -> str:
    """Format a date string or datetime object."""
    if date_str is None:
        return "N/A"

    if isinstance(date_str, str):
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return date_str

    if isinstance(date_str, datetime):
        return date_str.strftime("%Y-%m-%d")

    return str(date_str)


def format_datetime(date_str: str | datetime | None) -> str:
    """Format a datetime string or datetime object."""
    if date_str is None:
        return "N/A"

    if isinstance(date_str, str):
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return date_str

    if isinstance(date_str, datetime):
        return date_str.strftime("%Y-%m-%d %H:%M:%S")

    return str(date_str)


def format_distance(meters: float | int | None) -> str:
    """Format distance from meters to km."""
    if meters is None:
        return "N/A"

    km = meters / 1000
    return f"{km:.2f} km"


def format_duration(seconds: int | float | None) -> str:
    """Format duration in seconds to HH:MM:SS."""
    if seconds is None:
        return "N/A"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_elevation(meters: float | int | None) -> str:
    """Format elevation in meters."""
    if meters is None:
        return "N/A"

    return f"{meters:.0f} m"


def format_speed(mps: float | None) -> str:
    """Format speed from m/s to km/h."""
    if mps is None or mps == 0:
        return "N/A"

    kmh = mps * 3.6
    return f"{kmh:.2f} km/h"


def format_pace(mps: float | None) -> str:
    """Format pace from m/s to min/km."""
    if mps is None or mps == 0:
        return "N/A"

    # Convert m/s to min/km
    seconds_per_km = 1000 / mps
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)

    return f"{minutes}:{seconds:02d} /km"


def format_weight(grams: float | int | None) -> str:
    """Format weight from grams to kg."""
    if grams is None:
        return "N/A"

    kg = grams / 1000
    return f"{kg:.2f} kg"


def format_summary(title: str, data: JSONSerializable) -> str:
    """Format a data summary with title and content."""
    if data is None or (isinstance(data, (dict, list)) and not data):
        return f"{title}\n\nNo data available."

    output = [f"{title}\n"]
    output.append("=" * len(title))
    output.append("")
    output.append(format_json(data))

    return "\n".join(output)


def format_list_items(
    items: list[dict[str, JSONSerializable]], fields: list[str], max_items: int | None = None
) -> str:
    """Format a list of items with specified fields."""
    if not items:
        return "No items found."

    display_items = items[:max_items] if max_items else items
    output = []

    for i, item in enumerate(display_items, 1):
        output.append(f"{i}. {item.get('name', 'Unnamed')}")
        for field in fields:
            if field in item and item[field] is not None:
                value = item[field]
                # Apply formatting based on field name
                if "date" in field.lower():
                    value = format_date(value)
                elif "distance" in field.lower():
                    value = format_distance(value)
                elif "duration" in field.lower() or "time" in field.lower():
                    value = format_duration(value)
                elif "elevation" in field.lower():
                    value = format_elevation(value)

                output.append(f"   {field}: {value}")
        output.append("")

    if max_items and len(items) > max_items:
        output.append(f"... and {len(items) - max_items} more items")

    return "\n".join(output)


def format_sleep_summary(data: SleepData) -> str:
    """Format sleep data as a concise summary with key metrics."""
    if not data:
        return "No sleep data available"

    output = []

    # Extract daily sleep DTO
    dto = data.get("dailySleepDTO", {})

    if dto:
        # Convert timestamps to readable format
        sleep_start = dto.get("sleepStartTimestampLocal")
        sleep_end = dto.get("sleepEndTimestampLocal")

        # Handle both string timestamps and millisecond timestamps
        if isinstance(sleep_start, (int, float)):
            sleep_start = datetime.fromtimestamp(sleep_start / 1000).strftime("%Y-%m-%d %H:%M")
        if isinstance(sleep_end, (int, float)):
            sleep_end = datetime.fromtimestamp(sleep_end / 1000).strftime("%Y-%m-%d %H:%M")

        output.append(f"Sleep Period: {sleep_start} → {sleep_end}")

        # Sleep duration breakdown
        total_hours = (dto.get("sleepTimeSeconds") or 0) / 3600
        deep_hours = (dto.get("deepSleepSeconds") or 0) / 3600
        light_hours = (dto.get("lightSleepSeconds") or 0) / 3600
        rem_hours = (dto.get("remSleepSeconds") or 0) / 3600
        awake_mins = (dto.get("awakeSleepSeconds") or 0) / 60

        output.append(f"Total Sleep: {total_hours:.1f}h")
        output.append(
            f"  - Deep: {deep_hours:.1f}h ({deep_hours / total_hours * 100:.0f}%)"
            if total_hours > 0
            else "  - Deep: 0.0h"
        )
        output.append(
            f"  - Light: {light_hours:.1f}h ({light_hours / total_hours * 100:.0f}%)"
            if total_hours > 0
            else "  - Light: 0.0h"
        )
        output.append(
            f"  - REM: {rem_hours:.1f}h ({rem_hours / total_hours * 100:.0f}%)"
            if total_hours > 0
            else "  - REM: 0.0h"
        )
        output.append(f"  - Awake: {awake_mins:.0f}m")

        # Sleep quality metrics
        sleep_scores = dto.get("sleepScores", {})
        overall_score = sleep_scores.get("overall", {}).get("value")
        if overall_score:
            output.append(f"\nSleep Score: {overall_score}/100")

            # Individual score components if available
            quality = sleep_scores.get("quality", {}).get("value")
            duration = sleep_scores.get("duration", {}).get("value")
            recovery = sleep_scores.get("recovery", {}).get("value")

            if quality or duration or recovery:
                output.append("  Component Scores:")
                if quality:
                    output.append(f"    - Quality: {quality}")
                if duration:
                    output.append(f"    - Duration: {duration}")
                if recovery:
                    output.append(f"    - Recovery: {recovery}")

        # Additional metrics
        restless = data.get("restlessMomentsCount")
        if restless is not None:
            output.append(f"\nRestless Moments: {restless}")

        avg_hrv = data.get("avgOvernightHrv")
        if avg_hrv:
            output.append(f"Average HRV: {avg_hrv:.1f} ms")

        resting_hr = data.get("restingHeartRate")
        if resting_hr:
            output.append(f"Resting Heart Rate: {resting_hr} bpm")

        # Body battery change
        bb_change = data.get("bodyBatteryChange")
        if bb_change:
            output.append(f"Body Battery Change: {bb_change:+d}")

    # Add note about detailed data availability
    detailed_arrays = []
    sleep_movement = data.get("sleepMovement")
    if sleep_movement:
        detailed_arrays.append(f"movement ({len(sleep_movement)} points)")
    sleep_heart_rate = data.get("sleepHeartRate")
    if sleep_heart_rate:
        detailed_arrays.append(f"heart rate ({len(sleep_heart_rate)} points)")
    respiration_data = data.get("wellnessEpochRespirationDataDTOList")
    if respiration_data:
        detailed_arrays.append(f"respiration ({len(respiration_data)} points)")

    if detailed_arrays:
        output.append(f"\nDetailed data available: {', '.join(detailed_arrays)}")
        output.append("(Use verbosity='full' to see detailed time-series data)")

    return "\n".join(output)


def format_stress_summary(data: StressData) -> str:
    """Format stress data as a concise summary with key metrics."""
    if not data:
        return "No stress data available"

    output = []

    # Date and time range
    date = data.get("calendarDate")
    start_time = data.get("startTimestampLocal")
    end_time = data.get("endTimestampLocal")

    output.append(f"Date: {date}")
    output.append(f"Period: {start_time} → {end_time}")

    # Stress levels
    avg_stress = data.get("avgStressLevel")
    max_stress = data.get("maxStressLevel")

    if avg_stress is not None:
        output.append(f"\nAverage Stress: {avg_stress}")
        # Add stress level interpretation
        if avg_stress < 25:
            output.append("  (Low stress)")
        elif avg_stress < 50:
            output.append("  (Moderate stress)")
        elif avg_stress < 75:
            output.append("  (High stress)")
        else:
            output.append("  (Very high stress)")

    if max_stress is not None:
        output.append(f"Maximum Stress: {max_stress}")

    # Data point information
    stress_values = data.get("stressValuesArray", [])
    bb_values = data.get("bodyBatteryValuesArray", [])

    if stress_values:
        output.append(f"\nStress readings: {len(stress_values)} data points")
    if bb_values:
        output.append(f"Body Battery readings: {len(bb_values)} data points")

    if stress_values or bb_values:
        output.append("(Use verbosity='full' to see detailed time-series data)")

    return "\n".join(output)


def format_heart_rate_summary(data: HeartRateData | HeartRateListData) -> str:
    """Format heart rate data as a concise summary with key metrics."""
    if not data:
        return "No heart rate data available"

    output = []

    # Check if this is a list of HR values or a summary object
    if isinstance(data, list):
        if not data:
            return "No heart rate data available"

        # Extract HR values from the list
        hr_values = [
            float(item[1])
            for item in data
            if len(item) > 1 and item[1] is not None and isinstance(item[1], (int, float))
        ]

        if hr_values:
            min_hr = min(hr_values)
            max_hr = max(hr_values)
            avg_hr = sum(hr_values) / len(hr_values)

            output.append(f"Heart Rate Summary ({len(hr_values)} readings)")
            output.append(f"Average: {avg_hr:.0f} bpm")
            output.append(f"Minimum: {min_hr} bpm")
            output.append(f"Maximum: {max_hr} bpm")
            output.append(f"\nDetailed readings: {len(data)} data points")
            output.append("(Use verbosity='full' to see minute-by-minute data)")

    elif isinstance(data, dict):
        # Handle dictionary format
        resting_hr = data.get("restingHeartRate")
        max_hr = data.get("maxHeartRate")
        min_hr = data.get("minHeartRate")
        avg_hr = data.get("averageHeartRate")

        output.append("Heart Rate Summary")
        if resting_hr:
            output.append(f"Resting: {resting_hr} bpm")
        if avg_hr:
            output.append(f"Average: {avg_hr} bpm")
        if min_hr:
            output.append(f"Minimum: {min_hr} bpm")
        if max_hr:
            output.append(f"Maximum: {max_hr} bpm")

        # Check for detailed data arrays
        if "heartRateValues" in data:
            output.append(f"\nDetailed readings: {len(data['heartRateValues'])} data points")
            output.append("(Use verbosity='full' to see detailed time-series data)")

    return "\n".join(output)


def format_steps_summary(data: StepsData | StepsListData) -> str:
    """Format steps data as a concise summary with key metrics."""
    if not data:
        return "No steps data available"

    output = []

    # Handle list format (array of time periods)
    if isinstance(data, list):
        # Calculate totals from the list
        total_steps = sum(item.get("steps", 0) for item in data)

        output.append(f"Total Steps: {total_steps:,}")
        output.append(f"Time Periods: {len(data)} intervals")

        # Find active periods (steps > 0)
        active_periods = [item for item in data if item.get("steps", 0) > 0]
        if active_periods:
            max_period = max(active_periods, key=lambda x: x.get("steps", 0))
            output.append(
                f"Most Active Period: {max_period.get('steps')} steps at {max_period.get('startGMT', 'unknown time')}"
            )

        output.append("\n(Use verbosity='full' to see step counts by time period)")
        return "\n".join(output)

    # Handle dictionary format
    total_steps = data.get("totalSteps") or 0
    step_goal = data.get("dailyStepGoal") or 0

    output.append(f"Total Steps: {total_steps:,}")

    if step_goal:
        completion = (total_steps / step_goal * 100) if step_goal > 0 else 0
        output.append(f"Daily Goal: {step_goal:,} ({completion:.0f}% complete)")

        if total_steps >= step_goal:
            output.append("✓ Goal achieved!")

    # Distance and calories if available
    distance = data.get("totalDistanceMeters")
    if distance:
        output.append(f"Distance: {distance / 1000:.2f} km")

    calories = data.get("activeKilocalories")
    if calories:
        output.append(f"Active Calories: {calories:.0f} kcal")

    # Step breakdown by period if available
    steps_array = data.get("stepsArray", [])
    if steps_array:
        output.append(f"\nDetailed breakdown: {len(steps_array)} time periods")
        output.append("(Use verbosity='full' to see step counts by time period)")

    return "\n".join(output)


def format_sleep_summary_range(data_by_date: dict[str, SleepData]) -> str:
    """Format sleep data for multiple dates as a summary table."""
    if not data_by_date:
        return "No sleep data available"

    output = []

    # Table header
    output.append(
        f"{'Date':<12} {'Total':<7} {'Deep':<6} {'Light':<6} {'REM':<6} {'Awake':<7} {'Score':<6}"
    )
    output.append("-" * 60)

    # Stats for aggregation
    total_sleep_hours = []
    scores = []
    best_night = None
    best_score = 0

    # Process each date
    for date, data in sorted(data_by_date.items()):
        dto = data.get("dailySleepDTO", {})

        total_hours = (dto.get("sleepTimeSeconds") or 0) / 3600
        deep_hours = (dto.get("deepSleepSeconds") or 0) / 3600
        light_hours = (dto.get("lightSleepSeconds") or 0) / 3600
        rem_hours = (dto.get("remSleepSeconds") or 0) / 3600
        awake_mins = (dto.get("awakeSleepSeconds") or 0) / 60

        sleep_scores = dto.get("sleepScores", {})
        score = sleep_scores.get("overall", {}).get("value", 0)

        # Track for summary
        if total_hours > 0:
            total_sleep_hours.append(total_hours)
        if score:
            scores.append(score)
            if score > best_score:
                best_score = score
                best_night = date

        # Format row
        output.append(
            f"{date:<12} {total_hours:>5.1f}h {deep_hours:>4.1f}h {light_hours:>4.1f}h "
            f"{rem_hours:>4.1f}h {awake_mins:>5.0f}m {score:>4}/100"
            if score
            else f"{date:<12} {total_hours:>5.1f}h {deep_hours:>4.1f}h {light_hours:>4.1f}h "
            f"{rem_hours:>4.1f}h {awake_mins:>5.0f}m  {'N/A':>6}"
        )

    # Add range summary
    if total_sleep_hours or scores:
        output.append("")
        output.append("Range Summary:")

        if total_sleep_hours:
            avg_sleep = sum(total_sleep_hours) / len(total_sleep_hours)
            output.append(f"  Average Sleep: {avg_sleep:.1f}h/night")

        if scores:
            avg_score = sum(scores) / len(scores)
            output.append(f"  Average Score: {avg_score:.0f}/100")

        if best_night:
            output.append(f"  Best Night: {best_night} ({best_score} score)")

    return "\n".join(output)


def format_stress_summary_range(data_by_date: dict[str, StressData]) -> str:
    """Format stress data for multiple dates as a summary table."""
    if not data_by_date:
        return "No stress data available"

    output = []

    # Table header
    output.append(f"{'Date':<12} {'Avg Stress':<12} {'Max Stress':<12} {'Level':<20}")
    output.append("-" * 60)

    # Stats for aggregation
    avg_stresses = []
    max_stresses = []
    lowest_day = None
    lowest_avg = 999

    # Process each date
    for date, data in sorted(data_by_date.items()):
        avg_stress = data.get("avgStressLevel", 0)
        max_stress = data.get("maxStressLevel", 0)

        # Determine stress level
        if avg_stress < 25:
            level = "Low"
        elif avg_stress < 50:
            level = "Moderate"
        elif avg_stress < 75:
            level = "High"
        else:
            level = "Very High"

        # Track for summary
        if avg_stress > 0:
            avg_stresses.append(avg_stress)
            if avg_stress < lowest_avg:
                lowest_avg = avg_stress
                lowest_day = date
        if max_stress > 0:
            max_stresses.append(max_stress)

        # Format row
        cal_date = data.get("calendarDate", date)
        output.append(f"{cal_date:<12} {avg_stress:>10} {max_stress:>10} {level:<20}")

    # Add range summary
    if avg_stresses:
        output.append("")
        output.append("Range Summary:")

        avg = sum(avg_stresses) / len(avg_stresses)
        output.append(f"  Average Daily Stress: {avg:.0f}")

        if max_stresses:
            peak = max(max_stresses)
            output.append(f"  Peak Stress: {peak}")

        if lowest_day:
            output.append(f"  Lowest Stress Day: {lowest_day} ({lowest_avg})")

    return "\n".join(output)


def format_heart_rate_summary_range(data_by_date: dict[str, list | dict]) -> str:
    """Format heart rate data for multiple dates as a summary table."""
    if not data_by_date:
        return "No heart rate data available"

    output = []

    # Table header
    output.append(f"{'Date':<12} {'Resting':<9} {'Average':<9} {'Min':<6} {'Max':<6}")
    output.append("-" * 50)

    # Stats for aggregation
    resting_hrs = []
    avg_hrs = []

    # Process each date
    for date, data in sorted(data_by_date.items()):
        if isinstance(data, list):
            # Calculate from list of readings
            hr_values = [item[1] for item in data if len(item) > 1 and item[1] is not None]

            if hr_values:
                min_hr = min(hr_values)
                max_hr = max(hr_values)
                avg_hr = sum(hr_values) / len(hr_values)
                resting = "N/A"

                avg_hrs.append(avg_hr)
                output.append(f"{date:<12} {resting:<9} {avg_hr:>7.0f} {min_hr:>5} {max_hr:>5}")

        elif isinstance(data, dict):
            # Extract from dictionary
            resting_hr = data.get("restingHeartRate", 0)
            avg_hr = data.get("averageHeartRate", 0)
            min_hr = data.get("minHeartRate", 0)
            max_hr = data.get("maxHeartRate", 0)

            if resting_hr:
                resting_hrs.append(resting_hr)
            if avg_hr:
                avg_hrs.append(avg_hr)

            resting_str = str(resting_hr) if resting_hr else "N/A"
            avg_str = str(int(avg_hr)) if avg_hr else "N/A"
            min_str = str(min_hr) if min_hr else "N/A"
            max_str = str(max_hr) if max_hr else "N/A"

            output.append(f"{date:<12} {resting_str:<9} {avg_str:>7} {min_str:>5} {max_str:>5}")

    # Add range summary
    if resting_hrs or avg_hrs:
        output.append("")
        output.append("Range Summary:")

        if resting_hrs:
            avg_resting = sum(resting_hrs) / len(resting_hrs)
            output.append(f"  Average Resting HR: {avg_resting:.0f} bpm")

        if avg_hrs:
            overall_avg = sum(avg_hrs) / len(avg_hrs)
            output.append(f"  Overall Average HR: {overall_avg:.0f} bpm")

    return "\n".join(output)


def format_steps_summary_range(data_by_date: list[StepsRangeItem]) -> str:
    """Format steps data for multiple dates as a summary table."""
    if not data_by_date:
        return "No steps data available"

    output = []

    # Table header
    output.append(f"{'Date':<12} {'Steps':<10} {'Goal':<10} {'Progress':<12} {'Distance':<10}")
    output.append("-" * 60)

    # Stats for aggregation
    total_steps_sum = 0
    days_with_goal = 0
    days_met_goal = 0
    best_day = None
    best_steps = 0

    # Process each date entry
    for entry in data_by_date:
        date = entry.get("calendarDate", "Unknown")
        total_steps = entry.get("totalSteps") or 0
        step_goal = entry.get("stepGoal") or 0
        distance = entry.get("totalDistance") or 0

        # Track for summary
        total_steps_sum += total_steps
        if step_goal:
            days_with_goal += 1
            if total_steps >= step_goal:
                days_met_goal += 1

        if total_steps > best_steps:
            best_steps = total_steps
            best_day = date

        # Calculate progress
        if step_goal:
            progress = total_steps / step_goal * 100
            progress_str = f"{progress:.0f}%"
            if total_steps >= step_goal:
                progress_str += " ✓"
        else:
            progress_str = "N/A"

        # Format distance
        distance_km = distance / 1000 if distance else 0
        distance_str = f"{distance_km:.1f} km" if distance else "N/A"

        # Format row
        output.append(
            f"{date:<12} {total_steps:>8,} {step_goal:>8,} {progress_str:<12} {distance_str:<10}"
        )

    # Add range summary
    if data_by_date:
        output.append("")
        output.append("Range Summary:")

        num_days = len(data_by_date)
        avg_steps = total_steps_sum / num_days if num_days else 0
        output.append(f"  Total Steps: {total_steps_sum:,}")
        output.append(f"  Average Steps/Day: {avg_steps:,.0f}")

        if days_with_goal:
            goal_rate = days_met_goal / days_with_goal * 100
            output.append(
                f"  Goal Achievement: {days_met_goal}/{days_with_goal} days ({goal_rate:.0f}%)"
            )

        if best_day:
            output.append(f"  Best Day: {best_day} ({best_steps:,} steps)")

    return "\n".join(output)
