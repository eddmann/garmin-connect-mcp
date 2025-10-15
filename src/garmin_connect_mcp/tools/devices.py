"""Device management tools for Garmin Connect MCP server."""

from typing import Annotated

from fastmcp import Context

from ..client import GarminAPIError
from ..response_builder import ResponseBuilder


async def query_devices(
    device_id: Annotated[int | None, "Specific device ID"] = None,
    include_last_used: Annotated[bool, "Include last used device info"] = True,
    include_primary: Annotated[bool, "Include primary training device"] = True,
    include_settings: Annotated[bool, "Include device settings"] = False,
    include_solar_data: Annotated[bool, "Include solar charging data"] = False,
    include_alarms: Annotated[bool, "Include device alarms"] = False,
    ctx: Context | None = None,
) -> str:
    """
    Query Garmin devices.

    Get comprehensive device information including last used device,
    primary training device, settings, solar data, and alarms.
    """
    assert ctx is not None
    try:
        client = ctx.get_state("client")

        data = {}

        # Get all devices
        try:
            devices = client.safe_call("get_devices")
            data["devices"] = devices
        except Exception:
            data["devices"] = None

        # Last used device
        if include_last_used:
            try:
                last_used = client.safe_call("get_device_last_used")
                data["last_used"] = last_used
            except Exception:
                data["last_used"] = None

        # Primary training device
        if include_primary:
            try:
                primary = client.safe_call("get_primary_training_device")
                data["primary_device"] = primary
            except Exception:
                data["primary_device"] = None

        # Device-specific details
        if device_id is not None:
            if include_settings:
                try:
                    settings = client.safe_call("get_device_settings", device_id)
                    data["device_settings"] = settings
                except Exception:
                    data["device_settings"] = None

            if include_solar_data:
                try:
                    solar = client.safe_call("get_device_solar_data", device_id)
                    data["solar_data"] = solar
                except Exception:
                    data["solar_data"] = None

            if include_alarms:
                try:
                    alarms = client.safe_call("get_device_alarms", device_id)
                    data["alarms"] = alarms
                except Exception:
                    data["alarms"] = None

        # Generate insights
        insights = []
        if isinstance(data.get("devices"), list):
            insights.append(f"Total devices: {len(data['devices'])}")
        if data.get("primary_device"):
            insights.append("Primary training device identified")
        if data.get("solar_data"):
            insights.append("Solar charging data available")

        return ResponseBuilder.build_response(
            data=data,
            analysis={"insights": insights} if insights else None,
            metadata={"device_id": device_id},
        )

    except GarminAPIError as e:
        return ResponseBuilder.build_error_response(
            e.message,
            "api_error",
            ["Check your Garmin Connect credentials", "Verify your internet connection"],
        )
    except Exception as e:
        return ResponseBuilder.build_error_response(str(e), "internal_error")
