"""Workout management tools for Garmin Connect MCP server."""

from typing import Annotated

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder


async def manage_workouts(
    action: Annotated[str, "Action: 'list', 'get', 'download', 'upload'"],
    workout_id: Annotated[int | None, "Workout ID (for get/download actions)"] = None,
    workout_data: Annotated[str | None, "Workout data (for upload action)"] = None,
    ctx: Context | None = None,
) -> str:
    """
    Manage structured workouts.

    Actions:
    - list: Get all workouts
    - get: Get specific workout by ID
    - download: Download workout file
    - upload: Upload a new workout
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        if action == "list":
            workouts = client.safe_call("get_workouts")
            return ResponseBuilder.build_response(
                data={
                    "workouts": workouts,
                    "count": len(workouts) if isinstance(workouts, list) else 0,
                },
                metadata={"action": "list"},
            )

        elif action == "get":
            if workout_id is None:
                return ResponseBuilder.build_error_response(
                    "Workout ID required for get action",
                    "invalid_parameters",
                    ["Provide workout_id parameter"],
                )

            workout = client.safe_call("get_workout", workout_id)
            return ResponseBuilder.build_response(
                data={"workout": workout},
                metadata={"action": "get", "workout_id": workout_id},
            )

        elif action == "download":
            if workout_id is None:
                return ResponseBuilder.build_error_response(
                    "Workout ID required for download action",
                    "invalid_parameters",
                    ["Provide workout_id parameter"],
                )

            download_info = client.safe_call("download_workout", workout_id)
            return ResponseBuilder.build_response(
                data={"download_info": download_info},
                metadata={"action": "download", "workout_id": workout_id},
            )

        elif action == "upload":
            if not workout_data:
                return ResponseBuilder.build_error_response(
                    "Workout data required for upload action",
                    "invalid_parameters",
                    ["Provide workout_data parameter"],
                )

            result = client.safe_call("upload_workout", workout_data)
            return ResponseBuilder.build_response(
                data={"result": result},
                analysis={"insights": ["Workout uploaded successfully"]},
                metadata={"action": "upload"},
            )

        else:
            return ResponseBuilder.build_error_response(
                f"Invalid action: {action}",
                "invalid_parameters",
                ["Valid actions: 'list', 'get', 'download', 'upload'"],
            )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(e.message, "api_error")
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
