"""User profile tools for Garmin Connect MCP server."""

from datetime import datetime

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


async def get_user_profile(
    include_stats: bool = True,
    include_prs: bool = True,
    include_devices: bool = True,
) -> str:
    """
    Get comprehensive user profile with optional stats, personal records, and devices.

    Args:
        include_stats: Include daily stats and user summary (default: True)
        include_prs: Include personal records (default: True)
        include_devices: Include device information (default: True)

    Returns:
        Structured JSON with profile data, analysis, and metadata
    """
    try:
        client = _get_client()

        # Get basic profile info
        full_name = client.safe_call("get_full_name")

        data = {
            "profile": {
                "full_name": full_name,
            }
        }

        # Add stats and user summary
        if include_stats:
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                stats = client.safe_call("get_stats", today)
                data["stats"] = stats
            except Exception:
                data["stats"] = None

            try:
                user_summary = client.safe_call("get_user_summary", today)
                data["user_summary"] = user_summary
            except Exception:
                data["user_summary"] = None

        # Add personal records
        if include_prs:
            try:
                prs = client.safe_call("get_personal_record")
                data["personal_records"] = prs
            except Exception:
                data["personal_records"] = None

        # Add device information
        if include_devices:
            try:
                devices = client.safe_call("get_devices")
                data["devices"] = devices

                # Add primary device
                try:
                    primary_device = client.safe_call("get_primary_training_device")
                    data["primary_device"] = primary_device
                except Exception:
                    data["primary_device"] = None

            except Exception:
                data["devices"] = None
                data["primary_device"] = None

        # Generate insights
        insights = []
        if full_name:
            insights.append(f"Profile for: {full_name}")

        if include_devices and data.get("devices"):
            device_count = len(data["devices"]) if isinstance(data["devices"], list) else 0
            if device_count > 0:
                insights.append(f"{device_count} device(s) registered")

        if include_prs and data.get("personal_records"):
            pr_count = (
                len(data["personal_records"]) if isinstance(data["personal_records"], list) else 0
            )
            if pr_count > 0:
                insights.append(f"{pr_count} personal record(s)")

        analysis = {"insights": insights} if insights else None

        metadata = {
            "include_stats": include_stats,
            "include_prs": include_prs,
            "include_devices": include_devices,
        }

        return ResponseBuilder.build_response(
            data=data,
            analysis=analysis,
            metadata=metadata,
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            message=e.message,
            error_type="GarminAPIError",
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(
            message=f"Unexpected error: {str(e)}",
            error_type="UnexpectedError",
        )
