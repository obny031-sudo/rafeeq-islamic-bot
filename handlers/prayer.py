from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from keyboards import get_prayer_menu_keyboard, get_main_menu_keyboard
from services.prayer_service import prayer_service
from cache.prayer_cache import PrayerCache
from utils.shared_cache import shared_cache
from config.settings import settings
import logging

router = Router()
logger = logging.getLogger(__name__)

# Initialize Prayer cache
prayer_cache = PrayerCache(shared_cache)

# Default Cairo location
DEFAULT_LATITUDE = 30.0444
DEFAULT_LONGITUDE = 31.2357
DEFAULT_TIMEZONE = "Africa/Cairo"

@router.callback_query(F.data == "prayer")
async def show_prayer_menu(callback: CallbackQuery, db: AsyncSession):
    """Show prayer module menu (inline keyboard version)"""
    await callback.answer("🕌 مواقيت الصلاة")
    
    user_id = callback.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    language = user.language.value if user else "ar"
    
    await callback.message.edit_text(
        "🕌 *الصلاة والعبادة* 🕌\n\n"
        "اختر خياراً:",
        parse_mode="Markdown",
        reply_markup=get_prayer_menu_keyboard(language)
    )


@router.callback_query(F.data == "prayer_times")
async def show_prayer_times(callback: CallbackQuery, db: AsyncSession):
    """Show current prayer times for Cairo"""
    await callback.answer("🕐 مواقيت الصلاة")
    
    try:
        logger.info("Attempting to get prayer times for Cairo")
        
        # Use Cairo coordinates as default
        latitude = 30.0444  # Cairo
        longitude = 31.2357  # Cairo
        method = 5  # Egyptian General Authority of Survey
        asr_method = 1  # Shafi
        timezone = "Africa/Cairo"
        
        prayer_data = await prayer_service.get_prayer_times(
            latitude=latitude,
            longitude=longitude,
            method=method,
            asr_method=asr_method,
            timezone=timezone
        )
        
        logger.info(f"Prayer data: {prayer_data}")
        
        if not prayer_data:
            logger.error("Prayer data is None")
            await callback.message.edit_text("❌ خطأ في حساب مواقيت الصلاة - لم يتم الحصول على البيانات")
            return
        
        timings = prayer_data.get("timings", {})
        date_info = prayer_data.get("date", {})
        
        logger.info(f"Timings: {timings}")
        
        times_text = (
            "🕐 *مواقيت الصلاة - القاهرة* 🕐\n\n"
            f"📅 التاريخ: {date_info.get('readable', 'غير متاح')}\n"
            f"📅 التقويم الهجري: {date_info.get('hijri', {}).get('date', 'غير متاح')}\n\n"
            f"🌅 الفجر: {timings.get('Fajr', 'غير متاح')}\n"
            f"☀️ الشروق: {timings.get('Sunrise', 'غير متاح')}\n"
            f"🕌 الظهر: {timings.get('Dhuhr', 'غير متاح')}\n"
            f"🌆 العصر: {timings.get('Asr', 'غير متاح')}\n"
            f"🌇 المغرب: {timings.get('Maghrib', 'غير متاح')}\n"
            f"🌙 العشاء: {timings.get('Isha', 'غير متاح')}\n\n"
            f"التوقيت: {timezone}"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 تحديث", callback_data="prayer_times"),
            InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="prayer")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            times_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting prayer times: {e}", exc_info=True)
        await callback.message.edit_text(f"❌ خطأ في حساب مواقيت الصلاة: {str(e)}")


@router.callback_query(F.data == "qibla")
async def show_qibla(callback: CallbackQuery, db: AsyncSession):
    """Show Qibla direction"""
    await callback.answer("🧭 اتجاه القبلة")
    
    try:
        qibla_data = await prayer_service.get_qibla_direction(
            latitude=DEFAULT_LATITUDE,
            longitude=DEFAULT_LONGITUDE
        )
        
        if not qibla_data:
            await callback.message.edit_text("❌ خطأ في حساب اتجاه القبلة")
            return
        
        qibla_text = (
            "🧭 *اتجاه القبلة - القاهرة* 🧭\n\n"
            f"الاتجاه: {qibla_data.get('direction', 'غير متاح')}\n"
            f"الزاوية: {qibla_data.get('degrees', 'غير متاح')}°\n\n"
            f"الموقع: القاهرة، مصر\n"
            f"إحداثيات: {DEFAULT_LATITUDE}°, {DEFAULT_LONGITUDE}°"
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 تحديث", callback_data="qibla"),
            InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="prayer")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            qibla_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting qibla direction: {e}")
        await callback.message.edit_text("❌ خطأ في حساب اتجاه القبلة")


@router.callback_query(F.data == "hijri_calendar")
async def show_hijri_calendar(callback: CallbackQuery):
    """Show Hijri calendar"""
    await callback.answer("📅 التقويم الهجري")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="prayer")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "📅 *التويم الهجري* 📅\n\n"
        "سيتم إضافة هذه الميزة قريباً.",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "prayer_method")
async def show_prayer_method(callback: CallbackQuery):
    """Show prayer calculation method"""
    await callback.answer("⚙️ طريقة الحساب")
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="prayer")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "⚙️ *طريقة حساب الصلاة* ⚙️\n\n"
        "طريقة الحساب الحالية: Egyptian General Authority of Survey\n\n"
        "سيتم إضافة المزيد من الطرق قريباً.",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


async def get_cairo_prayer_times():
    """Get prayer times for Cairo"""
    try:
        prayer_data = await prayer_service.get_prayer_times(
            latitude=DEFAULT_LATITUDE,
            longitude=DEFAULT_LONGITUDE,
            timezone=DEFAULT_TIMEZONE
        )
        return prayer_data
    except Exception as e:
        logger.error(f"Error getting Cairo prayer times: {e}")
        return None
