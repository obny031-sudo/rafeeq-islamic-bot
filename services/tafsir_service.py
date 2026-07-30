"""Tafsir service with external API and caching."""

import logging
from typing import Any, Dict, Optional

from cache import CacheKeyBuilder, RedisCache
from config.settings import settings
from services.http_client import ResilientHttpClient

logger = logging.getLogger(__name__)


class TafsirService:
    """Fetch Tafsir commentary from alquran.cloud."""

    TAFSIR_EDITION = "en.tafsir"

    def __init__(self, cache: Optional[RedisCache] = None):
        self.base_url = settings.quran.QURAN_API_URL
        self.client = ResilientHttpClient(timeout=settings.quran.QURAN_API_TIMEOUT)
        self.cache = cache
        self.cache_ttl = settings.quran.QURAN_CACHE_TTL

    async def get_tafsir(self, surah_number: int, ayah_number: int) -> Optional[Dict[str, Any]]:
        cache_key = f"tafsir:{surah_number}:{ayah_number}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        data = await self.client.get(
            f"{self.base_url}/ayah/{surah_number}:{ayah_number}/{self.TAFSIR_EDITION}"
        )
        if not data or data.get("code") != 200:
            return None

        ayah_data = data.get("data", {})
        result = {
            "surah": surah_number,
            "ayah": ayah_number,
            "text": ayah_data.get("text", ""),
            "edition": self.TAFSIR_EDITION,
        }

        if self.cache:
            await self.cache.set(cache_key, result, self.cache_ttl)
        return result

    async def close(self) -> None:
        await self.client.close()


tafsir_service = TafsirService()
