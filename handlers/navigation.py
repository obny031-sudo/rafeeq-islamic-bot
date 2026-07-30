"""
Navigation handlers for unified back button and main menu.
Provides consistent navigation across all bot sections.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from services.content_manager import content_manager
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "go_main_menu")
async def handle_main_menu(callback: CallbackQuery, db: AsyncSession):
    """Handle main menu navigation callback - returns to actual main menu"""
    await callback.answer("🔙 العودة للقائمة الرئيسية")
    
    try:
        user_id = callback.from_user.id
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text(
                "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
                reply_markup=get_main_menu_keyboard("ar", user_id)
            )
            return
        
        # Get user's name
        name = user.first_name or "صديقي"
        
        welcome_text = (
            f"مرحبًا بعودتك، {name}! 🌟\n\n"
            "تابع رحلتك الروحانية معنا. "
            "بارك الله في جهودك.\n\n"
            "اختر القسم الذي تود استكشافه:"
        )
        
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard("ar", user_id)
        )
        
    except Exception as e:
        logger.error(f"Error handling main menu navigation: {e}")


@router.callback_query(F.data == "quran_menu")
async def handle_quran_menu(callback: CallbackQuery):
    """Handle Quran menu callback"""
    await callback.answer("📖 القائمة القرآنية")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📜 قراءة السور", callback_data="quran_surah_list"),
        InlineKeyboardButton(text="🔍 البحث في القرآن", callback_data="quran_search")
    )
    builder.row(
        InlineKeyboardButton(text="📍 موضع القراءة الأخير", callback_data="quran_last_position"),
        InlineKeyboardButton(text="📖 الأجزاء", callback_data="quran_juz")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "📖 *القرآن الكريم*\n\nاختر خياراً:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "hadith_menu")
async def handle_hadith_menu(callback: CallbackQuery):
    """Handle Hadith menu callback"""
    await callback.answer("📚 القائمة الحديثية")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 البحث في الأحاديث", callback_data="hadith_search"),
        InlineKeyboardButton(text="📚 صحيح البخاري", callback_data="hadith_bukhari")
    )
    builder.row(
        InlineKeyboardButton(text="📖 صحيح مسلم", callback_data="hadith_muslim"),
        InlineKeyboardButton(text="📜 سنن الترمذي", callback_data="hadith_tirmidhi")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "📚 *الأحاديث النبوية الشريفة*\n\nاختر مجموعة:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "adhkar_menu")
async def handle_adhkar_menu(callback: CallbackQuery):
    """Handle Adhkar menu callback"""
    await callback.answer("🤲 قائمة الأذكار")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌅 أذكار الصباح", callback_data="adhkar_morning"),
        InlineKeyboardButton(text="🌙 أذكار المساء", callback_data="adhkar_evening")
    )
    builder.row(
        InlineKeyboardButton(text="😴 أذكار النوم", callback_data="adhkar_sleep"),
        InlineKeyboardButton(text="🤲 أذكار عامة", callback_data="adhkar_general")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "🤲 *الأذكار*\n\nاختر نوع الأذكار:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "prayer_menu")
async def handle_prayer_menu(callback: CallbackQuery):
    """Handle Prayer menu callback"""
    await callback.answer("🕐 قائمة الصلاة")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🕐 مواقيت الصلاة", callback_data="prayer_times"),
        InlineKeyboardButton(text="🧭 اتجاه القبلة", callback_data="qibla_direction")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "🕐 *مواقيت الصلاة*\n\nاختر خياراً:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "tasbeeh_menu")
async def handle_tasbeeh_menu(callback: CallbackQuery):
    """Handle Tasbeeh menu callback"""
    await callback.answer("📿 المسبحة")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📿 بدء التسبيح (0)", callback_data="tasbeeh_start")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "📿 *المسبحة الإلكترونية*\n\n"
        "اضغط على الزر للبدء بالتسبيح",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
