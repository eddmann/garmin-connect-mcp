"""Configuration settings for Garmin Connect MCP tools."""

from pydantic_settings import BaseSettings


class ToolConfig(BaseSettings):
    """Configuration for tool behavior and preferences."""

    # Caching settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour default

    # Query limits
    default_activity_limit: int = 20
    max_activity_limit: int = 100

    # Unit preferences
    distance_unit: str = "km"  # "km" or "miles"
    elevation_unit: str = "m"  # "m" or "ft"
    temperature_unit: str = "C"  # "C" or "F"
    weight_unit: str = "kg"  # "kg" or "lbs"

    # Output preferences
    verbose_errors: bool = True
    include_debug_info: bool = False

    class Config:
        """Pydantic config."""

        env_prefix = "GARMIN_TOOL_"
        case_sensitive = False


# Global config instance
_config: ToolConfig | None = None


def get_tool_config() -> ToolConfig:
    """Get or create the global tool configuration."""
    global _config
    if _config is None:
        _config = ToolConfig()
    return _config


def reload_tool_config() -> ToolConfig:
    """Reload the tool configuration from environment."""
    global _config
    _config = ToolConfig()
    return _config
