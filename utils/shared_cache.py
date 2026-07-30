"""Shared Redis cache instance for all services."""

from cache import RedisCache
from config.settings import settings

shared_cache = RedisCache(settings.REDIS_URL, settings.REDIS_CACHE_DB)
