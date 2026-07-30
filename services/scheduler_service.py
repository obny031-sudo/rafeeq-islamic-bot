import os
import json
import random
import logging
from typing import Optional
from urllib.parse import urlparse

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
        # 🌅 الصباح الساعة 7:00
        self.scheduler.add_job(
            func=send_morning_broadcast,
            trigger=CronTrigger(hour=7, minute=0),
            id="global_morning_adhkar",
            replace_existing=True,
        )
        # ☀️ الظهر الساعة 12:00
        self.scheduler.add_job(
            func=send_noon_broadcast,
            trigger=CronTrigger(hour=12, minute=0),
            id="global_noon_hadith",
            replace_existing=True,
        )
        # 🌆 العصر/المساء الساعة 17:00
        self.scheduler.add_job(
            func=send_evening_broadcast,
            trigger=CronTrigger(hour=17, minute=0),
            id="global_evening_adhkar",
            replace_existing=True,
        )
        # 🌙 الليل الساعة 21:00
        self.scheduler.add_job(
            func=send_night_broadcast,
            trigger=CronTrigger(hour=21, minute=0),
            id="global_night_adhkar",
            replace_existing=True,
        )

    # --- وظائف إرسال المحتوى من ملفات الـ JSON ---

async def send_morning_broadcast():
    """إرسال أذكار الصباح + آية من القرآن"""
    global _global_bot
    if not _global_bot:
        logger.warning("البوت غير معرف، متعذر إرسال الإشعار")
        return
    
    from services.content_manager import content_manager
    
    # Get random Ayah from ContentManager
    random_ayah = content_manager.get_random_ayah()
    
    text = "🌅 *صباح الخير - تذكير الصباح*\n\n"
    if random_ayah:
        text += f"📖 *آية اليوم:*\n{random_ayah.get('arabic_text', '')}\n"
        text += f"[{random_ayah.get('surah_name', '')} - آية {random_ayah.get('ayah_number', 1)}]\n\n"
    
    text += "🤲 *أذكار الصباح*\n\n"
    text += "استقبل يومك بذكر الله واطمئن قلبك.\n\n"
    text += "📚 المرجع: الأذكار النبوية"

    await _send_safe_broadcast(_global_bot, text)

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
    
    await _send_safe_broadcast(_global_bot, text)

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

    await _send_safe_broadcast(_global_bot, text)

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
        
    await _send_safe_broadcast(_global_bot, text)

async def _send_safe_broadcast(bot, text: str):
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

        for u_id in user_ids:
            try:
                # تقسيم الرسالة إذا تجاوزت الحد الأقصى لتليجرام 4096 حرف
                if len(text) > 4000:
                    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
                        await bot.send_message(chat_id=u_id, text=chunk, parse_mode="Markdown")
                else:
                    await bot.send_message(chat_id=u_id, text=text, parse_mode="Markdown")
            except Exception as exc:
                logger.error(f"فشل الإرسال للمستخدم {u_id}: {exc}")
    except Exception as exc:
        logger.error(f"خطأ في جلب قائمة المستخدمين: {exc}")


scheduler_service = SchedulerService()