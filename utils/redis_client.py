import redis.asyncio as redis
from config.settings import settings

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        return self.client
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str):
        """Get value from Redis"""
        return await self.client.get(key)
    
    async def set(self, key: str, value: str, ex: int = None):
        """Set value in Redis with optional expiration"""
        return await self.client.set(key, value, ex=ex)
    
    async def delete(self, key: str):
        """Delete key from Redis"""
        return await self.client.delete(key)
    
    async def exists(self, key: str):
        """Check if key exists"""
        return await self.client.exists(key)

redis_client = RedisClient()
