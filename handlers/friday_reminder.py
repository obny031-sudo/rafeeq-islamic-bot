"""
Friday Surah Al-Kahf reminder handler.
Sends automatic reminders on Friday to read Surah Al-Kahf.
"""

import logging
import httpx
from datetime import datetime
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

# API endpoint
QURAN_API_BASE = "http://api.alquran.cloud/v1"


async def get_surah_al_kahf() -> dict:
    """
    Get Surah Al-Kahf (Surah 18) from the Quran API.
    
    Returns:
        Dictionary with Surah data
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{QURAN_API_BASE}/surah/18"
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 200:
                return data.get("data", {})
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting Surah Al-Kahf: {e}")
        return None


async def send_friday_reminder(user_id: int, bot=None):
    """
    Send Friday Surah Al-Kahf reminder to a user.
    
    Args:
        user_id: Telegram user ID
        bot: Bot instance
    """
    if not bot:
        return
    
    try:
        # Check if today is Friday
        today = datetime.now().strftime("%A")
        
        if today.lower() != "friday":
            logger.info(f"Today is not Friday, skipping reminder for user {user_id}")
            return
        
        # Get Surah Al-Kahf data
        surah_data = await get_surah_al_kahf()
        
        if surah_data:
            surah_info = surah_data.get("surah", {})
            surah_name = surah_info.get("name", "الكهف")
            ayahs = surah_data.get("ayahs", [])
            
            # Build reminder message
            text = (
                f"🕌 *تذكير يوم الجمعة*\n\n"
                f"📖 *سورة الكهف*\n\n"
                f"عن أبي الدرداء رضي الله عنه قال: قال رسول الله صلى الله عليه وسلم:\n"
                f"«مَنْ حَفِظَ عَشْرَ آيَاتٍ مِنْ أَوَّلِ سُورَةِ الْكَهْفِ عُصِمَ مِنَ الدَّجَّالِ»\n\n"
                f"📚 رواه مسلم\n\n"
                f"عدد الآيات: {len(ayahs)}\n\n"
                f"🤲 اقرأ سورة الكهف يوم الجمعة للحماية من الفتن.\n\n"
                f"يمكنك قراءة السورة الكاملة من خلال قائمة القرآن."
            )
            
            await bot.send_message(user_id, text, parse_mode="Markdown")
            logger.info(f"Sent Friday Surah Al-Kahf reminder to user {user_id}")
        else:
            logger.error(f"Failed to get Surah Al-Kahf for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error sending Friday reminder to user {user_id}: {e}")


@router.callback_query(F.data == "toggle_friday_reminder")
async def handle_toggle_friday_reminder(callback: CallbackQuery, db: AsyncSession):
    """Toggle Friday reminder for user"""
    await callback.answer("جاري تحديث إعدادات تذكير الجمعة")
    
    user_id = callback.from_user.id
    
    try:
        # Get current status
        current_status = await redis_client.client.get(f"friday_reminder:{user_id}")
        is_enabled = current_status == "true"
        
        # Toggle status
        new_status = not is_enabled
        await redis_client.client.set(f"friday_reminder:{user_id}", "true" if new_status else "false")
        
        # Build updated keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "✅" if new_status else "❌"
        status_text = "مفعل" if new_status else "معطل"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} تذكير الجمعة: {status_text}",
                callback_data="toggle_friday_reminder"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        # Update message
        info_text = (
            f"🕌 *تذكير سورة الكهف يوم الجمعة*\n\n"
            f"الحالة: {status_text}\n\n"
            f"عن أبي الدرداء رضي الله عنه قال: قال رسول الله صلى الله عليه وسلم:\n"
            f"«مَنْ حَفِظَ عَشْرَ آيَاتٍ مِنْ أَوَّلِ سُورَةِ الْكَهْفِ عُصِمَ مِنَ الدَّجَّالِ»\n\n"
            f"📚 رواه مسلم\n\n"
            f"عند تفعيل هذا التذكير:\n"
            f"• ستصلك رسالة تذكير كل يوم جمعة\n"
            f"• تذكير بأهمية قراءة سورة الكهف\n"
            f"• نص الحديث الشريف\n\n"
            f"التذكير يُرسل صباح يوم الجمعة."
        )
        
        await callback.message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
        logger.info(f"Friday reminder toggled for user {user_id}: {new_status}")
        
    except Exception as e:
        logger.error(f"Error toggling Friday reminder: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "friday_reminder_menu")
async def handle_friday_reminder_menu(callback: CallbackQuery, db: AsyncSession):
    """Show Friday reminder menu"""
    await callback.answer("🕌 إعدادات تذكير الجمعة")
    
    user_id = callback.from_user.id
    
    try:
        # Get current status
        current_status = await redis_client.client.get(f"friday_reminder:{user_id}")
        is_enabled = current_status == "true"
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "✅" if is_enabled else "❌"
        status_text = "مفعل" if is_enabled else "معطل"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} تذكير الجمعة: {status_text}",
                callback_data="toggle_friday_reminder"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        info_text = (
            f"🕌 *تذكير سورة الكهف يوم الجمعة*\n\n"
            f"الحالة الحالية: {status_text}\n\n"
            f"عن أبي الدرداء رضي الله عنه قال: قال رسول الله صلى الله عليه وسلم:\n"
            f"«مَنْ حَفِظَ عَشْرَ آيَاتٍ مِنْ أَوَّلِ سُورَةِ الْكَهْفِ عُصِمَ مِنَ الدَّجَّالِ»\n\n"
            f"📚 رواه مسلم\n\n"
            f"عند تفعيل هذا التذكير:\n"
            f"• ستصلك رسالة تذكير كل يوم جمعة\n"
            f"• تذكير بأهمية قراءة سورة الكهف\n"
            f"• نص الحديث الشريف\n\n"
            f"التذكير يُرسل صباح يوم الجمعة."
        )
        
        await callback.message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing Friday reminder menu: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


async def is_friday_reminder_enabled(user_id: int) -> bool:
    """
    Check if Friday reminder is enabled for a user.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        True if enabled, False otherwise
    """
    try:
        status = await redis_client.client.get(f"friday_reminder:{user_id}")
        return status == "true"
    except Exception as e:
        logger.error(f"Error checking Friday reminder status: {e}")
        return False


async def send_friday_reminders_to_all_enabled_users(bot=None):
    """
    Send Friday reminders to all users who have enabled it.
    
    Args:
        bot: Bot instance
    """
    if not bot:
        return
    
    try:
        # Check if today is Friday
        today = datetime.now().strftime("%A")
        
        if today.lower() != "friday":
            logger.info("Today is not Friday, skipping mass Friday reminders")
            return
        
        # Get all users with Friday reminder enabled
        # This would require scanning all users or maintaining a separate list
        # For now, we'll implement a simpler approach
        logger.info("Friday reminder mass send would be implemented here")
        
    except Exception as e:
        logger.error(f"Error sending Friday reminders to all users: {e}")
