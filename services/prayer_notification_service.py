import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from services.prayer_service import prayer_service
from services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)

class PrayerNotificationService:
    """
    Service to manage prayer notifications for users.
    Fetches prayer times and schedules notifications based on user location.
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def schedule_user_prayer_notifications(self, user_id: int, db: AsyncSession):
        """
        Schedule prayer notifications for a user based on their location.
        
        Args:
            user_id: Telegram user ID
            db: Database session
        """
        try:
            # Get user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.latitude or not user.prayer_notifications_enabled:
                logger.info(f"User {user_id} not eligible for prayer notifications")
                return
            
            # Fetch prayer times
            prayer_data = await prayer_service.get_prayer_times(
                latitude=user.latitude,
                longitude=user.longitude,
                method=user.prayer_method,
                asr_method=user.asr_method,
                timezone=user.timezone
            )
            
            if not prayer_data:
                logger.error(f"Failed to fetch prayer times for user {user_id}")
                return
            
            timings = prayer_data.get("timings", {})
            
            # Schedule notifications for each prayer
            prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
            
            for prayer in prayers:
                prayer_time = timings.get(prayer)
                if prayer_time:
                    # Parse time (format: HH:MM)
                    try:
                        # Remove AM/PM if present and parse
                        time_str = prayer_time.split(' ')[0]
                        scheduler_service.add_prayer_notification_job(
                            user_id=user_id,
                            prayer_name=prayer,
                            prayer_time=time_str
                        )
                        logger.info(f"Scheduled {prayer} notification for user {user_id} at {time_str}")
                    except Exception as e:
                        logger.error(f"Failed to parse prayer time {prayer_time}: {e}")
            
        except Exception as e:
            logger.error(f"Error scheduling prayer notifications for user {user_id}: {e}")
    
    async def remove_user_prayer_notifications(self, user_id: int):
        """Remove all prayer notifications for a user"""
        prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
        
        for prayer in prayers:
            scheduler_service.remove_prayer_notification_job(user_id, prayer)
        
        logger.info(f"Removed all prayer notifications for user {user_id}")
    
    async def send_prayer_notification(self, user_id: int, prayer_name: str):
        """
        Send prayer notification message to user.
        
        Args:
            user_id: Telegram user ID
            prayer_name: Name of the prayer
        """
        try:
            message = (
                f"🕌 *Prayer Time Reminder*\n\n"
                f"It's time for {prayer_name} prayer.\n\n"
                f"May Allah accept your prayers. 🤲"
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Sent {prayer_name} notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send prayer notification to user {user_id}: {e}")
    
    async def refresh_all_user_notifications(self, db: AsyncSession):
        """
        Refresh prayer notifications for all users with enabled notifications.
        This should be called daily to update prayer times.
        """
        try:
            result = await db.execute(
                select(User).where(
                    User.prayer_notifications_enabled == True,
                    User.latitude.isnot(None)
                )
            )
            users = result.scalars().all()
            
            logger.info(f"Refreshing prayer notifications for {len(users)} users")
            
            for user in users:
                await self.schedule_user_prayer_notifications(user.id, db)
            
        except Exception as e:
            logger.error(f"Error refreshing user notifications: {e}")
