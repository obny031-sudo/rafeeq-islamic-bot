"""Hadith service with external API and caching."""

import logging
import random
from typing import Any, Dict, List, Optional

from cache import RedisCache
from services.http_client import ResilientHttpClient

logger = logging.getLogger(__name__)

HADITH_COLLECTIONS = ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"]


class HadithService:
    """Fetch Hadith from hadith.gading.dev API."""

    BASE_URL = "https://api.hadith.gading.dev"

    def __init__(self, cache: Optional[RedisCache] = None):
        self.client = ResilientHttpClient(timeout=30.0)
        self.cache = cache

    async def get_random_hadith(self, collection: Optional[str] = None) -> Optional[Dict[str, Any]]:
        collection = collection or random.choice(HADITH_COLLECTIONS)
        cache_key = f"hadith:random:{collection}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        meta = await self.client.get(f"{self.BASE_URL}/books/{collection}")
        if not meta or not meta.get("data"):
            return None

        total = meta["data"].get("available", 1)
        number = random.randint(1, max(1, total))
        data = await self.client.get(f"{self.BASE_URL}/books/{collection}?range={number}-{number}")
        if not data or not data.get("data"):
            return None

        hadiths = data["data"].get("hadiths", [])
        if not hadiths:
            return None

        item = hadiths[0]
        result = {
            "arabic": item.get("arabic", ""),
            "translation": item.get("id", item.get("english", "")),
            "reference": f"{meta['data'].get('name', collection)} #{number}",
            "collection": collection,
        }

        if self.cache:
            await self.cache.set(cache_key, result, ttl=3600)
        return result

    async def get_hadith_by_number(self, collection: str, number: int) -> Optional[Dict[str, Any]]:
        data = await self.client.get(f"{self.BASE_URL}/books/{collection}?range={number}-{number}")
        if not data or not data.get("data"):
            return None
        hadiths = data["data"].get("hadiths", [])
        if not hadiths:
            return None
        item = hadiths[0]
        return {
            "arabic": item.get("arabic", ""),
            "translation": item.get("id", item.get("english", "")),
            "reference": f"{collection} #{number}",
            "collection": collection,
        }

    async def close(self) -> None:
        await self.client.close()


hadith_service = HadithService()
