"""
User repository for user-specific database operations.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.user import User, Language, Role
from .base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Get user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
        
        Returns:
            User instance or None
        """
        try:
            result = await self.session.execute(
                select(User).where(User.id == telegram_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
            return None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Telegram username
        
        Returns:
            User instance or None
        """
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: Language = Language.ENGLISH,
        role: Role = Role.USER
    ) -> User:
        """
        Create a new user.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            language: Preferred language
            role: User role
        
        Returns:
            Created User instance
        """
        user = User(
            id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            role=role,
            last_active_date=datetime.now(timezone.utc)
        )
        return await self.create(user)
    
    async def update_last_active(self, telegram_id: int) -> bool:
        """
        Update user's last active timestamp.
        
        Args:
            telegram_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.execute(
                update(User)
                .where(User.id == telegram_id)
                .values(last_active_date=datetime.now(timezone.utc))
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating last active for user {telegram_id}: {e}")
            return False
    
    async def update_location(
        self,
        telegram_id: int,
        latitude: float,
        longitude: float,
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> bool:
        """
        Update user's location.
        
        Args:
            telegram_id: Telegram user ID
            latitude: Latitude
            longitude: Longitude
            city: City name
            country: Country name
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.execute(
                update(User)
                .where(User.id == telegram_id)
                .values(
                    latitude=latitude,
                    longitude=longitude,
                    city=city,
                    country=country
                )
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating location for user {telegram_id}: {e}")
            return False
    
    async def update_quran_position(
        self,
        telegram_id: int,
        surah_number: int,
        ayah_number: int
    ) -> bool:
        """
        Update user's last Quran reading position.
        
        Args:
            telegram_id: Telegram user ID
            surah_number: Surah number
            ayah_number: Ayah number
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.execute(
                update(User)
                .where(User.id == telegram_id)
                .values(
                    last_read_surah=surah_number,
                    last_read_ayah=ayah_number
                )
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating Quran position for user {telegram_id}: {e}")
            return False
    
    async def increment_streak(self, telegram_id: int) -> bool:
        """
        Increment user's streak days.
        
        Args:
            telegram_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.execute(
                update(User)
                .where(User.id == telegram_id)
                .values(streak_days=User.streak_days + 1)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error incrementing streak for user {telegram_id}: {e}")
            return False
    
    async def reset_streak(self, telegram_id: int) -> bool:
        """
        Reset user's streak days.
        
        Args:
            telegram_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.execute(
                update(User)
                .where(User.id == telegram_id)
                .values(streak_days=0)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error resetting streak for user {telegram_id}: {e}")
            return False
    
    async def update_role(self, telegram_id: int, role: Role) -> bool:
        """
        Update user's role.
        
        Args:
            telegram_id: Telegram user ID
            role: New role
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.execute(
                update(User)
                .where(User.id == telegram_id)
                .values(role=role)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error updating role for user {telegram_id}: {e}")
            return False
    
    async def get_users_by_role(self, role: Role) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            role: User role
        
        Returns:
            List of User instances
        """
        try:
            result = await self.session.execute(
                select(User).where(User.role == role)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            return []
    
    async def get_active_users(self, days: int = 7) -> List[User]:
        """
        Get users active within the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of active User instances
        """
        try:
            cutoff_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            result = await self.session.execute(
                select(User).where(User.last_active_date >= cutoff_date)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
