"""Quran search service with caching."""

import logging
from typing import Any, Dict, List, Optional

from config.settings import settings
from services.http_client import ResilientHttpClient

logger = logging.getLogger(__name__)


class SearchService:
    """Search Quran text via alquran.cloud API."""

    def __init__(self):
        self.base_url = settings.quran.QURAN_API_URL
        self.client = ResilientHttpClient(timeout=settings.quran.QURAN_API_TIMEOUT)

    async def search_quran(
        self,
        keyword: str,
        surah: str = "all",
        edition: str = "en",
        page: int = 1,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        keyword = keyword.strip()
        if not keyword:
            return []

        url = f"{self.base_url}/search/{keyword}/{surah}/{edition}"
        data = await self.client.get(url, params={"page": page, "size": limit})
        if not data or data.get("code") != 200:
            return []

        matches = data.get("data", {}).get("matches", [])
        return matches[:limit]

    async def close(self) -> None:
        await self.client.close()


search_service = SearchService()
