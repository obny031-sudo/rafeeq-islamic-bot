"""
Automated notification scheduler for Islamic content.
Handles scheduled notifications for Adhkar, Quran, Hadith, and other content.
"""

import logging
import asyncio
from datetime import datetime, time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.user import User
from models.content import (
    UserNotificationPreference,
    Adhkar,
    Hadith,
    IslamicTip,
    Dua,
    QuranAyah
)
from aiogram import Bot
import random

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Service for scheduling and sending automated notifications"""
    
    def __init__(self, bot: Bot, db_session_factory):
        self.bot = bot
        self.db_session_factory = db_session_factory
        self.last_sent = {}
    
    async def get_db_session(self) -> AsyncSession:
        """Get database session"""
        return self.db_session_factory()
    
    async def get_users_with_notification_enabled(
        self,
        notification_type: str
    ) -> list:
        """Get users who have a specific notification enabled"""
        async with self.get_db_session() as db:
            # Map notification types to preference columns
            preference_map = {
                'morning_adhkar': UserNotificationPreference.morning_adhkar_enabled,
                'evening_adhkar': UserNotificationPreference.evening_adhkar_enabled,
                'night_adhkar': UserNotificationPreference.night_adhkar_enabled,
                'friday_surah': UserNotificationPreference.friday_surah_enabled,
                'daily_ayah': UserNotificationPreference.daily_ayah_enabled,
                'daily_hadith': UserNotificationPreference.daily_hadith_enabled,
                'daily_tip': UserNotificationPreference.daily_tip_enabled,
                'daily_dua': UserNotificationPreference.daily_dua_enabled,
            }
            
            preference_column = preference_map.get(notification_type)
            if not preference_column:
                return []
            
            result = await db.execute(
                select(User.id)
                .join(UserNotificationPreference, User.id == UserNotificationPreference.user_id)
                .where(preference_column == True)
            )
            return [row[0] for row in result.all()]
    
    async def get_random_adhkar(self, category: str) -> Optional[dict]:
        """Get a random Adhkar from the database"""
        async with self.get_db_session() as db:
            result = await db.execute(
                select(Adhkar)
                .where(Adhkar.category == category)
                .order_by(func.random())
                .limit(1)
            )
            adhkar = result.scalar_one_or_none()
            
            if adhkar:
                return {
                    'arabic_text': adhkar.arabic_text,
                    'translation_ar': adhkar.translation_ar,
                    'reference': adhkar.reference,
                    'count': adhkar.count
                }
            return None
    
    async def get_random_hadith(self) -> Optional[dict]:
        """Get a random Hadith from the database"""
        async with self.get_db_session() as db:
            result = await db.execute(
                select(Hadith)
                .order_by(func.random())
                .limit(1)
            )
            hadith = result.scalar_one_or_none()
            
            if hadith:
                return {
                    'arabic_text': hadith.arabic_text,
                    'translation_ar': hadith.translation_ar,
                    'narrator': hadith.narrator,
                    'grade': hadith.grade,
                    'explanation_ar': hadith.explanation_ar
                }
            return None
    
    async def get_random_tip(self) -> Optional[dict]:
        """Get a random Islamic Tip from the database"""
        async with self.get_db_session() as db:
            result = await db.execute(
                select(IslamicTip)
                .order_by(func.random())
                .limit(1)
            )
            tip = result.scalar_one_or_none()
            
            if tip:
                return {
                    'title_ar': tip.title_ar,
                    'content_ar': tip.content_ar,
                    'reference': tip.reference
                }
            return None
    
    async def get_random_dua(self) -> Optional[dict]:
        """Get a random Dua from the database"""
        async with self.get_db_session() as db:
            result = await db.execute(
                select(Dua)
                .order_by(func.random())
                .limit(1)
            )
            dua = result.scalar_one_or_none()
            
            if dua:
                return {
                    'arabic_text': dua.arabic_text,
                    'translation_ar': dua.translation_ar,
                    'reference': dua.reference,
                    'occasion_ar': dua.occasion_ar
                }
            return None
    
    async def get_random_ayah(self) -> Optional[dict]:
        """Get a random Quranic Ayah from the database"""
        async with self.get_db_session() as db:
            result = await db.execute(
                select(QuranAyah)
                .order_by(func.random())
                .limit(1)
            )
            ayah = result.scalar_one_or_none()
            
            if ayah:
                return {
                    'arabic_text': ayah.arabic_text,
                    'translation_ar': ayah.translation_ar,
                    'surah_name_ar': ayah.surah_name_ar,
                    'ayah_number_in_surah': ayah.ayah_number_in_surah
                }
            return None
    
    async def send_morning_adhkar(self):
        """Send morning Adhkar notification at 6 AM"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            cache_key = f"morning_adhkar_{current_time}"
            
            # Check if already sent today
            if cache_key in self.last_sent:
                return
            
            users = await self.get_users_with_notification_enabled('morning_adhkar')
            adhkar = await self.get_random_adhkar('morning')
            
            if not adhkar:
                logger.warning("No morning Adhkar found in database")
                return
            
            message = (
                f"🌅 *أذكار الصباح*\n\n"
                f"{adhkar['arabic_text']}\n\n"
                f"{adhkar['translation_ar']}\n\n"
                f"📖 المرجع: {adhkar['reference']}\n\n"
                f"التكرار: {adhkar['count']} مرة"
            )
            
            for user_id in users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error sending morning Adhkar to user {user_id}: {e}")
            
            self.last_sent[cache_key] = datetime.now()
            logger.info(f"Sent morning Adhkar to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error in morning Adhkar scheduler: {e}")
    
    async def send_evening_adhkar(self):
        """Send evening Adhkar notification at 5 PM"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            cache_key = f"evening_adhkar_{current_time}"
            
            if cache_key in self.last_sent:
                return
            
            users = await self.get_users_with_notification_enabled('evening_adhkar')
            adhkar = await self.get_random_adhkar('evening')
            
            if not adhkar:
                logger.warning("No evening Adhkar found in database")
                return
            
            message = (
                f"🌙 *أذكار المساء*\n\n"
                f"{adhkar['arabic_text']}\n\n"
                f"{adhkar['translation_ar']}\n\n"
                f"📖 المرجع: {adhkar['reference']}\n\n"
                f"التكرار: {adhkar['count']} مرة"
            )
            
            for user_id in users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error sending evening Adhkar to user {user_id}: {e}")
            
            self.last_sent[cache_key] = datetime.now()
            logger.info(f"Sent evening Adhkar to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error in evening Adhkar scheduler: {e}")
    
    async def send_night_adhkar(self):
        """Send night Adhkar notification at 10:30 PM"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            cache_key = f"night_adhkar_{current_time}"
            
            if cache_key in self.last_sent:
                return
            
            users = await self.get_users_with_notification_enabled('night_adhkar')
            adhkar = await self.get_random_adhkar('sleep')
            
            if not adhkar:
                logger.warning("No night Adhkar found in database")
                return
            
            message = (
                f"😴 *أذكار النوم*\n\n"
                f"{adhkar['arabic_text']}\n\n"
                f"{adhkar['translation_ar']}\n\n"
                f"📖 المرجع: {adhkar['reference']}\n\n"
                f"التكرار: {adhkar['count']} مرة"
            )
            
            for user_id in users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error sending night Adhkar to user {user_id}: {e}")
            
            self.last_sent[cache_key] = datetime.now()
            logger.info(f"Sent night Adhkar to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error in night Adhkar scheduler: {e}")
    
    async def send_friday_surah_kahf(self):
        """Send Surah Al-Kahf reminder on Friday"""
        try:
            # Check if today is Friday
            if datetime.now().weekday() != 4:  # Friday is 4 (0=Monday, 6=Sunday)
                return
            
            current_time = datetime.now().strftime("%H:%M")
            cache_key = f"friday_surah_{current_time}"
            
            if cache_key in self.last_sent:
                return
            
            users = await self.get_users_with_notification_enabled('friday_surah')
            
            message = (
                "📖 *تذكير بسورة الكهف*\n\n"
                "يا أيها الذين آمنوا اذكروا نعمة الله عليكم إذ هم قوم أن يبسطوا إليكم أيديهم فكف أيديهم عنكم واتقوا الله وعلى الله فليتوكل المؤمنون\n\n"
                "📚 *فضل سورة الكهف:*\n"
                "- تقرأ يوم الجمعة لحماية من الدجال\n"
                "- نور من الجمعة إلى الجمعة\n"
                "- مغفرة للذنوب بين الجمعتين\n\n"
                "حاول قراءتها اليوم كاملة أو ما تيسر منها."
            )
            
            for user_id in users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error sending Friday Surah to user {user_id}: {e}")
            
            self.last_sent[cache_key] = datetime.now()
            logger.info(f"Sent Friday Surah reminder to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error in Friday Surah scheduler: {e}")
    
    async def send_daily_content(self):
        """Send random daily content (Ayah, Hadith, Tip, Dua) 3x daily"""
        try:
            current_hour = datetime.now().hour
            
            # Send at 9 AM, 12 PM, and 3 PM
            if current_hour not in [9, 12, 15]:
                return
            
            current_time = datetime.now().strftime("%H:%M")
            cache_key = f"daily_content_{current_time}"
            
            if cache_key in self.last_sent:
                return
            
            # Rotate content types based on time
            content_types = {
                9: ('daily_ayah', self.get_random_ayah, '📖 آية اليوم'),
                12: ('daily_hadith', self.get_random_hadith, '📚 حديث اليوم'),
                15: ('daily_tip', self.get_random_tip, '💡 نصيحة اليوم')
            }
            
            notification_type, content_func, title = content_types.get(current_hour, ('daily_dua', self.get_random_dua, '🤲 دعاء اليوم'))
            
            users = await self.get_users_with_notification_enabled(notification_type)
            content = await content_func()
            
            if not content:
                logger.warning(f"No content found for {title}")
                return
            
            # Format message based on content type
            if 'ayah' in title:
                message = (
                    f"{title}\n\n"
                    f"{content['arabic_text']}\n\n"
                    f"{content['translation_ar']}\n\n"
                    f"📖 {content['surah_name_ar']} - آية {content['ayah_number_in_surah']}"
                )
            elif 'hadith' in title:
                message = (
                    f"{title}\n\n"
                    f"{content['arabic_text']}\n\n"
                    f"{content['translation_ar']}\n\n"
                    f"👤 الراوي: {content['narrator']}\n"
                    f"⭐ الدرجة: {content['grade']}"
                )
            elif 'نصيحة' in title:
                message = (
                    f"{title}\n\n"
                    f"📌 {content['title_ar']}\n\n"
                    f"{content['content_ar']}\n\n"
                    f"📖 المرجع: {content['reference']}"
                )
            else:  # Dua
                message = (
                    f"{title}\n\n"
                    f"{content['arabic_text']}\n\n"
                    f"{content['translation_ar']}\n\n"
                    f"📖 المرجع: {content['reference']}\n"
                    f"🕐 متى يقال: {content['occasion_ar']}"
                )
            
            for user_id in users:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error sending daily content to user {user_id}: {e}")
            
            self.last_sent[cache_key] = datetime.now()
            logger.info(f"Sent {title} to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error in daily content scheduler: {e}")
    
    async def run_scheduler(self):
        """Main scheduler loop - runs every minute"""
        while True:
            try:
                current_time = datetime.now()
                
                # Check scheduled times
                if current_time.hour == 6 and current_time.minute == 0:
                    await self.send_morning_adhkar()
                
                elif current_time.hour == 17 and current_time.minute == 0:
                    await self.send_evening_adhkar()
                
                elif current_time.hour == 22 and current_time.minute == 30:
                    await self.send_night_adhkar()
                
                elif current_time.hour == 8 and current_time.minute == 0:  # Friday reminder
                    await self.send_friday_surah_kahf()
                
                # Daily content (9 AM, 12 PM, 3 PM)
                elif current_time.minute == 0 and current_time.hour in [9, 12, 15]:
                    await self.send_daily_content()
                
                # Clean old cache entries (older than 24 hours)
                cutoff_time = datetime.now().timestamp() - 86400
                self.last_sent = {
                    k: v for k, v in self.last_sent.items()
                    if v.timestamp() > cutoff_time
                }
                
                # Wait 1 minute before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)


# Global instance
notification_scheduler: Optional[NotificationScheduler] = None


def get_notification_scheduler(bot: Bot, db_session_factory) -> NotificationScheduler:
    """Get or create NotificationScheduler instance"""
    global notification_scheduler
    if notification_scheduler is None:
        notification_scheduler = NotificationScheduler(bot, db_session_factory)
    return notification_scheduler
