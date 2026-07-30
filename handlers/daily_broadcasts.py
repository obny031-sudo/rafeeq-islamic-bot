"""
Daily broadcasts handler.
Manages scheduled daily Ayah and wisdom broadcasts to users.
"""

import logging
import random
import httpx
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()

# API endpoints
QURAN_API_BASE = "http://api.alquran.cloud/v1"

# Wisdom/Hadith collection
WISDOM_COLLECTION = [
    {
        "arabic": "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ",
        "translation": "The best among you are those who learn the Quran and teach it",
        "source": "البخاري"
    },
    {
        "arabic": "مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ بِهِ طَرِيقًا إِلَى الْجَنَّةِ",
        "translation": "Whoever follows a path in search of knowledge, Allah will make easy for him a path to Paradise",
        "source": "مسلم"
    },
    {
        "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
        "translation": "Actions are judged by intentions",
        "source": "البخاري"
    },
    {
        "arabic": "الدِّينُ النَّصِيحَةُ",
        "translation": "Religion is sincerity",
        "source": "مسلم"
    },
    {
        "arabic": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ лِسَانِهِ وَيَدِهِ",
        "translation": "A Muslim is one from whose tongue and hand other Muslims are safe",
        "source": "البخاري"
    },
    {
        "arabic": "الْمُؤْمِنُ الْقَوِيُّ خَيْرٌ وَأَحَبُّ إِلَى اللَّهِ مِنَ الْمُؤْمِنِ الضَّعِيفِ",
        "translation": "The strong believer is better and more beloved to Allah than the weak believer",
        "source": "مسلم"
    },
    {
        "arabic": "لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ",
        "translation": "None of you truly believes until he loves for his brother what he loves for himself",
        "source": "البخاري"
    },
    {
        "arabic": "الْجَنَّةُ تَحْتَ أَقْدَامِ الْأُمَّهَاتِ",
        "translation": "Paradise lies at the feet of mothers",
        "source": "النسائي"
    }
]


async def get_random_ayah() -> dict:
    """
    Get a random Ayah from the Quran.
    
    Returns:
        Dictionary with Ayah data
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get a random Surah (1-114)
            surah_number = random.randint(1, 114)
            
            # Get a random Ayah from that Surah
            url = f"{QURAN_API_BASE}/surah/{surah_number}"
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 200:
                surah_data = data.get("data", {})
                ayahs = surah_data.get("ayahs", [])
                
                if ayahs:
                    # Get a random Ayah
                    ayah = random.choice(ayahs)
                    
                    return {
                        "surah_number": surah_number,
                        "surah_name": surah_data.get("englishName", ""),
                        "ayah_number": ayah.get("numberInSurah"),
                        "text": ayah.get("text", "")
                    }
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting random Ayah: {e}")
        return None


async def get_random_wisdom() -> dict:
    """
    Get a random wisdom/hadith from the collection.
    
    Returns:
        Dictionary with wisdom data
    """
    return random.choice(WISDOM_COLLECTION)


async def send_daily_ayah(user_id: int, bot=None):
    """
    Send daily Ayah to a user.
    
    Args:
        user_id: Telegram user ID
        bot: Bot instance
    """
    if not bot:
        return
    
    try:
        ayah_data = await get_random_ayah()
        
        if ayah_data:
            text = (
                f"📖 *آية اليوم*\n\n"
                f"سورة {ayah_data['surah_name']}، آية {ayah_data['ayah_number']}\n\n"
                f"{ayah_data['text']}\n\n"
                f"🤲 وَذَكِّرْ فَإِنَّ الذِّكْرَى تَنْفَعُ الْمُؤْمِنِينَ"
            )
            
            await bot.send_message(user_id, text, parse_mode="Markdown")
            logger.info(f"Sent daily Ayah to user {user_id}")
        else:
            logger.error(f"Failed to get Ayah for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error sending daily Ayah to user {user_id}: {e}")


async def send_daily_wisdom(user_id: int, bot=None):
    """
    Send daily wisdom/hadith to a user.
    
    Args:
        user_id: Telegram user ID
        bot: Bot instance
    """
    if not bot:
        return
    
    try:
        wisdom_data = await get_random_wisdom()
        
        if wisdom_data:
            text = (
                f"💎 *حكمة اليوم*\n\n"
                f"{wisdom_data['arabic']}\n\n"
                f"📝 {wisdom_data['translation']}\n\n"
                f"📚 المصدر: {wisdom_data['source']}"
            )
            
            await bot.send_message(user_id, text, parse_mode="Markdown")
            logger.info(f"Sent daily wisdom to user {user_id}")
        else:
            logger.error(f"Failed to get wisdom for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error sending daily wisdom to user {user_id}: {e}")


@router.callback_query(F.data == "toggle_daily_broadcasts")
async def handle_toggle_daily_broadcasts(callback: CallbackQuery, db: AsyncSession):
    """Toggle daily broadcasts for user"""
    await callback.answer("جاري تحديث الإعدادات...")
    
    user_id = callback.from_user.id
    
    try:
        # Get current status
        current_status = await redis_client.client.get(f"daily_broadcasts:{user_id}")
        is_enabled = current_status == "true"
        
        # Toggle status
        new_status = not is_enabled
        await redis_client.client.set(f"daily_broadcasts:{user_id}", "true" if new_status else "false")
        
        # Update database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.daily_wird_enabled = new_status
            await db.commit()
            
            # Update scheduler
            from services.scheduler_service import scheduler_service
            if new_status:
                scheduler_service.add_user_to_all_daily_jobs(user_id)
            else:
                scheduler_service.remove_user_from_all_daily_jobs(user_id)
        
        # Build updated keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "✅" if new_status else "❌"
        status_text = "مفعل" if new_status else "معطل"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} البث اليومي: {status_text}",
                callback_data="toggle_daily_broadcasts"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        # Update message
        info_text = (
            f"📢 *البث اليومي*\n\n"
            f"الحالة: {status_text}\n\n"
            f"عند تفعيل هذه الميزة:\n"
            f"• آية يومية من القرآن الكريم\n"
            f"• حكمة أو حديث يومي\n"
            f"• نصائح روحانية\n\n"
            f"ستصلك هذه المحتويات تلقائياً كل يوم."
        )
        
        await callback.message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
        logger.info(f"Daily broadcasts toggled for user {user_id}: {new_status}")
        
    except Exception as e:
        logger.error(f"Error toggling daily broadcasts: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "daily_broadcasts_menu")
async def handle_daily_broadcasts_menu(callback: CallbackQuery, db: AsyncSession):
    """Show daily broadcasts menu"""
    await callback.answer("📢 إعدادات البث اليومي")
    
    user_id = callback.from_user.id
    
    try:
        # Get current status
        current_status = await redis_client.client.get(f"daily_broadcasts:{user_id}")
        is_enabled = current_status == "true"
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "✅" if is_enabled else "❌"
        status_text = "مفعل" if is_enabled else "معطل"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} البث اليومي: {status_text}",
                callback_data="toggle_daily_broadcasts"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        info_text = (
            f"📢 *البث اليومي*\n\n"
            f"الحالة الحالية: {status_text}\n\n"
            f"عند تفعيل هذه الميزة:\n"
            f"• آية يومية من القرآن الكريم\n"
            f"• حكمة أو حديث يومي\n"
            f"• نصائح روحانية\n\n"
            f"ستصلك هذه المحتويات تلقائياً كل يوم."
        )
        
        await callback.message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing daily broadcasts menu: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


async def is_daily_broadcasts_enabled(user_id: int) -> bool:
    """
    Check if daily broadcasts are enabled for a user.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        True if enabled, False otherwise
    """
    try:
        status = await redis_client.client.get(f"daily_broadcasts:{user_id}")
        return status == "true"
    except Exception as e:
        logger.error(f"Error checking daily broadcasts status: {e}")
        return False
