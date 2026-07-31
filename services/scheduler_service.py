import os
import json
import random
import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
from collections import defaultdict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from config.settings import settings

logger = logging.getLogger(__name__)

# Global bot instance for broadcast functions
_global_bot = None

# مسار مجلد البيانات
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Notification history to prevent duplicates (in-memory cache)
# Format: {user_id: {notification_type: last_sent_time}}
_notification_history = defaultdict(dict)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 15]  # seconds


def _load_json_data(filename: str, default=None):
    """قراءة بيانات JSON بأمان وسرعة من مجلد data"""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return default if default is not None else []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error(f"خطأ في قراءة الملف {filename}: {exc}")
        return default if default is not None else []


def _parse_redis_host_port() -> tuple[str, int, int]:
    parsed = urlparse(settings.REDIS_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    return host, port, settings.REDIS_SCHEDULER_DB


def _is_duplicate_notification(user_id: int, notification_type: str, cooldown_minutes: int = 60) -> bool:
    """Check if notification was already sent recently to prevent duplicates"""
    try:
        user_history = _notification_history.get(user_id, {})
        last_sent = user_history.get(notification_type)
        
        if last_sent:
            time_diff = datetime.now() - last_sent
            if time_diff < timedelta(minutes=cooldown_minutes):
                logger.info(f"Duplicate prevented: {notification_type} for user {user_id} (sent {time_diff.seconds} seconds ago)")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking duplicate notification: {e}")
        return False


def _mark_notification_sent(user_id: int, notification_type: str):
    """Mark notification as sent to prevent duplicates"""
    try:
        _notification_history[user_id][notification_type] = datetime.now()
        _cleanup_old_notifications()
    except Exception as e:
        logger.error(f"Error marking notification as sent: {e}")


def _cleanup_old_notifications():
    """Clean up notification history older than 24 hours"""
    try:
        cutoff = datetime.now() - timedelta(hours=24)
        for user_id in list(_notification_history.keys()):
            for notif_type in list(_notification_history[user_id].keys()):
                if _notification_history[user_id][notif_type] < cutoff:
                    del _notification_history[user_id][notif_type]
            # Remove empty user entries
            if not _notification_history[user_id]:
                del _notification_history[user_id]
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")


async def _send_with_retry(bot, user_id: int, text: str, notification_type: str):
    """Send message with retry mechanism"""
    for attempt in range(MAX_RETRIES):
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
            logger.info(f"Notification sent successfully: {notification_type} to user {user_id} (attempt {attempt + 1})")
            return True
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for user {user_id}: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                await asyncio.sleep(delay)
    
    logger.error(f"Failed to send notification after {MAX_RETRIES} attempts: {notification_type} to user {user_id}")
    return False


class SchedulerService:
    """محرك الإشعارات والجدولة المركزية للبوت"""

    def __init__(self):
        # Use memory jobstore instead of Redis to avoid pickling issues
        jobstores = {"default": MemoryJobStore()}
        executors = {"default": AsyncIOExecutor()}
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 3600,
        }
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )
        self._bot = None

    def set_bot(self, bot) -> None:
        self._bot = bot
        global _global_bot
        _global_bot = bot

    async def start(self):
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self._setup_global_schedules()
            logger.info("تم تشغيل محرك الإشعارات بنجاح 🚀")
        except Exception as exc:
            logger.error("فشل تشغيل محرك الإشعارات: %s", exc)
            raise

    async def shutdown(self):
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            logger.info("تم إيقاف محرك الإشعارات بنجاح")
        except Exception as exc:
            logger.error("خطأ أثناء إيقاف محرك الإشعارات: %s", exc)

    def _setup_global_schedules(self):
        """تجهيز الإشعارات التلقائية في مواعيدها المحددة للجميع"""
        # 🌅 الصباح الساعة 7:00 - أذكار الصباح
        self.scheduler.add_job(
            func=send_morning_adhkar,
            trigger=CronTrigger(hour=7, minute=0),
            id="global_morning_adhkar",
            replace_existing=True,
        )
        
        # 📖 قراءة القرآن الساعة 9:00
        self.scheduler.add_job(
            func=send_quran_reading_reminder,
            trigger=CronTrigger(hour=9, minute=0),
            id="global_quran_reading",
            replace_existing=True,
        )
        
        # 🤲 ذكر الله - سبحان الله الساعة 11:00
        self.scheduler.add_job(
            func=send_dhikr_reminder,
            trigger=CronTrigger(hour=11, minute=0),
            id="global_dhikr_morning",
            replace_existing=True,
        )
        
        # ☀️ الظهر الساعة 12:00 - حديث اليوم
        self.scheduler.add_job(
            func=send_noon_broadcast,
            trigger=CronTrigger(hour=12, minute=0),
            id="global_noon_hadith",
            replace_existing=True,
        )
        
        # 🤲 ذكر الله - الحمد لله الساعة 15:00
        self.scheduler.add_job(
            func=send_dhikr_reminder,
            trigger=CronTrigger(hour=15, minute=0),
            id="global_dhikr_afternoon",
            replace_existing=True,
        )
        
        # 🌆 العصر/المساء الساعة 17:00 - أذكار المساء
        self.scheduler.add_job(
            func=send_evening_adhkar,
            trigger=CronTrigger(hour=17, minute=0),
            id="global_evening_adhkar",
            replace_existing=True,
        )
        
        # 📖 آية عشوائية الساعة 19:00
        self.scheduler.add_job(
            func=send_random_ayah,
            trigger=CronTrigger(hour=19, minute=0),
            id="global_random_ayah",
            replace_existing=True,
        )
        
        # 🌙 الليل الساعة 21:00 - أذكار النوم
        self.scheduler.add_job(
            func=send_night_broadcast,
            trigger=CronTrigger(hour=21, minute=0),
            id="global_night_adhkar",
            replace_existing=True,
        )
        
        # 🤲 تهجد الساعة 2:00 صباحاً
        self.scheduler.add_job(
            func=send_tahajjud_reminder,
            trigger=CronTrigger(hour=2, minute=0),
            id="global_tahajjud",
            replace_existing=True,
        )
        
        # 🕌 تذكير الجمعة يوم الجمعة الساعة 11:00
        self.scheduler.add_job(
            func=send_friday_reminder,
            trigger=CronTrigger(day_of_week=5, hour=11, minute=0),  # Friday = 5
            id="global_friday_reminder",
            replace_existing=True,
        )

    # --- وظائف إرسال المحتوى من ملفات الـ JSON ---

async def send_morning_adhkar():
    """إرسال أذكار الصباح"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    text = "🌅 *أذكار الصباح*\n\n"
    text += "استيقظ بذكر الله وابدأ يومك بالأذكار:\n\n"
    text += "سُبْحَانَ اللهِ وَبِحَمْدِهِ (100 مرة)\n"
    text += "أَسْتَغْفِرُ اللَّهَ (100 مرة)\n"
    text += "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ\n\n"
    text += "📚 المرجع: الأذكار النبوية"

    await _send_safe_broadcast(_global_bot, text, notification_type="morning_adhkar")


async def send_quran_reading_reminder():
    """تذكير بقراءة القرآن"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    from services.content_manager import content_manager
    
    random_ayah = content_manager.get_random_ayah()
    
    text = "📖 *وقت القراءة*\n\n"
    text += "حان وقت قراءة القرآن الكريم\n\n"
    if random_ayah:
        text += f"آية اليوم:\n{random_ayah.get('arabic_text', '')}\n\n"
    
    text += "اقرأ ولو صفحة واحدة، فلك بكل حرف حسنة\n\n"
    text += "🤲 اللهم اجعل القرآن ربيع قلوبنا"

    await _send_safe_broadcast(_global_bot, text, notification_type="quran_reading")


async def send_dhikr_reminder():
    """تذكير بذكر الله"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    dhikrs = [
        "سُبْحَانَ اللهِ",
        "الْحَمْدُ لِلَّهِ",
        "اللَّهُ أَكْبَرُ",
        "لَا إِلَهَ إِلَّا اللَّهُ",
        "أَسْتَغْفِرُ اللَّهَ"
    ]
    
    import random
    selected_dhikr = random.choice(dhikrs)
    
    text = "🤲 *ذكر الله*\n\n"
    text += f"اذكر الله بقولك: {selected_dhikr}\n\n"
    text += "فَذِكْرُ اللَّهِ أَكْبَرُ\n\n"
    text += "💡 قُلْهَا 33 مرة"

    await _send_safe_broadcast(_global_bot, text, notification_type="dhikr_reminder")


async def send_evening_adhkar():
    """إرسال أذكار المساء"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    text = "� *أذكار المساء*\n\n"
    text += "اختم يومك بذكر الله:\n\n"
    text += "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ (3 مرات)\n"
    text += "اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا\n"
    text += "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ\n\n"
    text += "📚 المرجع: الأذكار النبوية"

    await _send_safe_broadcast(_global_bot, text, notification_type="evening_adhkar")


async def send_random_ayah():
    """إرسال آية عشوائية"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    from services.content_manager import content_manager
    
    random_ayah = content_manager.get_random_ayah()
    
    text = "📖 *آية من القرآن*\n\n"
    if random_ayah:
        text += f"{random_ayah.get('arabic_text', '')}\n\n"
        text += f"[{random_ayah.get('surah_name', '')} - آية {random_ayah.get('ayah_number', 1)}]\n\n"
    
    text += "تدبر في معاني الآية وعمل بها"

    await _send_safe_broadcast(_global_bot, text, notification_type="random_ayah")


async def send_tahajjud_reminder():
    """تذكير بصلاة التهجد"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    text = "🤲 *تذكير التهجد*\n\n"
    text += "قُمْ لِصَلَاةِ التَّهَجُدِ\n\n"
    text += "أَفَلَا يَتَدَبَّرُونَ الْقُرْآنَ أَمْ عَلَى قُلُوبٍ أَقْفَالُهَا\n\n"
    text += "اللَّهُمَّ أَعِنِّي عَلَى قِيَامِ اللَّيْلِ"

    await _send_safe_broadcast(_global_bot, text, notification_type="tahajjud_reminder")


async def send_friday_reminder():
    """تذكير يوم الجمعة"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    text = "🕌 *تذكير الجمعة*\n\n"
    text += "يَوْمُ الْجُمُعَةِ يَوْمُ عِيدٍ\n\n"
    text += "� اغتسل وتطيب وصلِ الجمعة\n\n"
    text += "أَكْثِرُوا مِنَ الصَّلَاةِ عَلَيَّ يَوْمَ الْجُمُعَةِ\n\n"
    text += "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ"

    await _send_safe_broadcast(_global_bot, text, notification_type="friday_reminder")

async def send_noon_broadcast():
    """إرسال حديث اليوم"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    from services.content_manager import content_manager
    
    # Get random Hadith from ContentManager
    hadith = content_manager.get_hadith(random=True)
    if not hadith:
        return

    text = (
        f"☀️ *حديث اليوم*\n\n"
        f"📚 {hadith.get('arabic_text', '')}\n\n"
    )
    
    if hadith.get('translation_ar'):
        text += f"📝 {hadith.get('translation_ar', '')}\n\n"
    
    if hadith.get('collection'):
        text += f"المصدر: {hadith.get('collection', '')}"
    if hadith.get('hadith_number'):
        text += f" - #{hadith.get('hadith_number', '')}"
    
    await _send_safe_broadcast(_global_bot, text, notification_type="noon_hadith")

async def send_evening_broadcast():
    """إرسال أذكار المساء + نصيحة اليوم"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    from services.content_manager import content_manager
    
    # Get random Ayah for evening wisdom
    random_ayah = content_manager.get_random_ayah()
    
    text = "🌆 *مساء الخير - أذكار المساء*\n\n"
    if random_ayah:
        text += f"💡 *نصيحة اليوم:*\n{random_ayah.get('arabic_text', '')}\n\n"

    text += "🌙 *أذكار المساء*\n\n"
    text += "اختم يومك بذكر الله واطمئن قلبك.\n\n"
    text += "📚 المرجع: الأذكار النبوية"

    await _send_safe_broadcast(_global_bot, text, notification_type="evening_adhkar")

async def send_night_broadcast():
    """إرسال أذكار النوم + دعاء اليوم"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    from services.content_manager import content_manager
    
    # Get random Hadith for night dua
    hadith = content_manager.get_hadith(random=True)
    
    text = "🌙 *طاب مساؤكم - أذكار النوم*\n\n"
    if hadith:
        text += f"🤲 *دعاء اليوم:*\n{hadith.get('arabic_text', '')}\n\n"

    text += "😴 *أذكار النوم*\n\n"
    text += "احفظك الله ويرعاك.\n\n"
    text += "🛏️ تصبحون على خير."
        
    await _send_safe_broadcast(_global_bot, text, notification_type="night_adhkar")

async def _send_safe_broadcast(bot, text: str, notification_type: str = "broadcast"):
    """إرسال الإشعار لجميع المستخدمين المسجلين في قاعدة البيانات"""
    if not bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return

    try:
        from config.database import AsyncSessionLocal
        from sqlalchemy import select
        from models.user import User

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.id).where(User.is_banned == False)
            )
            user_ids = result.scalars().all()

        success_count = 0
        failure_count = 0
        
        for u_id in user_ids:
            try:
                # Check for duplicate
                if _is_duplicate_notification(u_id, notification_type, cooldown_minutes=60):
                    logger.info(f"Skipping duplicate notification for user {u_id}")
                    continue
                
                # تقسيم الرسالة إذا تجاوزت الحد الأقصى لتليجرام 4096 حرف
                message_text = text
                if len(text) > 4000:
                    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                    for chunk in chunks:
                        success = await _send_with_retry(bot, u_id, chunk, notification_type)
                        if success:
                            success_count += 1
                        else:
                            failure_count += 1
                else:
                    success = await _send_with_retry(bot, u_id, text, notification_type)
                    if success:
                        success_count += 1
                        _mark_notification_sent(u_id, notification_type)
                    else:
                        failure_count += 1
                        
            except Exception as exc:
                logger.error(f"فشل الإرسال للمستخدم {u_id}: {exc}")
                failure_count += 1
        
        logger.info(f"Broadcast completed: {success_count} sent, {failure_count} failed")
        
    except Exception as exc:
        logger.error(f"خطأ في جلب قائمة المستخدمين: {exc}")


scheduler_service = SchedulerService()