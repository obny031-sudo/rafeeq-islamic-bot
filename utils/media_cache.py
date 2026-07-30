"""
Redis media caching for Telegram file IDs.
Caches Telegram file_id for images and media assets to enable instant sending.
"""

import logging
from typing import Optional
from pathlib import Path
import hashlib
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class MediaCache:
    """Cache for Telegram media file IDs using Redis"""
    
    def __init__(self):
        self.redis = redis_client.client
        self.prefix = "media_cache:"
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file path"""
        return hashlib.md5(file_path.encode()).hexdigest()
    
    async def get_cached_file_id(self, file_path: str) -> Optional[str]:
        """
        Get cached Telegram file_id for a file.
        
        Args:
            file_path: Path to the media file
        
        Returns:
            Cached file_id or None if not found
        """
        try:
            file_hash = self._get_file_hash(file_path)
            key = f"{self.prefix}{file_hash}"
            
            file_id = await self.redis.get(key)
            if file_id:
                logger.debug(f"Cache hit for {file_path}")
                return file_id.decode('utf-8')
            
            logger.debug(f"Cache miss for {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached file_id: {e}")
            return None
    
    async def cache_file_id(self, file_path: str, file_id: str, ttl: int = 2592000):
        """
        Cache Telegram file_id for a file.
        
        Args:
            file_path: Path to the media file
            file_id: Telegram file_id from sent message
            ttl: Time to live in seconds (default 30 days)
        """
        try:
            file_hash = self._get_file_hash(file_path)
            key = f"{self.prefix}{file_hash}"
            
            await self.redis.setex(key, ttl, file_id)
            logger.info(f"Cached file_id for {file_path} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Error caching file_id: {e}")
    
    async def invalidate_cache(self, file_path: str):
        """
        Invalidate cached file_id for a file.
        
        Args:
            file_path: Path to the media file
        """
        try:
            file_hash = self._get_file_hash(file_path)
            key = f"{self.prefix}{file_hash}"
            
            await self.redis.delete(key)
            logger.info(f"Invalidated cache for {file_path}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    async def clear_all_cache(self):
        """Clear all media cache"""
        try:
            keys = await self.redis.keys(f"{self.prefix}*")
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} media cache entries")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        try:
            keys = await self.redis.keys(f"{self.prefix}*")
            return {
                "total_cached_files": len(keys),
                "cache_prefix": self.prefix
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"total_cached_files": 0, "cache_prefix": self.prefix}


# Global instance
media_cache = MediaCache()
