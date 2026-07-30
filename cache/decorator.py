"""
Caching decorator for API calls.
Provides Redis-first caching for external API calls.
"""

import logging
import functools
from typing import Optional, Callable, Any
from .base import CacheBackend

logger = logging.getLogger(__name__)


def cached(
    cache: CacheBackend,
    ttl: int = 3600,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results in Redis.
    
    Args:
        cache: Cache backend instance
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache keys
        key_builder: Custom function to build cache key (optional)
    
    Usage:
        @cached(cache=redis_cache, ttl=3600, key_prefix="prayer")
        async def get_prayer_times(lat, lon):
            # API call here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder: function_name + args + kwargs
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # Cache miss - call the function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                await cache.set(cache_key, result, ttl)
                logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(
    cache: CacheBackend,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        cache: Cache backend instance
        key_prefix: Prefix for cache keys
        key_builder: Custom function to build cache key (optional)
    
    Usage:
        @cache_invalidate(cache=redis_cache, key_prefix="prayer")
        async def update_user_location(user_id, lat, lon):
            # Update location
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            await cache.delete(cache_key)
            logger.debug(f"Invalidated cache for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


class CacheKeyBuilder:
    """Helper class to build cache keys"""
    
    @staticmethod
    def prayer_times(latitude: float, longitude: float, method: int, timezone: str) -> str:
        """Build cache key for prayer times"""
        return f"prayer:times:{latitude}:{longitude}:{method}:{timezone}"
    
    @staticmethod
    def quran_surah(surah_number: int, edition: str) -> str:
        """Build cache key for Quran Surah"""
        return f"quran:surah:{surah_number}:{edition}"
    
    @staticmethod
    def quran_ayah(surah_number: int, ayah_number: int, edition: str) -> str:
        """Build cache key for Quran Ayah"""
        return f"quran:ayah:{surah_number}:{ayah_number}:{edition}"
    
    @staticmethod
    def adhkar(category: str) -> str:
        """Build cache key for Adhkar"""
        return f"adhkar:{category}"
    
    @staticmethod
    def user_data(user_id: int, data_type: str) -> str:
        """Build cache key for user data"""
        return f"user:{user_id}:{data_type}"
