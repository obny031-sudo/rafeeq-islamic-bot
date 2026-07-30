"""
Metrics repository for tracking usage, streaks, and achievements.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from models.metrics import UserMetrics, ModuleUsage, Achievement, UserAchievement
from models.user import User
from .base import BaseRepository

logger = logging.getLogger(__name__)


class UserMetricsRepository(BaseRepository[UserMetrics]):
    """Repository for UserMetrics operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserMetrics, session)
    
    async def get_or_create(self, user_id: int) -> UserMetrics:
        """Get or create user metrics"""
        metrics = await self.get_by_id(user_id)
        if not metrics:
            metrics = UserMetrics(id=user_id)
            await self.create(metrics)
        return metrics
    
    async def increment_messages(self, user_id: int) -> bool:
        """Increment total message count"""
        try:
            await self.session.execute(
                update(UserMetrics)
                .where(UserMetrics.id == user_id)
                .values(total_messages=UserMetrics.total_messages + 1)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error incrementing messages for user {user_id}: {e}")
            return False
    
    async def increment_quran_read(self, user_id: int, count: int = 1) -> bool:
        """Increment Quran Ayahs read count"""
        try:
            await self.session.execute(
                update(UserMetrics)
                .where(UserMetrics.id == user_id)
                .values(quran_ayahs_read=UserMetrics.quran_ayahs_read + count)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error incrementing Quran read for user {user_id}: {e}")
            return False
    
    async def increment_prayers(self, user_id: int) -> bool:
        """Increment prayers completed count"""
        try:
            await self.session.execute(
                update(UserMetrics)
                .where(UserMetrics.id == user_id)
                .values(prayers_completed=UserMetrics.prayers_completed + 1)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error incrementing prayers for user {user_id}: {e}")
            return False
    
    async def add_xp(self, user_id: int, xp: int) -> bool:
        """Add XP points and update level if needed"""
        try:
            metrics = await self.get_or_create(user_id)
            metrics.xp_points += xp
            
            # Simple level calculation: level = sqrt(xp / 100)
            new_level = int((metrics.xp_points / 100) ** 0.5) + 1
            if new_level > metrics.level:
                metrics.level = new_level
                logger.info(f"User {user_id} leveled up to {new_level}")
            
            await self.update(metrics)
            return True
        except Exception as e:
            logger.error(f"Error adding XP for user {user_id}: {e}")
            return False


class ModuleUsageRepository(BaseRepository[ModuleUsage]):
    """Repository for ModuleUsage operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ModuleUsage, session)
    
    async def log_usage(
        self,
        user_id: int,
        module_name: str,
        action: str
    ) -> ModuleUsage:
        """Log module usage"""
        usage = ModuleUsage(
            user_id=user_id,
            module_name=module_name,
            action=action
        )
        return await self.create(usage)
    
    async def get_user_usage(
        self,
        user_id: int,
        module_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ModuleUsage]:
        """Get user's module usage history"""
        try:
            query = select(ModuleUsage).where(ModuleUsage.user_id == user_id)
            if module_name:
                query = query.where(ModuleUsage.module_name == module_name)
            query = query.order_by(ModuleUsage.timestamp.desc()).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting usage for user {user_id}: {e}")
            return []
    
    async def get_module_stats(self, module_name: str) -> dict:
        """Get statistics for a specific module"""
        try:
            result = await self.session.execute(
                select(
                    func.count(ModuleUsage.id).label('total'),
                    func.count(func.distinct(ModuleUsage.user_id)).label('unique_users')
                ).where(ModuleUsage.module_name == module_name)
            )
            row = result.one()
            return {
                'total_uses': row.total,
                'unique_users': row.unique_users
            }
        except Exception as e:
            logger.error(f"Error getting stats for module {module_name}: {e}")
            return {'total_uses': 0, 'unique_users': 0}


class AchievementRepository(BaseRepository[Achievement]):
    """Repository for Achievement operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Achievement, session)
    
    async def get_by_category(self, category: str) -> List[Achievement]:
        """Get achievements by category"""
        try:
            result = await self.session.execute(
                select(Achievement).where(Achievement.category == category)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting achievements for category {category}: {e}")
            return []


class UserAchievementRepository(BaseRepository[UserAchievement]):
    """Repository for UserAchievement operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserAchievement, session)
    
    async def get_user_achievements(self, user_id: int) -> List[UserAchievement]:
        """Get user's achievements"""
        try:
            result = await self.session.execute(
                select(UserAchievement).where(UserAchievement.user_id == user_id)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return []
    
    async def unlock_achievement(self, user_id: int, achievement_id: int) -> bool:
        """Unlock achievement for user"""
        try:
            # Check if already unlocked
            result = await self.session.execute(
                select(UserAchievement).where(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement_id
                )
            )
            user_achievement = result.scalar_one_or_none()
            
            if user_achievement:
                if user_achievement.unlocked:
                    return False  # Already unlocked
                
                user_achievement.unlocked = True
                user_achievement.unlocked_at = datetime.now(timezone.utc)
            else:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    unlocked=True,
                    unlocked_at=datetime.now(timezone.utc)
                )
                await self.create(user_achievement)
            
            await self.session.flush()
            logger.info(f"Unlocked achievement {achievement_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error unlocking achievement for user {user_id}: {e}")
            return False
