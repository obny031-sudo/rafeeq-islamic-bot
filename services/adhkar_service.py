"""Adhkar service backed by PostgreSQL with Redis caching."""

import logging
import random
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cache import CacheKeyBuilder, RedisCache
from config.settings import settings
from models.knowledge_graph import ContentNode, ContentType
from services.content_fetcher import SmartContentFetcher

logger = logging.getLogger(__name__)


class AdhkarService:
    """Serve Adhkar from PostgreSQL content_nodes."""

    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache
        self.cache_ttl = settings.adhkar.ADHKAR_CACHE_TTL

    async def get_random_adhkar(
        self,
        session: AsyncSession,
        user_id: int,
        category: str = "general",
    ) -> Optional[Dict[str, Any]]:
        cache_key = CacheKeyBuilder.adhkar(f"{category}:{user_id}")
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        fetcher = SmartContentFetcher(session)
        results = await fetcher.get_random_adhkar(user_id=user_id, category=category, limit=1)
        if results:
            adhkar = results[0]
            if self.cache:
                await self.cache.set(cache_key, adhkar, ttl=60)
            return adhkar

        adhkar = await self._get_from_db(session, category)
        if adhkar and self.cache:
            await self.cache.set(cache_key, adhkar, ttl=60)
        return adhkar

    async def _get_from_db(self, session: AsyncSession, category: str) -> Optional[Dict[str, Any]]:
        try:
            query = select(ContentNode).where(
                ContentNode.content_type == ContentType.ADHKAR,
            )
            if category:
                query = query.where(ContentNode.tags.contains([category]))

            result = await session.execute(query)
            nodes = list(result.scalars().all())
            if not nodes:
                result = await session.execute(
                    select(ContentNode).where(ContentNode.content_type == ContentType.ADHKAR)
                )
                nodes = list(result.scalars().all())

            if not nodes:
                return None

            node = random.choice(nodes)
            return {
                "arabic": node.text_arabic,
                "transliteration": node.text_transliteration,
                "translation": node.text_translation,
                "reference": node.reference,
                "count": (node.tags or {}).get("count") if isinstance(node.tags, dict) else None,
            }
        except Exception as exc:
            logger.error("Error fetching adhkar from DB: %s", exc)
            return None

    async def count_by_category(self, session: AsyncSession, category: str) -> int:
        result = await session.execute(
            select(func.count())
            .select_from(ContentNode)
            .where(
                ContentNode.content_type == ContentType.ADHKAR,
                ContentNode.tags.contains([category]),
            )
        )
        return result.scalar() or 0


adhkar_service = AdhkarService()
