"""
Caching utilities for the Marine & Biodiversity Data Explorer.

This module provides caching mechanisms to improve performance by reducing
redundant API calls and database queries.
"""

from functools import wraps, lru_cache
from typing import Any, Callable, Optional, Dict
import time
import logging

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Time-To-Live cache that expires entries after a specified time.

    This is useful for API responses that may change over time but can be
    cached for short periods to reduce API calls.
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize TTL cache.

        Args:
            ttl_seconds: Time to live for cache entries in seconds (default: 300 = 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() - entry['timestamp'] > self.ttl_seconds:
            # Entry expired, remove it
            del self._cache[key]
            logger.debug(f"Cache entry expired: {key}")
            return None

        logger.debug(f"Cache hit: {key}")
        return entry['value']

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        logger.debug(f"Cache set: {key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def size(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry['timestamp'] > self.ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


def cached_with_ttl(ttl_seconds: int = 300):
    """
    Decorator to cache function results with TTL.

    Args:
        ttl_seconds: Time to live for cache entries in seconds

    Example:
        @cached_with_ttl(ttl_seconds=600)
        def expensive_api_call(species_name):
            return api.search(species_name)
    """
    cache = TTLCache(ttl_seconds=ttl_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Cache miss - call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        # Attach cache management methods to the wrapper
        wrapper.cache_clear = cache.clear
        wrapper.cache_info = lambda: {
            'size': cache.size(),
            'ttl_seconds': ttl_seconds
        }
        wrapper.cache_cleanup = cache.cleanup_expired

        return wrapper
    return decorator


# Global caches for specific use cases
trait_cache = TTLCache(ttl_seconds=3600)  # 1 hour for trait data
species_cache = TTLCache(ttl_seconds=600)  # 10 minutes for species searches
occurrence_cache = TTLCache(ttl_seconds=300)  # 5 minutes for occurrence data


def get_or_cache(cache: TTLCache, key: str, fetch_func: Callable, *args, **kwargs) -> Any:
    """
    Get value from cache or fetch it using provided function.

    Args:
        cache: TTLCache instance to use
        key: Cache key
        fetch_func: Function to call if cache miss
        *args, **kwargs: Arguments to pass to fetch_func

    Returns:
        Cached or fetched value

    Example:
        result = get_or_cache(
            trait_cache,
            f"traits:{aphia_id}",
            trait_db.get_traits_for_species,
            aphia_id
        )
    """
    cached_value = cache.get(key)
    if cached_value is not None:
        return cached_value

    # Cache miss - fetch and cache
    value = fetch_func(*args, **kwargs)
    cache.set(key, value)
    return value


def clear_all_caches():
    """Clear all global caches."""
    trait_cache.clear()
    species_cache.clear()
    occurrence_cache.clear()
    logger.info("All caches cleared")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about all caches.

    Returns:
        Dictionary with cache statistics
    """
    return {
        'trait_cache': {
            'size': trait_cache.size(),
            'ttl_seconds': trait_cache.ttl_seconds
        },
        'species_cache': {
            'size': species_cache.size(),
            'ttl_seconds': species_cache.ttl_seconds
        },
        'occurrence_cache': {
            'size': occurrence_cache.size(),
            'ttl_seconds': occurrence_cache.ttl_seconds
        }
    }
