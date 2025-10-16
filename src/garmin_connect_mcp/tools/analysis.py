"""Activity analysis tools for Garmin Connect MCP server."""

from typing import Annotated, Any

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder
from ..types import UnitSystem


async def compare_activities(
    activity_ids: Annotated[str, "Comma-separated activity IDs (2-5 activities)"],
    unit: Annotated[UnitSystem, "Unit system: 'metric' or 'imperial'"] = "metric",
    ctx: Context | None = None,
) -> str:
    """
    Compare multiple activities side-by-side.

    Analyzes 2-5 activities and provides:
    - Side-by-side metrics comparison
    - Identification of best/worst performances
    - Performance insights and patterns

    Example: activity_ids="12345678,12345679,12345680"
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        # Parse activity IDs
        ids = [int(id_str.strip()) for id_str in activity_ids.split(",")]

        if len(ids) < 2:
            return ResponseBuilder.build_error_response(
                "Must provide at least 2 activities to compare",
                "invalid_parameters",
                ["Provide 2-5 activity IDs separated by commas", "Example: '12345678,12345679'"],
            )

        if len(ids) > 5:
            return ResponseBuilder.build_error_response(
                "Cannot compare more than 5 activities at once",
                "invalid_parameters",
                [
                    "Please limit comparison to 5 activities",
                    "Split into multiple comparisons if needed",
                ],
            )

        # Fetch all activities
        activities = []
        for activity_id in ids:
            try:
                activity = client.safe_call("get_activity", activity_id)
                if activity:
                    formatted_activity = ResponseBuilder.format_activity(activity, unit)
                    activities.append(formatted_activity)
            except Exception:
                # Skip activities that can't be fetched
                pass

        if len(activities) < 2:
            return ResponseBuilder.build_error_response(
                f"Could only fetch {len(activities)} of {len(ids)} activities",
                "insufficient_data",
                [
                    "Check that activity IDs are correct",
                    "Ensure activities exist and are accessible",
                ],
            )

        # Build comparison data
        comparison: dict[str, Any] = {}

        # Distance comparison
        distances = []
        for act in activities:
            if isinstance(act.get("distance"), dict):
                distances.append(
                    (act["activityId"], act["distance"]["meters"], act["distance"]["formatted"])
                )
            elif act.get("distance"):
                dist = act["distance"]
                distances.append(
                    (act["activityId"], dist, ResponseBuilder._format_distance(dist, unit))
                )

        if distances:
            distances.sort(key=lambda x: x[1], reverse=True)
            comparison["distance"] = {
                "longest": {
                    "id": distances[0][0],
                    "meters": distances[0][1],
                    "formatted": distances[0][2],
                },
                "shortest": {
                    "id": distances[-1][0],
                    "meters": distances[-1][1],
                    "formatted": distances[-1][2],
                },
            }

        # Time comparison
        times = []
        for act in activities:
            if isinstance(act.get("duration"), dict):
                times.append(
                    (act["activityId"], act["duration"]["seconds"], act["duration"]["formatted"])
                )
            elif act.get("duration"):
                dur = act["duration"]
                times.append((act["activityId"], dur, ResponseBuilder._format_duration(dur)))

        if times:
            times.sort(key=lambda x: x[1])
            comparison["time"] = {
                "fastest": {"id": times[0][0], "seconds": times[0][1], "formatted": times[0][2]},
                "slowest": {"id": times[-1][0], "seconds": times[-1][1], "formatted": times[-1][2]},
            }

        # Pace comparison (for activities with distance and time)
        paces = []
        for act in activities:
            dist = (
                act.get("distance", {}).get("meters")
                if isinstance(act.get("distance"), dict)
                else act.get("distance")
            )
            dur = (
                act.get("duration", {}).get("seconds")
                if isinstance(act.get("duration"), dict)
                else act.get("duration")
            )

            if dist and dur and dist > 0 and dur > 0:
                mps = dist / dur
                paces.append((act["activityId"], mps, ResponseBuilder._format_pace(mps, unit)))

        if paces:
            paces.sort(key=lambda x: x[1], reverse=True)  # Higher m/s = faster pace
            comparison["pace"] = {
                "fastest": {"id": paces[0][0], "mps": paces[0][1], "formatted": paces[0][2]},
                "slowest": {"id": paces[-1][0], "mps": paces[-1][1], "formatted": paces[-1][2]},
            }

        # Elevation comparison
        elevations = []
        for act in activities:
            if isinstance(act.get("elevationGain"), dict):
                elevations.append(
                    (
                        act["activityId"],
                        act["elevationGain"]["meters"],
                        act["elevationGain"]["formatted"],
                    )
                )
            elif act.get("elevationGain"):
                elev = act["elevationGain"]
                elevations.append(
                    (act["activityId"], elev, ResponseBuilder._format_elevation(elev, unit))
                )

        if elevations:
            elevations.sort(key=lambda x: x[1], reverse=True)
            comparison["elevation"] = {
                "most": {
                    "id": elevations[0][0],
                    "meters": elevations[0][1],
                    "formatted": elevations[0][2],
                },
                "least": {
                    "id": elevations[-1][0],
                    "meters": elevations[-1][1],
                    "formatted": elevations[-1][2],
                },
            }

        # Heart rate comparison (if available)
        hrs = []
        for act in activities:
            avg_hr = act.get("averageHR")
            if avg_hr:
                hrs.append((act["activityId"], avg_hr, f"{avg_hr} bpm"))

        if hrs:
            hrs.sort(key=lambda x: x[1], reverse=True)
            comparison["heart_rate"] = {
                "highest_avg": {"id": hrs[0][0], "bpm": hrs[0][1], "formatted": hrs[0][2]},
                "lowest_avg": {"id": hrs[-1][0], "bpm": hrs[-1][1], "formatted": hrs[-1][2]},
            }

        # Generate insights
        insights = []

        # Activity type consistency
        activity_types = set(
            act.get("activityType", {}).get("typeKey", "unknown")
            if isinstance(act.get("activityType"), dict)
            else "unknown"
            for act in activities
        )
        if len(activity_types) == 1:
            insights.append(f"All activities are {list(activity_types)[0]} type")
        else:
            insights.append(
                f"Activities span {len(activity_types)} different types: {', '.join(activity_types)}"
            )

        # Performance variation
        if paces and len(paces) >= 2:
            fastest_mps = paces[0][1]
            slowest_mps = paces[-1][1]
            if fastest_mps > 0:
                diff_percent = ((fastest_mps - slowest_mps) / slowest_mps) * 100
                if diff_percent > 25:
                    insights.append(
                        f"Large pace variation: fastest is {diff_percent:.0f}% faster than slowest"
                    )
                elif diff_percent > 10:
                    insights.append(
                        f"Moderate pace variation: fastest is {diff_percent:.0f}% faster than slowest"
                    )
                else:
                    insights.append(
                        f"Consistent pace: only {diff_percent:.0f}% difference between fastest and slowest"
                    )

        # Distance consistency
        if distances and len(distances) >= 2:
            longest = distances[0][1]
            shortest = distances[-1][1]
            if longest > 0:
                dist_diff_percent = ((longest - shortest) / shortest) * 100
                if dist_diff_percent < 10:
                    insights.append("Similar distance across all activities")

        return ResponseBuilder.build_response(
            data={"activities": activities, "comparison": comparison, "count": len(activities)},
            analysis={"insights": insights},
            metadata={"activity_ids": ids, "unit": unit},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")


async def find_similar_activities(
    activity_id: Annotated[int, "Reference activity ID"],
    criteria: Annotated[
        str, "Similarity criteria: 'type', 'distance', 'elevation', 'duration' (comma-separated)"
    ] = "type,distance",
    limit: Annotated[
        str | int, "Maximum number of similar activities to return (1-20, default 10)"
    ] = 10,
    unit: Annotated[UnitSystem, "Unit system: 'metric' or 'imperial'"] = "metric",
    ctx: Context | None = None,
) -> str:
    """
    Find activities similar to a reference activity.

    Finds activities matching specified criteria:
    - type: Same activity type (running, cycling, etc.)
    - distance: Similar distance (±20%)
    - elevation: Similar elevation gain (±30%)
    - duration: Similar duration (±20%)

    Returns similarity scores and comparisons.

    Example: criteria="type,distance"
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        # Coerce limit to int if passed as string
        if isinstance(limit, str):
            try:
                limit = int(limit)
            except ValueError:
                return ResponseBuilder.build_error_response(
                    f"Invalid limit value: '{limit}'. Must be a number between 1 and 20.",
                    error_type="validation_error",
                )

        # Validate limit range
        if limit < 1 or limit > 20:
            return ResponseBuilder.build_error_response(
                f"Invalid limit: {limit}. Must be between 1 and 20.",
                error_type="validation_error",
            )

        # Parse criteria
        criteria_list = [c.strip().lower() for c in criteria.split(",")]
        valid_criteria = {"type", "distance", "elevation", "duration"}
        criteria_list = [c for c in criteria_list if c in valid_criteria]

        if not criteria_list:
            return ResponseBuilder.build_error_response(
                "No valid criteria specified",
                "invalid_parameters",
                ["Valid criteria: type, distance, elevation, duration", "Example: 'type,distance'"],
            )

        # Fetch reference activity
        ref_activity = client.safe_call("get_activity", activity_id)
        if not ref_activity:
            return ResponseBuilder.build_error_response(
                f"Reference activity {activity_id} not found",
                "not_found",
                [
                    "Check that the activity ID is correct",
                    "Ensure the activity exists and is accessible",
                ],
            )

        # Extract reference metrics
        ref_type = ref_activity.get("activityType", {}).get("typeKey")
        ref_distance = ref_activity.get("distance", 0) or 0
        ref_elevation = ref_activity.get("elevationGain", 0) or 0
        ref_duration = ref_activity.get("duration", 0) or 0

        # Fetch recent activities to search through
        # We'll fetch the last 100 activities as candidates
        candidate_activities = client.safe_call("get_activities", 0, 100, "")

        if not candidate_activities:
            return ResponseBuilder.build_response(
                data={
                    "reference_activity": ResponseBuilder.format_activity(ref_activity, unit),
                    "similar_activities": [],
                },
                analysis={"insights": ["No activities available to compare"]},
                metadata={"reference_activity_id": activity_id, "criteria": criteria_list},
            )

        # Filter and score activities
        similar = []
        for act in candidate_activities:
            # Skip the reference activity itself
            if act.get("activityId") == activity_id:
                continue

            match_score = 0
            max_score = len(criteria_list)
            differences: dict[str, Any] = {}

            # Check type
            if "type" in criteria_list:
                act_type = act.get("activityType", {}).get("typeKey")
                if act_type == ref_type:
                    match_score += 1
                    differences["type"] = {"match": True}
                else:
                    differences["type"] = {
                        "match": False,
                        "reference": ref_type,
                        "activity": act_type,
                    }

            # Check distance (±20%)
            if "distance" in criteria_list and ref_distance > 0:
                act_distance = act.get("distance", 0) or 0
                distance_diff = abs(act_distance - ref_distance)
                distance_diff_percent = (distance_diff / ref_distance) * 100

                if distance_diff_percent <= 20:
                    match_score += 1 - (distance_diff_percent / 20) * 0.5  # Partial credit
                    differences["distance"] = {
                        "diff_meters": distance_diff,
                        "diff_percent": round(distance_diff_percent, 1),
                        "within_tolerance": True,
                    }
                else:
                    differences["distance"] = {
                        "diff_meters": distance_diff,
                        "diff_percent": round(distance_diff_percent, 1),
                        "within_tolerance": False,
                    }

            # Check elevation (±30%)
            if "elevation" in criteria_list and ref_elevation > 0:
                act_elevation = act.get("elevationGain", 0) or 0
                elevation_diff = abs(act_elevation - ref_elevation)
                elevation_diff_percent = (elevation_diff / ref_elevation) * 100

                if elevation_diff_percent <= 30:
                    match_score += 1 - (elevation_diff_percent / 30) * 0.5
                    differences["elevation"] = {
                        "diff_meters": elevation_diff,
                        "diff_percent": round(elevation_diff_percent, 1),
                        "within_tolerance": True,
                    }
                else:
                    differences["elevation"] = {
                        "diff_meters": elevation_diff,
                        "diff_percent": round(elevation_diff_percent, 1),
                        "within_tolerance": False,
                    }

            # Check duration (±20%)
            if "duration" in criteria_list and ref_duration > 0:
                act_duration = act.get("duration", 0) or 0
                duration_diff = abs(act_duration - ref_duration)
                duration_diff_percent = (duration_diff / ref_duration) * 100

                if duration_diff_percent <= 20:
                    match_score += 1 - (duration_diff_percent / 20) * 0.5
                    differences["duration"] = {
                        "diff_seconds": duration_diff,
                        "diff_percent": round(duration_diff_percent, 1),
                        "within_tolerance": True,
                    }
                else:
                    differences["duration"] = {
                        "diff_seconds": duration_diff,
                        "diff_percent": round(duration_diff_percent, 1),
                        "within_tolerance": False,
                    }

            # Calculate similarity score (0-1)
            similarity_score = match_score / max_score if max_score > 0 else 0

            # Only include if similarity > 0.3
            if similarity_score > 0.3:
                similar.append(
                    {
                        "activity": ResponseBuilder.format_activity(act, unit),
                        "similarity_score": round(similarity_score, 2),
                        "differences": differences,
                    }
                )

        # Sort by similarity score (descending) and limit
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        similar = similar[:limit]

        # Generate insights
        insights = []
        if similar:
            insights.append(f"Found {len(similar)} similar activities")
            avg_similarity = sum(s["similarity_score"] for s in similar) / len(similar)
            insights.append(f"Average similarity score: {avg_similarity:.2f}")

            if similar[0]["similarity_score"] > 0.9:
                insights.append("Very high similarity with top matches")
            elif similar[0]["similarity_score"] > 0.7:
                insights.append("Good similarity with top matches")
        else:
            insights.append("No similar activities found matching the criteria")

        return ResponseBuilder.build_response(
            data={
                "reference_activity": ResponseBuilder.format_activity(ref_activity, unit),
                "similar_activities": similar,
                "count": len(similar),
            },
            analysis={"insights": insights},
            metadata={
                "reference_activity_id": activity_id,
                "criteria": criteria_list,
                "limit": limit,
                "unit": unit,
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
