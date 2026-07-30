"""
Customizable Adhkar timings handler.
Allows users to customize when they receive Adhkar reminders.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()

# FSM States for Adhkar timing customization
class AdhkarTimingStates(StatesGroup):
    waiting_for_morning_time = State()
    waiting_for_evening_time = State()
    waiting_for_sleep_time = State()


@router.callback_query(F.data == "customize_adhkar_timings")
async def handle_customize_adhkar_timings(callback: CallbackQuery, db: AsyncSession):
    """Show Adhkar timing customization menu"""
    await callback.answer("⏰ إعداد مواعيد الأذكار")
    
    user_id = callback.from_user.id
    
    try:
        # Get current user timings
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("❌ لم يتم العثور على المستخدم", show_alert=True)
            return
        
        # Get current timings from Redis or database
        morning_time = await redis_client.client.get(f"adhkar_morning_time:{user_id}") or "07:00"
        evening_time = await redis_client.client.get(f"adhkar_evening_time:{user_id}") or "18:00"
        sleep_time = await redis_client.client.get(f"adhkar_sleep_time:{user_id}") or "22:00"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=f"🌅 الصباح: {morning_time}", callback_data="set_morning_time")
        )
        builder.row(
            InlineKeyboardButton(text=f"🌙 المساء: {evening_time}", callback_data="set_evening_time")
        )
        builder.row(
            InlineKeyboardButton(text=f"😴 النوم: {sleep_time}", callback_data="set_sleep_time")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            "⏰ *إعداد مواعيد الأذكار*\n\n"
            "اختر الوقت المناسب لكل نوع من الأذكار:\n\n"
            "سيتم إرسال التذكيرات في الأوقات التي تحددها.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing Adhkar timing menu: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data == "set_morning_time")
async def handle_set_morning_time(callback: CallbackQuery, state: FSMContext):
    """Start morning time setting"""
    await callback.answer("🌅 إعداد وقت الصباح")
    
    await state.set_state(AdhkarTimingStates.waiting_for_morning_time)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 إلغاء", callback_data="customize_adhkar_timings")
    )
    
    await callback.message.edit_text(
        "🌅 *إعداد وقت أذكار الصباح*\n\n"
        "يرجى إرسال الوقت بصيغة 24 ساعة:\n"
        "مثال: 07:00، 06:30، 08:00\n\n"
        "الوقت الحالي: 07:00",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "set_evening_time")
async def handle_set_evening_time(callback: CallbackQuery, state: FSMContext):
    """Start evening time setting"""
    await callback.answer("🌙 إعداد وقت المساء")
    
    await state.set_state(AdhkarTimingStates.waiting_for_evening_time)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 إلغاء", callback_data="customize_adhkar_timings")
    )
    
    await callback.message.edit_text(
        "🌙 *إعداد وقت أذكار المساء*\n\n"
        "يرجى إرسال الوقت بصيغة 24 ساعة:\n"
        "مثال: 18:00، 17:30، 19:00\n\n"
        "الوقت الحالي: 18:00",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "set_sleep_time")
async def handle_set_sleep_time(callback: CallbackQuery, state: FSMContext):
    """Start sleep time setting"""
    await callback.answer("😴 إعداد وقت النوم")
    
    await state.set_state(AdhkarTimingStates.waiting_for_sleep_time)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 إلغاء", callback_data="customize_adhkar_timings")
    )
    
    await callback.message.edit_text(
        "😴 *إعداد وقت أذكار النوم*\n\n"
        "يرجى إرسال الوقت بصيغة 24 ساعة:\n"
        "مثال: 22:00، 21:30، 23:00\n\n"
        "الوقت الحالي: 22:00",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


async def validate_time_format(time_str: str) -> bool:
    """Validate time format (HH:MM)"""
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return False
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except:
        return False


@router.callback_query(AdhkarTimingStates.waiting_for_morning_time)
async def handle_morning_time_input(callback: CallbackQuery, state: FSMContext):
    """Handle morning time input (if sent via callback from inline keyboard)"""
    await callback.answer()
    # This is a placeholder - actual time input comes via message


@router.message(AdhkarTimingStates.waiting_for_morning_time)
async def handle_morning_time_message(message: Message, state: FSMContext):
    """Handle morning time input via message"""
    time_str = message.text.strip()
    
    if not await validate_time_format(time_str):
        await message.answer("❌ صيغة الوقت غير صحيحة. يرجى استخدام صيغة HH:MM (مثال: 07:00)")
        return
    
    user_id = message.from_user.id
    
    # Save to Redis
    await redis_client.client.set(f"adhkar_morning_time:{user_id}", time_str)
    
    # Update scheduler
    from services.scheduler_service import scheduler_service
    scheduler_service.update_adhkar_time(user_id, "morning", time_str)
    
    await message.answer(
        f"✅ تم تحديث وقت أذكار الصباح إلى {time_str}\n\n"
        f"ستتلقى تذكير أذكار الصباح يومياً في هذا الوقت."
    )
    
    await state.clear()


@router.message(AdhkarTimingStates.waiting_for_evening_time)
async def handle_evening_time_message(message: Message, state: FSMContext):
    """Handle evening time input via message"""
    time_str = message.text.strip()
    
    if not await validate_time_format(time_str):
        await message.answer("❌ صيغة الوقت غير صحيحة. يرجى استخدام صيغة HH:MM (مثال: 18:00)")
        return
    
    user_id = message.from_user.id
    
    # Save to Redis
    await redis_client.client.set(f"adhkar_evening_time:{user_id}", time_str)
    
    # Update scheduler
    from services.scheduler_service import scheduler_service
    scheduler_service.update_adhkar_time(user_id, "evening", time_str)
    
    await message.answer(
        f"✅ تم تحديث وقت أذكار المساء إلى {time_str}\n\n"
        f"ستتلقى تذكير أذكار المساء يومياً في هذا الوقت."
    )
    
    await state.clear()


@router.message(AdhkarTimingStates.waiting_for_sleep_time)
async def handle_sleep_time_message(message: Message, state: FSMContext):
    """Handle sleep time input via message"""
    time_str = message.text.strip()
    
    if not await validate_time_format(time_str):
        await message.answer("❌ صيغة الوقت غير صحيحة. يرجى استخدام صيغة HH:MM (مثال: 22:00)")
        return
    
    user_id = message.from_user.id
    
    # Save to Redis
    await redis_client.client.set(f"adhkar_sleep_time:{user_id}", time_str)
    
    # Update scheduler
    from services.scheduler_service import scheduler_service
    scheduler_service.update_adhkar_time(user_id, "sleep", time_str)
    
    await message.answer(
        f"✅ تم تحديث وقت أذكار النوم إلى {time_str}\n\n"
        f"ستتلقى تذكير أذكار النوم يومياً في هذا الوقت."
    )
    
    await state.clear()


async def get_user_adhkar_timings(user_id: int) -> dict:
    """
    Get user's customized Adhkar timings.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        Dictionary with timing data
    """
    try:
        morning_time = await redis_client.client.get(f"adhkar_morning_time:{user_id}") or "07:00"
        evening_time = await redis_client.client.get(f"adhkar_evening_time:{user_id}") or "18:00"
        sleep_time = await redis_client.client.get(f"adhkar_sleep_time:{user_id}") or "22:00"
        
        return {
            "morning": morning_time,
            "evening": evening_time,
            "sleep": sleep_time
        }
    except Exception as e:
        logger.error(f"Error getting user Adhkar timings: {e}")
        return {
            "morning": "07:00",
            "evening": "18:00",
            "sleep": "22:00"
        }
