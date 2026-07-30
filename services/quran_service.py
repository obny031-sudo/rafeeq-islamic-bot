"""Quran API service with Redis caching and resilient HTTP."""

import logging
from typing import Any, Dict, List, Optional

from cache import CacheKeyBuilder, RedisCache
from config.settings import settings
from services.http_client import ResilientHttpClient

logger = logging.getLogger(__name__)


class QuranService:
    """Fetch Quran content from alquran.cloud with caching."""

    def __init__(self, cache: Optional[RedisCache] = None):
        self.base_url = settings.quran.QURAN_API_URL
        self.client = ResilientHttpClient(timeout=settings.quran.QURAN_API_TIMEOUT)
        self.cache = cache
        self.cache_ttl = settings.quran.QURAN_CACHE_TTL

    async def _cached_get(self, cache_key: str, url: str) -> Optional[Dict[str, Any]]:
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        data = await self.client.get(url)
        if data and data.get("code") == 200:
            result = data.get("data")
            if result and self.cache:
                await self.cache.set(cache_key, result, self.cache_ttl)
            return result
        return None

    async def get_surah_list(self) -> Optional[List[Dict[str, Any]]]:
        cache_key = "quran:surah_list"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        data = await self.client.get(f"{self.base_url}/surah")
        if data and data.get("code") == 200:
            result = data.get("data")
            if result and self.cache:
                await self.cache.set(cache_key, result, self.cache_ttl)
            return result
        return None

    async def get_surah_ayahs(
        self,
        surah_number: int,
        edition: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        edition = edition or settings.quran.DEFAULT_QURAN_EDITION
        cache_key = CacheKeyBuilder.quran_surah(surah_number, edition)
        return await self._cached_get(cache_key, f"{self.base_url}/surah/{surah_number}/{edition}")

    async def get_ayah(
        self,
        surah_number: int,
        ayah_number: int,
        edition: Optional[str] = None,
    ) -> Optional[str]:
        edition = edition or settings.quran.DEFAULT_QURAN_EDITION
        cache_key = CacheKeyBuilder.quran_ayah(surah_number, ayah_number, edition)
        result = await self._cached_get(
            cache_key,
            f"{self.base_url}/ayah/{surah_number}:{ayah_number}/{edition}",
        )
        if result:
            return result.get("text")
        return None

    async def close(self) -> None:
        await self.client.close()


quran_service = QuranService()
