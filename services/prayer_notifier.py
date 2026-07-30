"""
Prayer notification service for broadcasting Adhan at prayer times.
Integrates with AdhanService to send audio notifications at each prayer time.
"""

import logging
import asyncio
from datetime import datetime, time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from models.content import UserNotificationPreference
from services.adhan_service import get_adhan_service
from services.prayer_service import prayer_service
from config.settings import settings

logger = logging.getLogger(__name__)


class PrayerNotifier:
    """Service for sending prayer time notifications with Adhan"""
    
    def __init__(self, bot):
        self.bot = bot
        self.adhan_service = get_adhan_service(bot)
        self.prayer_cache = {}
    
    async def get_prayer_times(self) -> dict:
        """Get today's prayer times for Cairo"""
        prayer_data = await prayer_service.get_prayer_times(
            latitude=settings.prayer.DEFAULT_LATITUDE,
            longitude=settings.prayer.DEFAULT_LONGITUDE,
            method=settings.prayer.DEFAULT_PRAYER_METHOD,
            asr_method=settings.prayer.DEFAULT_ASR_METHOD,
            timezone=settings.prayer.DEFAULT_TIMEZONE
        )
        return prayer_data
    
    async def get_users_with_prayer_notifications(self, db: AsyncSession) -> List[tuple]:
        """Get users who have prayer notifications enabled"""
        result = await db.execute(
            select(User.id, UserNotificationPreference.prayer_notifications_enabled, UserNotificationPreference.adhan_audio_enabled)
            .join(UserNotificationPreference, User.id == UserNotificationPreference.user_id)
            .where(UserNotificationPreference.prayer_notifications_enabled == True)
        )
        return result.all()
    
    async def broadcast_prayer_notification(
        self,
        db: AsyncSession,
        prayer: str,
        prayer_time: str
    ):
        """
        Broadcast prayer notification to all users with notifications enabled
        
        Args:
            db: Database session
            prayer: Prayer name (fajr, dhuhr, asr, maghrib, isha)
            prayer_time: Prayer time string
        """
        try:
            users = await self.get_users_with_prayer_notifications(db)
            
            for user_id, prayer_enabled, audio_enabled in users:
                if prayer_enabled:
                    success = await self.adhan_service.broadcast_adhan(
                        chat_id=user_id,
                        prayer=prayer,
                        prayer_time=prayer_time,
                        audio_enabled=audio_enabled
                    )
                    
                    if success:
                        logger.info(f"Sent {prayer} notification to user {user_id}")
                    else:
                        logger.error(f"Failed to send {prayer} notification to user {user_id}")
            
            logger.info(f"Broadcasted {prayer} notification to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error broadcasting prayer notification: {e}")
    
    async def check_and_broadcast_prayers(self, db: AsyncSession):
        """Check if it's prayer time and broadcast if needed"""
        try:
            prayer_data = await self.get_prayer_times()
            
            if not prayer_data:
                logger.warning("Could not fetch prayer times")
                return
            
            timings = prayer_data.get("timings", {})
            current_time = datetime.now().strftime("%H:%M")
            
            # Prayer mappings
            prayers = {
                'Fajr': 'fajr',
                'Dhuhr': 'dhuhr',
                'Asr': 'asr',
                'Maghrib': 'maghrib',
                'Isha': 'isha'
            }
            
            # Check each prayer time
            for prayer_en, prayer_key in prayers.items():
                prayer_time = timings.get(prayer_en)
                
                if prayer_time == current_time:
                    # Avoid duplicate notifications
                    cache_key = f"{prayer_key}_{prayer_time}"
                    if cache_key not in self.prayer_cache:
                        await self.broadcast_prayer_notification(db, prayer_key, prayer_time)
                        self.prayer_cache[cache_key] = datetime.now()
                        logger.info(f"Broadcasted {prayer_key} Adhan at {prayer_time}")
            
            # Clean old cache entries (older than 1 hour)
            current_dt = datetime.now()
            self.prayer_cache = {
                k: v for k, v in self.prayer_cache.items()
                if (current_dt - v).seconds < 3600
            }
            
        except Exception as e:
            logger.error(f"Error checking prayer times: {e}")


# Global instance
prayer_notifier: Optional[PrayerNotifier] = None


def get_prayer_notifier(bot) -> PrayerNotifier:
    """Get or create PrayerNotifier instance"""
    global prayer_notifier
    if prayer_notifier is None:
        prayer_notifier = PrayerNotifier(bot)
    return prayer_notifier
