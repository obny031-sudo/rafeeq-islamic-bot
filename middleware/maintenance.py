"""
Maintenance Mode Middleware
Blocks non-admin users when maintenance mode is enabled.
"""

import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class MaintenanceMiddleware(BaseMiddleware):
    """Middleware to block non-admin users during maintenance mode"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Check maintenance mode and block non-admin users if enabled"""
        try:
            redis = redis_client
            if not redis or not redis.client:
                # If Redis is not available, allow all requests
                return await handler(event, data)
            
            # Check maintenance mode
            maintenance_mode = await redis.client.get("maintenance_mode")
            is_maintenance = maintenance_mode == b"1" or maintenance_mode == "1"
            
            if not is_maintenance:
                # Not in maintenance mode, proceed normally
                return await handler(event, data)
            
            # In maintenance mode - check if user is admin
            from config.settings import settings
            
            if hasattr(event, 'from_user'):
                user_id = event.from_user.id
                
                # Allow admin access
                if settings.ADMIN_ID and user_id == settings.ADMIN_ID:
                    return await handler(event, data)
                
                # Block non-admin users
                maintenance_message = (
                    "� *وضع الصيانة* �\n\n"
                    "البوت حالياً في وضع الصيانة الدورية، يرجى المحاولة لاحقاً.\n\n"
                    "⚙️ The bot is currently under maintenance.\n"
                    "Please try again later."
                )
                
                if isinstance(event, CallbackQuery):
                    await event.answer("Maintenance mode active", show_alert=True)
                    if event.message:
                        await event.message.edit_text(
                            maintenance_message,
                            parse_mode="Markdown"
                        )
                elif isinstance(event, Message):
                    await event.answer(
                        maintenance_message,
                        parse_mode="Markdown"
                    )
                
                logger.info(f"Blocked user {user_id} during maintenance mode")
                return None
            
            # No from_user attribute, proceed normally
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Error in maintenance middleware: {e}")
            # On error, allow the request to proceed
            return await handler(event, data)
