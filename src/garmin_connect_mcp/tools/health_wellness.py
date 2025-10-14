"""Health and wellness tools for Garmin Connect MCP server."""

from datetime import timedelta
from typing import Annotated

from ..auth import load_config, validate_credentials
from ..client import GarminAPIError, GarminClientWrapper, init_garmin_client
from ..response_builder import ResponseBuilder
from ..time_utils import parse_date_string

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


async def query_health_summary(
    date: Annotated[str | None, "Specific date ('today', 'yesterday', or YYYY-MM-DD)"] = None,
    start_date: Annotated[str | None, "Range start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD)"] = None,
    include_body_battery: Annotated[bool, "Include Body Battery data"] = True,
    include_training_readiness: Annotated[bool, "Include training readiness"] = True,
    include_training_status: Annotated[bool, "Include training status"] = True,
    unit: Annotated[str, "Unit system: 'metric' or 'imperial'"] = "metric",
) -> str:
    """
    Get comprehensive daily health snapshot.

    Includes stats, user summary, training readiness, training status,
    Body Battery, and Body Battery events.

    Supports single date or date range queries.
    """
    try:
        client = _get_client()

        # Determine date(s) to query
        if date:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False
        elif start_date and end_date:
            start = parse_date_string(start_date)
            end = parse_date_string(end_date)
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            is_range = True
        else:
            # Default to today
            date_str = parse_date_string("today").strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False

        # Collect data for each date
        summaries = []
        for date_str in dates:
            summary = {"date": date_str}

            # Get base stats
            try:
                stats = client.safe_call("get_stats", date_str)
                summary["stats"] = stats
            except Exception:
                summary["stats"] = None

            # Get user summary
            try:
                user_summary = client.safe_call("get_user_summary", date_str)
                summary["user_summary"] = user_summary
            except Exception:
                summary["user_summary"] = None

            # Training readiness
            if include_training_readiness:
                try:
                    readiness = client.safe_call("get_training_readiness", date_str)
                    summary["training_readiness"] = readiness
                except Exception:
                    summary["training_readiness"] = None

            # Training status
            if include_training_status:
                try:
                    status = client.safe_call("get_training_status", date_str)
                    summary["training_status"] = status
                except Exception:
                    summary["training_status"] = None

            # Body battery
            if include_body_battery:
                try:
                    # Body battery typically needs a range
                    bb = client.safe_call("get_body_battery", date_str, date_str)
                    summary["body_battery"] = bb
                except Exception:
                    summary["body_battery"] = None

                try:
                    bb_events = client.safe_call("get_body_battery_events", date_str)
                    summary["body_battery_events"] = bb_events
                except Exception:
                    summary["body_battery_events"] = None

            summaries.append(summary)

        # Build insights
        insights = []
        if len(summaries) == 1:
            s = summaries[0]
            if s.get("training_readiness"):
                insights.append("Training readiness data available")
            if s.get("body_battery"):
                insights.append("Body Battery tracking available")
        else:
            insights.append(f"Health summary for {len(summaries)} days")

        # Return appropriate structure
        if is_range:
            return ResponseBuilder.build_response(
                data={"summaries": summaries, "count": len(summaries)},
                analysis={"insights": insights} if insights else None,
                metadata={"start_date": dates[0], "end_date": dates[-1], "unit": unit},
            )
        else:
            return ResponseBuilder.build_response(
                data=summaries[0] if summaries else {},
                analysis={"insights": insights} if insights else None,
                metadata={"date": dates[0] if dates else None, "unit": unit},
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message, "garmin_api_error", ["Check your Garmin Connect credentials", "Verify your internet connection"]
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")


async def query_sleep_data(
    date: Annotated[str | None, "Specific date ('today', 'yesterday', or YYYY-MM-DD)"] = None,
    start_date: Annotated[str | None, "Range start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD)"] = None,
) -> str:
    """
    Get sleep data and analysis.

    Retrieves sleep duration, sleep stages (deep, light, REM), sleep scores,
    HRV, resting heart rate, and body battery impact.

    Supports single date or date range queries.
    """
    try:
        client = _get_client()

        # Determine date(s) to query
        if date:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False
        elif start_date and end_date:
            start = parse_date_string(start_date)
            end = parse_date_string(end_date)
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            is_range = True
        else:
            # Default to last night (yesterday's date)
            date_str = parse_date_string("yesterday").strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False

        # Collect sleep data
        sleep_data = []
        for date_str in dates:
            try:
                data = client.safe_call("get_sleep_data", date_str)
                sleep_data.append({"date": date_str, "sleep": data})
            except Exception:
                # Skip dates without sleep data
                pass

        if not sleep_data:
            return ResponseBuilder.build_response(
                data={"sleep_data": []},
                analysis={"insights": ["No sleep data found for the specified period"]},
                metadata={"dates": dates},
            )

        # Generate insights
        insights = []
        if len(sleep_data) == 1:
            data = sleep_data[0].get("sleep", {})
            dto = data.get("dailySleepDTO", {})
            total_hours = (dto.get("sleepTimeSeconds", 0)) / 3600
            sleep_score = dto.get("sleepScores", {}).get("overall", {}).get("value")

            if total_hours > 0:
                insights.append(f"Total sleep: {total_hours:.1f} hours")
            if sleep_score:
                insights.append(f"Sleep score: {sleep_score}/100")
        else:
            avg_sleep = 0
            count = 0
            for entry in sleep_data:
                dto = entry.get("sleep", {}).get("dailySleepDTO", {})
                total_hours = (dto.get("sleepTimeSeconds", 0)) / 3600
                if total_hours > 0:
                    avg_sleep += total_hours
                    count += 1

            if count > 0:
                insights.append(f"Average sleep: {avg_sleep / count:.1f} hours/night over {count} nights")

        # Return appropriate structure
        if is_range:
            return ResponseBuilder.build_response(
                data={"sleep_data": sleep_data, "count": len(sleep_data)},
                analysis={"insights": insights} if insights else None,
                metadata={"start_date": dates[0], "end_date": dates[-1]},
            )
        else:
            return ResponseBuilder.build_response(
                data=sleep_data[0] if sleep_data else {},
                analysis={"insights": insights} if insights else None,
                metadata={"date": dates[0] if dates else None},
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message, "garmin_api_error", ["Check your Garmin Connect credentials", "Verify your internet connection"]
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")


async def query_heart_rate_data(
    date: Annotated[str | None, "Specific date ('today', 'yesterday', or YYYY-MM-DD)"] = None,
    start_date: Annotated[str | None, "Range start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD)"] = None,
    include_resting: Annotated[bool, "Include resting heart rate"] = True,
) -> str:
    """
    Get heart rate data.

    Retrieves heart rate data including resting HR, average HR, min/max values.
    Supports single date or date range queries.
    """
    try:
        client = _get_client()

        # Determine date(s) to query
        if date:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False
        elif start_date and end_date:
            start = parse_date_string(start_date)
            end = parse_date_string(end_date)
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            is_range = True
        else:
            # Default to today
            date_str = parse_date_string("today").strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False

        # Collect heart rate data
        hr_data = []
        for date_str in dates:
            entry = {"date": date_str}

            # Get HR data
            try:
                hr = client.safe_call("get_heart_rates", date_str)
                entry["heart_rate"] = hr
            except Exception:
                entry["heart_rate"] = None

            # Get resting HR
            if include_resting:
                try:
                    rhr = client.safe_call("get_rhr_day", date_str)
                    entry["resting_hr"] = rhr
                except Exception:
                    entry["resting_hr"] = None

            hr_data.append(entry)

        # Generate insights
        insights = []
        if len(hr_data) == 1:
            entry = hr_data[0]
            rhr = entry.get("resting_hr")
            if rhr:
                insights.append("Resting heart rate data available")
        else:
            insights.append(f"Heart rate data for {len(hr_data)} days")

        # Return appropriate structure
        if is_range:
            return ResponseBuilder.build_response(
                data={"heart_rate_data": hr_data, "count": len(hr_data)},
                analysis={"insights": insights} if insights else None,
                metadata={"start_date": dates[0], "end_date": dates[-1]},
            )
        else:
            return ResponseBuilder.build_response(
                data=hr_data[0] if hr_data else {},
                analysis={"insights": insights} if insights else None,
                metadata={"date": dates[0] if dates else None},
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message, "garmin_api_error", ["Check your Garmin Connect credentials", "Verify your internet connection"]
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")


async def query_activity_metrics(
    date: Annotated[str | None, "Specific date ('today', 'yesterday', or YYYY-MM-DD)"] = None,
    start_date: Annotated[str | None, "Range start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "Range end date (YYYY-MM-DD)"] = None,
    metrics: Annotated[
        str, "Comma-separated metrics: steps,stress,respiration,spo2,floors,hydration,blood_pressure,body_composition"
    ] = "steps,stress",
    unit: Annotated[str, "Unit system: 'metric' or 'imperial'"] = "metric",
) -> str:
    """
    Get activity metrics (steps, stress, etc.).

    Includes steps, stress, respiration, SpO2, floors climbed, hydration,
    blood pressure, and body composition.

    Select specific metrics to retrieve using the metrics parameter.
    Default: steps and stress.
    """
    try:
        client = _get_client()

        # Parse requested metrics
        requested_metrics = [m.strip().lower() for m in metrics.split(",")]

        # Determine date(s) to query
        if date:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False
        elif start_date and end_date:
            start = parse_date_string(start_date)
            end = parse_date_string(end_date)
            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
            is_range = True
        else:
            # Default to today
            date_str = parse_date_string("today").strftime("%Y-%m-%d")
            dates = [date_str]
            is_range = False

        # Collect metrics data
        metrics_data = []
        for date_str in dates:
            entry = {"date": date_str}

            # Steps
            if "steps" in requested_metrics:
                try:
                    steps = client.safe_call("get_steps_data", date_str)
                    entry["steps"] = steps
                except Exception:
                    entry["steps"] = None

            # Stress
            if "stress" in requested_metrics:
                try:
                    stress = client.safe_call("get_stress_data", date_str)
                    entry["stress"] = stress
                except Exception:
                    entry["stress"] = None

            # Respiration
            if "respiration" in requested_metrics:
                try:
                    respiration = client.safe_call("get_respiration_data", date_str)
                    entry["respiration"] = respiration
                except Exception:
                    entry["respiration"] = None

            # SpO2
            if "spo2" in requested_metrics:
                try:
                    spo2 = client.safe_call("get_spo2_data", date_str)
                    entry["spo2"] = spo2
                except Exception:
                    entry["spo2"] = None

            # Floors
            if "floors" in requested_metrics:
                try:
                    floors = client.safe_call("get_floors", date_str)
                    entry["floors"] = floors
                except Exception:
                    entry["floors"] = None

            # Hydration
            if "hydration" in requested_metrics:
                try:
                    hydration = client.safe_call("get_hydration_data", date_str)
                    entry["hydration"] = hydration
                except Exception:
                    entry["hydration"] = None

            metrics_data.append(entry)

        # Handle range-based metrics
        if is_range and dates:
            # Blood pressure (range only)
            if "blood_pressure" in requested_metrics:
                try:
                    bp = client.safe_call("get_blood_pressure", dates[0], dates[-1])
                    # Add to first entry or create separate field
                    if metrics_data:
                        metrics_data[0]["blood_pressure"] = bp
                except Exception:
                    pass

            # Body composition (range only)
            if "body_composition" in requested_metrics:
                try:
                    bc = client.safe_call("get_body_composition", dates[0], dates[-1])
                    if metrics_data:
                        metrics_data[0]["body_composition"] = bc
                except Exception:
                    pass

        # Generate insights
        insights = []
        insights.append(f"Requested metrics: {', '.join(requested_metrics)}")
        if len(metrics_data) == 1:
            available = [k for k in metrics_data[0].keys() if k != "date" and metrics_data[0][k] is not None]
            if available:
                insights.append(f"Available metrics: {', '.join(available)}")
        else:
            insights.append(f"Metrics data for {len(metrics_data)} days")

        # Return appropriate structure
        if is_range:
            return ResponseBuilder.build_response(
                data={"metrics": metrics_data, "count": len(metrics_data)},
                analysis={"insights": insights} if insights else None,
                metadata={"start_date": dates[0], "end_date": dates[-1], "requested_metrics": requested_metrics, "unit": unit},
            )
        else:
            return ResponseBuilder.build_response(
                data=metrics_data[0] if metrics_data else {},
                analysis={"insights": insights} if insights else None,
                metadata={"date": dates[0] if dates else None, "requested_metrics": requested_metrics, "unit": unit},
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message, "garmin_api_error", ["Check your Garmin Connect credentials", "Verify your internet connection"]
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "unexpected_error")
