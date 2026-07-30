"""
Base cache interface and Redis abstraction layer.
"""

import logging
from typing import Optional, Any
from abc import ABC, abstractmethod
import json
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache"""
        pass


class RedisCache(CacheBackend):
    """
    Redis-based cache implementation.
    Provides async operations with automatic serialization/deserialization.
    """
    
    def __init__(self, redis_url: str, db: int = 0):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            db: Redis database number
        """
        self.redis_url = redis_url
        self.db = db
        self.client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                db=self.db,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            self._connected = True
            logger.info(f"Connected to Redis cache (DB: {self.db})")
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("Disconnected from Redis cache")
    
    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string"""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return json.dumps(value)
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to value"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return None
        
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting key {key} from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return False
        
        try:
            serialized = self._serialize(value)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key} from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key} in cache: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache in current database"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return False
        
        try:
            await self.client.flushdb()
            logger.info(f"Cleared cache in DB {self.db}")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return {}
        
        try:
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Error getting multiple keys from cache: {e}")
            return {}
    
    async def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        if not self._connected:
            logger.warning("Redis cache not connected")
            return False
        
        try:
            serialized_mapping = {k: self._serialize(v) for k, v in mapping.items()}
            if ttl:
                # For TTL, we need to set each key individually
                for key, value in serialized_mapping.items():
                    await self.client.setex(key, ttl, value)
            else:
                await self.client.mset(serialized_mapping)
            return True
        except Exception as e:
            logger.error(f"Error setting multiple keys in cache: {e}")
            return False
