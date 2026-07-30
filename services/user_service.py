"""User state and settings management service."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import Language, Role, User
from repositories import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Centralized user operations with repository layer."""

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.session = session

    async def get_user(self, telegram_id: int) -> Optional[User]:
        return await self.repo.get_by_telegram_id(telegram_id)

    async def ensure_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        user = await self.repo.get_by_telegram_id(telegram_id)
        if user:
            await self.repo.update_last_active(telegram_id)
            return user
        return await self.repo.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=Language.ENGLISH,
            role=Role.USER,
        )

    async def update_location(
        self,
        telegram_id: int,
        latitude: float,
        longitude: float,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> bool:
        return await self.repo.update_location(telegram_id, latitude, longitude, city, country)

    async def update_quran_position(self, telegram_id: int, surah_number: int, ayah_number: int) -> bool:
        return await self.repo.update_quran_position(telegram_id, surah_number, ayah_number)

    async def toggle_language(self, telegram_id: int) -> Optional[Language]:
        user = await self.repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        new_lang = Language.ARABIC if user.language == Language.ENGLISH else Language.ENGLISH
        user.language = new_lang
        await self.session.flush()
        return new_lang

    async def toggle_prayer_notifications(self, telegram_id: int) -> Optional[bool]:
        user = await self.repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        user.prayer_notifications_enabled = not user.prayer_notifications_enabled
        await self.session.flush()
        return user.prayer_notifications_enabled

    async def toggle_daily_wird(self, telegram_id: int) -> Optional[bool]:
        user = await self.repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        user.daily_wird_enabled = not user.daily_wird_enabled
        await self.session.flush()
        return user.daily_wird_enabled

    async def update_last_active(self, telegram_id: int) -> bool:
        return await self.repo.update_last_active(telegram_id)

    async def get_language(self, telegram_id: int) -> str:
        user = await self.repo.get_by_telegram_id(telegram_id)
        return user.language.value if user and user.language else "en"
