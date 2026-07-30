"""
Low data mode handler.
Allows users to toggle low data mode to reduce bandwidth usage.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "toggle_low_data_mode")
async def handle_toggle_low_data_mode(callback: CallbackQuery):
    """Toggle low data mode for user"""
    await callback.answer("جاري تحديث وضع توفير البيانات...")
    
    user_id = callback.from_user.id
    
    try:
        # Get current status
        current_status = await redis_client.client.get(f"low_data_mode:{user_id}")
        is_enabled = current_status == "true"
        
        # Toggle status
        new_status = not is_enabled
        await redis_client.client.set(f"low_data_mode:{user_id}", "true" if new_status else "false")
        
        # Build updated keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "✅" if new_status else "❌"
        status_text = "مفعل" if new_status else "معطل"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} وضع توفير البيانات: {status_text}",
                callback_data="toggle_low_data_mode"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        # Update message
        info_text = (
            f"📱 *وضع توفير البيانات*\n\n"
            f"الحالة: {status_text}\n\n"
            f"عند تفعيل هذا الوضع:\n"
            f"• لن يتم إرسال الصور\n"
            f"• سيتم إرسال النصوص فقط\n"
            f"• تقليل استهلاك البيانات\n\n"
            f"مفيد للاتصالات البطيئة أو محدودية البيانات."
        )
        
        await callback.message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
        logger.info(f"Low data mode toggled for user {user_id}: {new_status}")
        
    except Exception as e:
        logger.error(f"Error toggling low data mode: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "low_data_menu")
async def handle_low_data_menu(callback: CallbackQuery):
    """Show low data mode menu"""
    await callback.answer("📱 إعدادات توفير البيانات")
    
    user_id = callback.from_user.id
    
    try:
        # Get current status
        current_status = await redis_client.client.get(f"low_data_mode:{user_id}")
        is_enabled = current_status == "true"
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        status_emoji = "✅" if is_enabled else "❌"
        status_text = "مفعل" if is_enabled else "معطل"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} وضع توفير البيانات: {status_text}",
                callback_data="toggle_low_data_mode"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        info_text = (
            f"📱 *وضع توفير البيانات*\n\n"
            f"الحالة الحالية: {status_text}\n\n"
            f"عند تفعيل هذا الوضع:\n"
            f"• لن يتم إرسال الصور\n"
            f"• سيتم إرسال النصوص فقط\n"
            f"• تقليل استهلاك البيانات\n\n"
            f"مفيد للاتصالات البطيئة أو محدودية البيانات."
        )
        
        await callback.message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing low data menu: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


async def is_low_data_mode_enabled(user_id: int) -> bool:
    """
    Check if low data mode is enabled for a user.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        True if low data mode is enabled, False otherwise
    """
    try:
        status = await redis_client.client.get(f"low_data_mode:{user_id}")
        return status == "true"
    except Exception as e:
        logger.error(f"Error checking low data mode: {e}")
        return False
