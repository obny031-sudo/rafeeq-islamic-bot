"""
Rate limiting middleware using Token Bucket algorithm.
Prevents Telegram flood bans by limiting user actions per second.
"""

import logging
import time
import asyncio
from typing import Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Token Bucket rate limiter middleware.
    Limits users to max 3 actions per second to prevent flood bans.
    """
    
    def __init__(self, max_requests: int = 3, time_window: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
        """
        super().__init__()
        self.max_requests = max_requests
        self.time_window = time_window
        self.redis = None  # Will be set when Redis connects
        self.prefix = "rate_limit:"
    
    async def __call__(self, handler, event: TelegramObject, data: Dict):
        """Process event through rate limiter"""
        
        # Initialize Redis client if not set
        if self.redis is None:
            self.redis = redis_client.client
        
        # Get user ID from update
        user_id = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
            elif event.inline_query:
                user_id = event.inline_query.from_user.id
            elif event.chosen_inline_result:
                user_id = event.chosen_inline_result.from_user.id
            elif event.poll_answer:
                user_id = event.poll_answer.user.id
            elif event.my_chat_member:
                user_id = event.my_chat_member.from_user.id
            elif event.chat_member:
                user_id = event.chat_member.from_user.id
        
        if not user_id:
            # No user ID, skip rate limiting
            return await handler(event, data)
        
        try:
            # Check rate limit
            if await self._is_rate_limited(user_id):
                logger.warning(f"Rate limit exceeded for user {user_id}")
                
                # Send rate limit message if it's a message update
                if isinstance(event, Update) and event.message:
                    await event.message.answer(
                        "⚠️ يرجى التباطؤ في الطلبات.\n"
                        "يمكنك إرسال 3 رسائل في الثانية الواحدة.",
                        parse_mode="Markdown"
                    )
                
                return  # Block the event
            
            # Record request
            await self._record_request(user_id)
            
            # Pass to handler
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
           # On error, allow the request to pass
            return await handler(event, data)
    
    async def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        try:
            key = f"{self.prefix}{user_id}"
            
            # Get current request count
            current = await self.redis.get(key)
            if current is None:
                return False
            
            return int(current) >= self.max_requests
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    async def _record_request(self, user_id: int):
        """Record user request"""
        try:
            key = f"{self.prefix}{user_id}"
            
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.time_window)
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Error recording request: {e}")
    
    async def reset_user_limit(self, user_id: int):
        """Reset rate limit for specific user (admin function)"""
        try:
            key = f"{self.prefix}{user_id}"
            await self.redis.delete(key)
            logger.info(f"Reset rate limit for user {user_id}")
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get rate limit statistics for user"""
        try:
            key = f"{self.prefix}{user_id}"
            current = await self.redis.get(key)
            ttl = await self.redis.ttl(key)
            
            return {
                "current_requests": int(current) if current else 0,
                "max_requests": self.max_requests,
                "time_window": self.time_window,
                "reset_in_seconds": ttl if ttl > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"error": str(e)}


# Global instance
rate_limit_middleware = RateLimitMiddleware(max_requests=3, time_window=1)
