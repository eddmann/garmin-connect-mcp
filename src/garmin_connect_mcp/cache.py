"""Caching utilities for Garmin Connect MCP tools."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from .config import get_tool_config

# Global cache storage
_cache: dict[str, tuple[Any, float]] = {}


def cached_call(cache_key_prefix: str, ttl_seconds: int | None = None) -> Callable:
    """
    Decorator for caching function results with TTL.

    Args:
        cache_key_prefix: Prefix for the cache key
        ttl_seconds: Time to live in seconds (uses config default if None)

    Returns:
        Decorated function with caching
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            config = get_tool_config()

            # Check if caching is enabled
            if not config.enable_caching:
                return await func(*args, **kwargs)

            # Generate cache key from function name and arguments
            cache_key = f"{cache_key_prefix}:{func.__name__}:{args}:{kwargs}"

            # Check cache
            if cache_key in _cache:
                cached_value, cached_time = _cache[cache_key]
                ttl = ttl_seconds if ttl_seconds is not None else config.cache_ttl_seconds
                if time.time() - cached_time < ttl:
                    return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            _cache[cache_key] = (result, time.time())
            return result

        return wrapper

    return decorator


def clear_cache(prefix: str | None = None) -> None:
    """
    Clear cached values.

    Args:
        prefix: If provided, only clear cache keys starting with this prefix.
                If None, clear all cache.
    """
    global _cache

    if prefix is None:
        _cache.clear()
    else:
        # Clear only keys with the given prefix
        keys_to_delete = [key for key in _cache if key.startswith(f"{prefix}:")]
        for key in keys_to_delete:
            del _cache[key]


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    now = time.time()
    config = get_tool_config()

    valid_entries = sum(
        1 for _, cached_time in _cache.values() if now - cached_time < config.cache_ttl_seconds
    )

    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(_cache) - valid_entries,
        "ttl_seconds": config.cache_ttl_seconds,
        "enabled": config.enable_caching,
    }
