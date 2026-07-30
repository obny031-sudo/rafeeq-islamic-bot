import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from models.user import User, Language

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """Auto-create users if they don't exist in the database."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user_id from different event types
        user_id = None
        user_data = None

        if isinstance(event, Message):
            user_id = event.from_user.id
            user_data = event.from_user
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            user_data = event.from_user
        else:
            # For other event types, try to extract user_id
            return await handler(event, data)

        if not user_id:
            return await handler(event, data)

        # Get database session from data
        db: AsyncSession = data.get("db")
        if not db:
            return await handler(event, data)

        # Check if user exists
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # Auto-create user
            username = getattr(user_data, 'username', None) or f"user_{user_id}"
            first_name = getattr(user_data, 'first_name', None) or ""
            last_name = getattr(user_data, 'last_name', None) or ""

            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language=Language.ARABIC,
                timezone="Africa/Cairo",
                latitude=30.0444,
                longitude=31.2357,
                city="القاهرة",
                country="مصر",
                last_active_date=datetime.now(timezone.utc)
            )
            db.add(user)
            await db.flush()
            logger.info(f"Auto-created user {user_id} with username {username}")

        # Update last active date
        user.last_active_date = datetime.now(timezone.utc)
        
        # Add user to data for handlers
        data["user"] = user

        return await handler(event, data)
