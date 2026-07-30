"""User settings handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from keyboards import get_main_menu_keyboard
from models.user import User

router = Router()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery, db: AsyncSession):
    """Show user settings menu (inline keyboard version)"""
    await callback.answer("⚙️ الإعدادات")
    
    user_id = callback.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    prayer_on = user.prayer_notifications_enabled if user else True
    wird_on = user.daily_wird_enabled if user else True
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 اللغة: العربية", callback_data="settings_language")
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if prayer_on else '❌'} تذكير الصلاة",
            callback_data="settings_prayer_notifications",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if wird_on else '❌'} الوِرد اليومي",
            callback_data="settings_daily_wird",
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
    
    await callback.message.edit_text(
        "⚙️ *الإعدادات* ⚙️\n\n"
        "تخصيص تجربتك مع البوت:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "settings_language")
async def toggle_language(callback: CallbackQuery, db: AsyncSession):
    """Toggle interface language"""
    await callback.answer("🌐 اللغة محددة على العربية فقط")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 العودة للإعدادات", callback_data="settings"))
    
    await callback.message.edit_text(
        "🌐 *اللغة*\n\n"
        "اللغة محددة حالياً على العربية فقط.\n"
        "سيتم إضافة المزيد من اللغات قريباً.",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "settings_prayer_notifications")
async def toggle_prayer_notifications(callback: CallbackQuery, db: AsyncSession):
    """Toggle prayer notification preference"""
    await callback.answer("🔔 تفعيل/تعطيل تذكير الصلاة")
    
    user_id = callback.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        user.prayer_notifications_enabled = not user.prayer_notifications_enabled
        await db.commit()
    
    # Refresh settings menu to show updated status
    prayer_on = user.prayer_notifications_enabled if user else True
    wird_on = user.daily_wird_enabled if user else True
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 اللغة: العربية", callback_data="settings_language")
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if prayer_on else '❌'} تذكير الصلاة",
            callback_data="settings_prayer_notifications",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if wird_on else '❌'} الوِرد اليومي",
            callback_data="settings_daily_wird",
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
    
    await callback.message.edit_text(
        "⚙️ *الإعدادات* ⚙️\n\n"
        "تخصيص تجربتك مع البوت:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "settings_daily_wird")
async def toggle_daily_wird(callback: CallbackQuery, db: AsyncSession):
    """Toggle daily wird (Adhkar) reminder preference"""
    await callback.answer("📅 تفعيل/تعطيل الوِرد اليومي")
    
    user_id = callback.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        user.daily_wird_enabled = not user.daily_wird_enabled
        await db.commit()
    
    # Refresh settings menu to show updated status
    prayer_on = user.prayer_notifications_enabled if user else True
    wird_on = user.daily_wird_enabled if user else True
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 اللغة: العربية", callback_data="settings_language")
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if prayer_on else '❌'} تذكير الصلاة",
            callback_data="settings_prayer_notifications",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if wird_on else '❌'} الوِرد اليومي",
            callback_data="settings_daily_wird",
        )
    )
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
    
    await callback.message.edit_text(
        "⚙️ *الإعدادات* ⚙️\n\n"
        "تخصيص تجربتك مع البوت:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


