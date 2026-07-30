"""
Digital Tasbeeh counter handler - Ultimate Version.
Interactive inline button counter for dhikr/tesbih with advanced features.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from models.user import User
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()

# FSM States for custom dhikr input
class TasbeehStates(StatesGroup):
    waiting_for_custom_dhikr = State()

# Preset dhikr options with emoji colors
PRESET_DHIKR = {
    "subhanallah": {
        "text": "سبحان الله",
        "emoji": "🟢",
        "color": "green"
    },
    "alhamdulillah": {
        "text": "الحمد لله",
        "emoji": "🔵",
        "color": "blue"
    },
    "la_ilaha_illallah": {
        "text": "لا إله إلا الله",
        "emoji": "🟡",
        "color": "yellow"
    },
    "allahu_akbar": {
        "text": "الله أكبر",
        "emoji": "🔴",
        "color": "red"
    },
    "astaghfirullah": {
        "text": "أستغفر الله واتوب إليه",
        "emoji": "🟣",
        "color": "purple"
    },
    "salawat": {
        "text": "الصلاة على النبي",
        "emoji": "🟠",
        "color": "orange"
    }
}

# Target options
TARGETS = {
    "33": 33,
    "100": 100,
    "1000": 1000,
    "unlimited": None
}


@router.callback_query(F.data == "tasbeeh")
async def handle_tasbeeh_menu(callback: CallbackQuery, db: AsyncSession):
    """Show tasbeeh menu from main menu"""
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


@router.callback_query(F.data == "tasbeeh_start")
async def handle_tasbeeh_start(callback: CallbackQuery, db: AsyncSession):
    """Start tasbeeh counter with menu"""
    await callback.answer("📿 بدء التسبيح")
    
    user_id = callback.from_user.id
    
    # Get user data for stats
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    # Initialize counter in Redis with atomic increment
    await redis_client.client.set(f"tasbeeh:{user_id}:count", 0)
    await redis_client.client.set(f"tasbeeh:{user_id}:dhikr", "subhanallah")
    await redis_client.client.set(f"tasbeeh:{user_id}:target", "33")
    await redis_client.client.set(f"tasbeeh:{user_id}:streak", 0)
    
    # Get daily stats from Redis
    daily_count = await redis_client.client.get(f"tasbeeh:{user_id}:daily_count")
    daily_count = int(daily_count) if daily_count else 0
    
    # Get lifetime stats from user model
    lifetime_count = user.total_quran_read if user else 0
    
    # Get streak
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    
    # Get current dhikr
    dhikr_key = await redis_client.client.get(f"tasbeeh:{user_id}:dhikr")
    dhikr_key = dhikr_key if isinstance(dhikr_key, str) else (dhikr_key.decode() if dhikr_key else "subhanallah")
    dhikr_info = PRESET_DHIKR.get(dhikr_key, PRESET_DHIKR["subhanallah"])
    
    # Get target
    target_str = await redis_client.client.get(f"tasbeeh:{user_id}:target")
    target_str = target_str if isinstance(target_str, str) else (target_str.decode() if target_str else "33")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"📿 اضغط للتسبيح | 0", callback_data="tasbeeh_increment")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="tasbeeh_reset"),
        InlineKeyboardButton(text="📊 إحصائياتي", callback_data="tasbeeh_stats")
    )
    builder.row(
        InlineKeyboardButton(text=f"🎯 الهدف: {target_str}", callback_data="tasbeeh_target"),
        InlineKeyboardButton(text=f"✏️ {dhikr_info['emoji']} {dhikr_info['text']}", callback_data="tasbeeh_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    # Calculate progress bar
    target = TARGETS.get(target_str, 33)
    progress_bar = "[░░░░░░░░░░] 0%"
    if target:
        percentage = 0
        progress_bar = "[" + "█" * (percentage // 10) + "░" * (10 - percentage // 10) + "] " + str(percentage) + "%"
    
    text = (
        "📿 *المسبحة الإلكترونية - النسخة المطورّة*\n\n"
        f"{dhikr_info['emoji']} *التسبيح الحالي:* {dhikr_info['text']}\n\n"
        f"{progress_bar}\n\n"
        f"� *اليوم:* {daily_count} | *الكلي:* {lifetime_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم\n\n"
        "اضغط على زر التسبيح لزيادة العداد"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "tasbeeh_increment")
async def handle_tasbeeh_increment(callback: CallbackQuery, db: AsyncSession):
    """Increment tasbeeh counter with Redis atomic increment for zero-delay"""
    # Instant callback answer FIRST to prevent loading spinner
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Atomic increment in Redis for zero-latency
    count = await redis_client.client.incr(f"tasbeeh:{user_id}:count")
    
    # Get current dhikr
    dhikr_key = await redis_client.client.get(f"tasbeeh:{user_id}:dhikr")
    dhikr_key = dhikr_key if isinstance(dhikr_key, str) else (dhikr_key.decode() if dhikr_key else "subhanallah")
    dhikr_info = PRESET_DHIKR.get(dhikr_key, PRESET_DHIKR["subhanallah"])
    
    # Get target
    target_str = await redis_client.client.get(f"tasbeeh:{user_id}:target")
    target_str = target_str if isinstance(target_str, str) else (target_str.decode() if target_str else "33")
    target = TARGETS.get(target_str, 33)
    
    # Update daily count
    daily_count = await redis_client.client.incr(f"tasbeeh:{user_id}:daily_count")
    
    # Update streak
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    if daily_count == 1:  # First tasbeeh of the day
        streak += 1
        await redis_client.client.set(f"tasbeeh:{user_id}:streak", streak)
    
    # Update lifetime in database (async, non-blocking)
    try:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(total_quran_read=User.total_quran_read + 1)
        )
        await db.flush()
    except Exception as e:
        logger.error(f"Error updating lifetime count: {e}")
    
    # Calculate progress bar
    progress_bar = "[░░░░░░░░░░] 0%"
    if target:
        percentage = min(int((count / target) * 100), 100)
        filled = percentage // 10
        progress_bar = "[" + "█" * filled + "░" * (10 - filled) + "] " + str(percentage) + "% (" + str(count) + "/" + str(target) + ")"
    else:
        progress_bar = f"[██████████] غير محدود ({count})"
    
    # Build keyboard with dynamic counter button
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"📿 اضغط للتسبيح | {count}", callback_data="tasbeeh_increment")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="tasbeeh_reset"),
        InlineKeyboardButton(text="📊 إحصائياتي", callback_data="tasbeeh_stats")
    )
    builder.row(
        InlineKeyboardButton(text=f"🎯 الهدف: {target_str}", callback_data="tasbeeh_target"),
        InlineKeyboardButton(text=f"✏️ {dhikr_info['emoji']} {dhikr_info['text']}", callback_data="tasbeeh_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    # Check for milestones and target completion with celebration badges
    milestone_text = ""
    badge = ""
    if count == 33:
        milestone_text = "\n\n🌟 *أحسنت!* وصلت إلى 33 تسبيحة"
        badge = "🥇"
    elif count == 99:
        milestone_text = "\n\n🌟 *مبارك!* وصلت إلى 99 تسبيحة"
        badge = "🥈"
    elif count == 100:
        milestone_text = "\n\n🌟 *ممتاز!* أكملت 100 تسبيحة"
        badge = "🥉"
    elif count == 1000:
        milestone_text = "\n\n🏆 *إنجاز عظيم!* أكملت 1000 تسبيحة"
        badge = "🏆"
    
    # Check if target reached
    if target and count >= target:
        milestone_text += f"\n\n🎉 *تهانينا!* أكملت هدفك: {target} تسبيحة {badge}"
        await redis_client.client.set(f"tasbeeh:{user_id}:count", 0)  # Auto-reset on completion
        # Award badge
        badge = "🎖️"
    
    text = (
        f"📿 *المسبحة الإلكترونية - النسخة المطورّة*\n\n"
        f"{dhikr_info['emoji']} *التسبيح الحالي:* {dhikr_info['text']}\n\n"
        f"{progress_bar}\n\n"
        f"📊 *اليوم:* {daily_count} | *الكلي:* {daily_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم\n\n"
        f"{badge if badge else ''}{milestone_text}"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "tasbeeh_reset")
async def handle_tasbeeh_reset(callback: CallbackQuery):
    """Reset tasbeeh counter"""
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Reset counter
    await redis_client.client.set(f"tasbeeh:{user_id}:count", 0)
    
    # Get current dhikr and target
    dhikr_key = await redis_client.client.get(f"tasbeeh:{user_id}:dhikr")
    dhikr_key = dhikr_key if isinstance(dhikr_key, str) else (dhikr_key.decode() if dhikr_key else "subhanallah")
    dhikr_info = PRESET_DHIKR.get(dhikr_key, PRESET_DHIKR["subhanallah"])
    
    target_str = await redis_client.client.get(f"tasbeeh:{user_id}:target")
    target_str = target_str if isinstance(target_str, str) else (target_str.decode() if target_str else "33")
    
    daily_count = await redis_client.client.get(f"tasbeeh:{user_id}:daily_count")
    daily_count = int(daily_count) if daily_count else 0
    
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📿 اضغط للتسبيح | 0", callback_data="tasbeeh_increment")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="tasbeeh_reset"),
        InlineKeyboardButton(text="📊 إحصائياتي", callback_data="tasbeeh_stats")
    )
    builder.row(
        InlineKeyboardButton(text=f"🎯 الهدف: {target_str}", callback_data="tasbeeh_target"),
        InlineKeyboardButton(text=f"✏️ {dhikr_info['emoji']} {dhikr_info['text']}", callback_data="tasbeeh_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    # Calculate progress bar
    target = TARGETS.get(target_str, 33)
    progress_bar = "[░░░░░░░░░░] 0%"
    if target:
        progress_bar = "[" + "░" * 10 + "] 0% (0/" + str(target) + ")"
    else:
        progress_bar = "[██████████] غير محدود (0)"
    
    await callback.message.edit_text(
        f"📿 *المسبحة الإلكترونية - النسخة المطورّة*\n\n"
        f"{dhikr_info['emoji']} *التسبيح الحالي:* {dhikr_info['text']}\n\n"
        f"{progress_bar}\n\n"
        f"📊 *اليوم:* {daily_count} | *الكلي:* {daily_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم\n\n"
        "تم إعادة تعيين العداد",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer("🔄 تم إعادة تعيين العداد")


@router.callback_query(F.data == "tasbeeh_target")
async def handle_tasbeeh_target(callback: CallbackQuery):
    """Show target selection menu"""
    await callback.answer("🎯 اختيار الهدف")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="33 تسبيحة", callback_data="tasbeeh_set_target_33")
    )
    builder.row(
        InlineKeyboardButton(text="100 تسبيحة", callback_data="tasbeeh_set_target_100")
    )
    builder.row(
        InlineKeyboardButton(text="1000 تسبيحة", callback_data="tasbeeh_set_target_1000")
    )
    builder.row(
        InlineKeyboardButton(text="غير محدود", callback_data="tasbeeh_set_target_unlimited")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 عودة", callback_data="tasbeeh_start")
    )
    
    await callback.message.edit_text(
        "🎯 *اختر هدف التسبيح*\n\n"
        "اختر عدد التسبيحات المستهدف:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("tasbeeh_set_target_"))
async def handle_tasbeeh_set_target(callback: CallbackQuery):
    """Set tasbeeh target"""
    await callback.answer()
    
    user_id = callback.from_user.id
    target_str = callback.data.replace("tasbeeh_set_target_", "")
    
    # Save target to Redis
    await redis_client.client.set(f"tasbeeh:{user_id}:target", target_str)
    
    # Get current count and dhikr
    count = await redis_client.client.get(f"tasbeeh:{user_id}:count")
    count = int(count) if count else 0
    
    dhikr_key = await redis_client.client.get(f"tasbeeh:{user_id}:dhikr")
    dhikr_key = dhikr_key if isinstance(dhikr_key, str) else (dhikr_key.decode() if dhikr_key else "subhanallah")
    
    # Check if custom dhikr
    if dhikr_key.startswith("custom:"):
        custom_dhikr = await redis_client.client.get(f"tasbeeh:{user_id}:custom_dhikr_text")
        custom_dhikr = custom_dhikr.decode() if custom_dhikr else "تسبيح مخصص"
        dhikr_display = f"✏️ {custom_dhikr[:15]}..."
        dhikr_emoji = "✏️"
    else:
        dhikr_info = PRESET_DHIKR.get(dhikr_key, PRESET_DHIKR["subhanallah"])
        dhikr_display = f"{dhikr_info['emoji']} {dhikr_info['text']}"
        dhikr_emoji = dhikr_info['emoji']
    
    daily_count = await redis_client.client.get(f"tasbeeh:{user_id}:daily_count")
    daily_count = int(daily_count) if daily_count else 0
    
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"📿 اضغط للتسبيح | {count}", callback_data="tasbeeh_increment")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="tasbeeh_reset"),
        InlineKeyboardButton(text="📊 إحصائياتي", callback_data="tasbeeh_stats")
    )
    builder.row(
        InlineKeyboardButton(text=f"🎯 الهدف: {target_str}", callback_data="tasbeeh_target"),
        InlineKeyboardButton(text=f"✏️ {dhikr_display}", callback_data="tasbeeh_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    # Calculate progress bar
    target = TARGETS.get(target_str, 33)
    progress_bar = "[░░░░░░░░░░] 0%"
    if target:
        percentage = min(int((count / target) * 100), 100)
        filled = percentage // 10
        progress_bar = "[" + "█" * filled + "░" * (10 - filled) + "] " + str(percentage) + "% (" + str(count) + "/" + str(target) + ")"
    else:
        progress_bar = f"[██████████] غير محدود ({count})"
    
    await callback.message.edit_text(
        f"📿 *المسبحة الإلكترونية - النسخة المطورّة*\n\n"
        f"{dhikr_emoji} *التسبيح الحالي:* {dhikr_display.replace('✏️ ', '')}\n\n"
        f"{progress_bar}\n\n"
        f"📊 *اليوم:* {daily_count} | *الكلي:* {daily_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer(f"🎯 تم تعيين الهدف: {target_str}")


@router.callback_query(F.data == "tasbeeh_dhikr")
async def handle_tasbeeh_dhikr(callback: CallbackQuery):
    """Show dhikr selection menu"""
    await callback.answer("✏️ اختيار التسبيح")
    
    builder = InlineKeyboardBuilder()
    
    # Add preset dhikr options with emoji colors
    for dhikr_key, dhikr_info in PRESET_DHIKR.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{dhikr_info['emoji']} {dhikr_info['text']}",
                callback_data=f"tasbeeh_set_dhikr_{dhikr_key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="✏️ ➕ إضافة ذكر مخصص", callback_data="tasbeeh_custom_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 عودة", callback_data="tasbeeh_start")
    )
    
    await callback.message.edit_text(
        "✏️ *اختر التسبيح*\n\n"
        "اختر التسبيح الذي تريد الذكر به:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("tasbeeh_set_dhikr_"))
async def handle_tasbeeh_set_dhikr(callback: CallbackQuery):
    """Set tasbeeh dhikr"""
    await callback.answer()
    
    user_id = callback.from_user.id
    dhikr_key = callback.data.replace("tasbeeh_set_dhikr_", "")
    dhikr_info = PRESET_DHIKR.get(dhikr_key, PRESET_DHIKR["subhanallah"])
    
    # Save dhikr to Redis
    await redis_client.client.set(f"tasbeeh:{user_id}:dhikr", dhikr_key)
    
    # Get current count and target
    count = await redis_client.client.get(f"tasbeeh:{user_id}:count")
    count = int(count) if count else 0
    
    target_str = await redis_client.client.get(f"tasbeeh:{user_id}:target")
    target_str = target_str if isinstance(target_str, str) else (target_str.decode() if target_str else "33")
    
    daily_count = await redis_client.client.get(f"tasbeeh:{user_id}:daily_count")
    daily_count = int(daily_count) if daily_count else 0
    
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"📿 اضغط للتسبيح | {count}", callback_data="tasbeeh_increment")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="tasbeeh_reset"),
        InlineKeyboardButton(text="📊 إحصائياتي", callback_data="tasbeeh_stats")
    )
    builder.row(
        InlineKeyboardButton(text=f"🎯 الهدف: {target_str}", callback_data="tasbeeh_target"),
        InlineKeyboardButton(text=f"✏️ {dhikr_info['emoji']} {dhikr_info['text']}", callback_data="tasbeeh_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    # Calculate progress bar
    target = TARGETS.get(target_str, 33)
    progress_bar = "[░░░░░░░░░░] 0%"
    if target:
        percentage = min(int((count / target) * 100), 100)
        filled = percentage // 10
        progress_bar = "[" + "█" * filled + "░" * (10 - filled) + "] " + str(percentage) + "% (" + str(count) + "/" + str(target) + ")"
    else:
        progress_bar = f"[██████████] غير محدود ({count})"
    
    await callback.message.edit_text(
        f"📿 *المسبحة الإلكترونية - النسخة المطورّة*\n\n"
        f"{dhikr_info['emoji']} *التسبيح الحالي:* {dhikr_info['text']}\n\n"
        f"{progress_bar}\n\n"
        f"📊 *اليوم:* {daily_count} | *الكلي:* {daily_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer(f"✏️ تم تعيين التسبيح: {dhikr_info['text']}")


@router.callback_query(F.data == "tasbeeh_custom_dhikr")
async def handle_tasbeeh_custom_dhikr(callback: CallbackQuery, state: FSMContext):
    """Prompt for custom dhikr"""
    await callback.answer("✏️ تسبيح مخصص")
    
    await state.set_state(TasbeehStates.waiting_for_custom_dhikr)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 إلغاء", callback_data="tasbeeh_dhikr")
    )
    
    await callback.message.edit_text(
        "✏️ *تسبيح مخصص*\n\n"
        "يرجى إرسال التسبيح الذي تريد الذكر به:\n"
        "مثال: لا حول ولا قوة إلا بالله",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.message(TasbeehStates.waiting_for_custom_dhikr)
async def handle_custom_dhikr_input(message: Message, state: FSMContext, db: AsyncSession):
    """Handle custom dhikr input from user"""
    user_id = message.from_user.id
    custom_dhikr = message.text.strip()
    
    if not custom_dhikr:
        await message.answer("❌ يرجى إرسال التسبيح")
        return
    
    # Save custom dhikr to Redis
    await redis_client.client.set(f"tasbeeh:{user_id}:dhikr", f"custom:{custom_dhikr}")
    await redis_client.client.set(f"tasbeeh:{user_id}:custom_dhikr_text", custom_dhikr)
    
    await state.clear()
    
    # Get current count and target
    count = await redis_client.client.get(f"tasbeeh:{user_id}:count")
    count = int(count) if count else 0
    
    target_str = await redis_client.client.get(f"tasbeeh:{user_id}:target")
    target_str = target_str if isinstance(target_str, str) else (target_str.decode() if target_str else "33")
    
    daily_count = await redis_client.client.get(f"tasbeeh:{user_id}:daily_count")
    daily_count = int(daily_count) if daily_count else 0
    
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"📿 اضغط للتسبيح | {count}", callback_data="tasbeeh_increment")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="tasbeeh_reset"),
        InlineKeyboardButton(text="📊 إحصائياتي", callback_data="tasbeeh_stats")
    )
    builder.row(
        InlineKeyboardButton(text=f"🎯 الهدف: {target_str}", callback_data="tasbeeh_target"),
        InlineKeyboardButton(text=f"✏️ ✏️ {custom_dhikr[:15]}...", callback_data="tasbeeh_dhikr")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    # Calculate progress bar
    target = TARGETS.get(target_str, 33)
    progress_bar = "[░░░░░░░░░░] 0%"
    if target:
        percentage = min(int((count / target) * 100), 100)
        filled = percentage // 10
        progress_bar = "[" + "█" * filled + "░" * (10 - filled) + "] " + str(percentage) + "% (" + str(count) + "/" + str(target) + ")"
    else:
        progress_bar = f"[██████████] غير محدود ({count})"
    
    await message.answer(
        f"📿 *المسبحة الإلكترونية - النسخة المطورّة*\n\n"
        f"✏️ *التسبيح الحالي:* {custom_dhikr}\n\n"
        f"{progress_bar}\n\n"
        f"📊 *اليوم:* {daily_count} | *الكلي:* {daily_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "tasbeeh_stats")
async def handle_tasbeeh_stats(callback: CallbackQuery, db: AsyncSession):
    """Show detailed statistics"""
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user data
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    # Get stats from Redis
    daily_count = await redis_client.client.get(f"tasbeeh:{user_id}:daily_count")
    daily_count = int(daily_count) if daily_count else 0
    
    lifetime_count = user.total_quran_read if user else 0
    
    current_count = await redis_client.client.get(f"tasbeeh:{user_id}:count")
    current_count = int(current_count) if current_count else 0
    
    streak = await redis_client.client.get(f"tasbeeh:{user_id}:streak")
    streak = int(streak) if streak else 0
    
    dhikr_key = await redis_client.client.get(f"tasbeeh:{user_id}:dhikr")
    dhikr_key = dhikr_key if isinstance(dhikr_key, str) else (dhikr_key.decode() if dhikr_key else "subhanallah")
    
    # Check if custom dhikr
    if dhikr_key.startswith("custom:"):
        custom_dhikr = await redis_client.client.get(f"tasbeeh:{user_id}:custom_dhikr_text")
        custom_dhikr = custom_dhikr.decode() if custom_dhikr else "تسبيح مخصص"
        dhikr_display = custom_dhikr
        dhikr_emoji = "✏️"
    else:
        dhikr_info = PRESET_DHIKR.get(dhikr_key, PRESET_DHIKR["subhanallah"])
        dhikr_display = dhikr_info['text']
        dhikr_emoji = dhikr_info['emoji']
    
    target_str = await redis_client.client.get(f"tasbeeh:{user_id}:target")
    target_str = target_str if isinstance(target_str, str) else (target_str.decode() if target_str else "33")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 عودة", callback_data="tasbeeh_start")
    )
    
    # Calculate achievements
    achievements = []
    if lifetime_count >= 33:
        achievements.append("🥇 33 تسبيحة")
    if lifetime_count >= 99:
        achievements.append("🥈 99 تسبيحة")
    if lifetime_count >= 100:
        achievements.append("🥉 100 تسبيحة")
    if lifetime_count >= 1000:
        achievements.append("🏆 1000 تسبيحة")
    if streak >= 7:
        achievements.append("🔥 أسبوع متتالي")
    if streak >= 30:
        achievements.append("⭐ شهر متتالي")
    
    achievements_text = "\n".join(achievements) if achievements else "لا توجد إنجازات بعد"
    
    text = (
        "📊 *إحصائيات التسبيح*\n\n"
        f"{dhikr_emoji} *التسبيح الحالي:* {dhikr_display}\n"
        f"🔢 *العداد الحالي:* {current_count}\n"
        f"🎯 *الهدف:* {target_str}\n\n"
        f"📅 *مجموع تسبيحات اليوم:* {daily_count}\n"
        f"📈 *إجمالي التسبيحات الكلي:* {lifetime_count}\n"
        f"🔥 *أطول سلسلة:* {streak} يوم\n\n"
        f"🏆 *الإنجازات:*\n"
        f"{achievements_text}"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
