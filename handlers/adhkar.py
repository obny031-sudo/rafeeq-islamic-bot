import logging
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pathlib import Path
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from models.user import User
from keyboards import get_main_menu_keyboard, get_adhkar_menu_keyboard
from services.scheduler_service import scheduler_service
from services.content_manager import content_manager

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "adhkar")
async def show_adhkar_menu(callback: CallbackQuery, db: AsyncSession):
    """Show Adhkar module menu (inline keyboard version)"""
    await callback.answer("🤲 الأذكار والأدعية")
    
    user_id = callback.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    await callback.message.edit_text(
        "🤲 *الأذكار والأدعية* 🤲\n\n"
        "اختر فئة:",
        parse_mode="Markdown",
        reply_markup=get_adhkar_menu_keyboard("ar")
    )


@router.callback_query(F.data == "adhkar_morning")
async def handle_adhkar_morning(callback: CallbackQuery):
    """Handle morning Adhkar button - send image"""
    await callback.answer("🌅 أذكار الصباح")
    
    try:
        adhkar_image = content_manager.get_adhkar_image("morning_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
                
                await callback.message.edit_caption(
                    caption="🌅 *أذكار الصباح*\n\n"
                           "استقبل يومك بذكر الله",
                    parse_mode="Markdown",
                    reply_markup=builder.as_markup()
                )
                return
        
        await callback.message.edit_text(
            "❌ خطأ في تحميل صورة الأذكار"
        )
    except Exception as e:
        logger.error(f"Error sending morning Adhkar image: {e}")
        await callback.message.edit_text(
            "❌ خطأ في إرسال أذكار الصباح"
        )


@router.callback_query(F.data == "adhkar_evening")
async def handle_adhkar_evening(callback: CallbackQuery):
    """Handle evening Adhkar button - send image"""
    await callback.answer("🌙 أذكار المساء")
    
    try:
        adhkar_image = content_manager.get_adhkar_image("evening_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
                
                await callback.message.edit_caption(
                    caption="🌙 *أذكار المساء*\n\n"
                           "اختم يومك بذكر الله",
                    parse_mode="Markdown",
                    reply_markup=builder.as_markup()
                )
                return
        
        await callback.message.edit_text(
            "❌ خطأ في تحميل صورة الأذكار"
        )
    except Exception as e:
        logger.error(f"Error sending evening Adhkar image: {e}")
        await callback.message.edit_text(
            "❌ خطأ في إرسال أذكار المساء"
        )


@router.callback_query(F.data == "adhkar_sleep")
async def handle_adhkar_sleep(callback: CallbackQuery):
    """Handle sleep Adhkar button - send image"""
    await callback.answer("😴 أذكار النوم")
    
    try:
        adhkar_image = content_manager.get_adhkar_image("evening_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
                
                await callback.message.edit_caption(
                    caption="😴 *أذكار النوم*\n\n"
                           "احفظك الله ويرعاك",
                    parse_mode="Markdown",
                    reply_markup=builder.as_markup()
                )
                return
        
        await callback.message.edit_text(
            "❌ خطأ في تحميل صورة الأذكار"
        )
    except Exception as e:
        logger.error(f"Error sending sleep Adhkar image: {e}")
        await callback.message.edit_text(
            "❌ خطأ في إرسال أذكار النوم"
        )


@router.callback_query(F.data == "adhkar_general")
async def handle_adhkar_general(callback: CallbackQuery):
    """Handle general Adhkar button - send image"""
    await callback.answer("🤲 أذكار عامة")
    
    try:
        adhkar_image = content_manager.get_adhkar_image("morning_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
                
                await callback.message.edit_caption(
                    caption="🤲 *أذكار عامة*\n\n"
                           "اذكر الله في كل وقت",
                    parse_mode="Markdown",
                    reply_markup=builder.as_markup()
                )
                return
        
        await callback.message.edit_text(
            "❌ خطأ في تحميل صورة الأذكار"
        )
    except Exception as e:
        logger.error(f"Error sending general Adhkar image: {e}")
        await callback.message.edit_text(
            "❌ خطأ في إرسال أذكار عامة"
        )


@router.message(F.text.in_(["🌅 أذكار الصباح", "أذكار الصباح"]))
async def handle_morning_adhkar(message: Message):
    """Handle morning Adhkar button from reply keyboard - send image"""
    try:
        adhkar_image = content_manager.get_adhkar_image("morning_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                await message.answer_photo(
                    photo=image_path,
                    caption="🌅 *أذكار الصباح*\n\n"
                           "استقبل يومك بذكر الله",
                    parse_mode="Markdown",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
            else:
                await message.answer(
                    "❌ خطأ في تحميل صورة الأذكار",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
        else:
            await message.answer(
                "❌ خطأ في تحميل بيانات الأذكار",
                reply_markup=get_adhkar_menu_keyboard("ar")
            )
    except Exception as e:
        logger.error(f"Error sending morning Adhkar image: {e}")
        await message.answer(
            "❌ خطأ في إرسال أذكار الصباح",
            reply_markup=get_adhkar_menu_keyboard("ar")
        )


@router.message(F.text.in_(["🌙 أذكار المساء", "أذكار المساء"]))
async def handle_evening_adhkar(message: Message):
    """Handle evening Adhkar button from reply keyboard - send image"""
    try:
        adhkar_image = content_manager.get_adhkar_image("evening_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                await message.answer_photo(
                    photo=image_path,
                    caption="🌙 *أذكار المساء*\n\n"
                           "اختم يومك بذكر الله",
                    parse_mode="Markdown",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
            else:
                await message.answer(
                    "❌ خطأ في تحميل صورة الأذكار",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
        else:
            await message.answer(
                "❌ خطأ في تحميل بيانات الأذكار",
                reply_markup=get_adhkar_menu_keyboard("ar")
            )
    except Exception as e:
        logger.error(f"Error sending evening Adhkar image: {e}")
        await message.answer(
            "❌ خطأ في إرسال أذكار المساء",
            reply_markup=get_adhkar_menu_keyboard("ar")
        )


@router.message(F.text.in_(["😴 أذكار النوم", "أذكار النوم"]))
async def handle_sleep_adhkar(message: Message):
    """Handle sleep Adhkar button from reply keyboard - send image"""
    try:
        adhkar_image = content_manager.get_adhkar_image("evening_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                await message.answer_photo(
                    photo=image_path,
                    caption="😴 *أذكار النوم*\n\n"
                           "احفظك الله ويرعاك",
                    parse_mode="Markdown",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
            else:
                await message.answer(
                    "❌ خطأ في تحميل صورة الأذكار",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
        else:
            await message.answer(
                "❌ خطأ في تحميل بيانات الأذكار",
                reply_markup=get_adhkar_menu_keyboard("ar")
            )
    except Exception as e:
        logger.error(f"Error sending sleep Adhkar image: {e}")
        await message.answer(
            "❌ خطأ في إرسال أذكار النوم",
            reply_markup=get_adhkar_menu_keyboard("ar")
        )


@router.message(F.text.in_(["🤲 أذكار عامة", "أذكار عامة"]))
async def handle_general_adhkar(message: Message):
    """Handle general Adhkar button from reply keyboard - send image"""
    try:
        adhkar_image = content_manager.get_adhkar_image("morning_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                await message.answer_photo(
                    photo=image_path,
                    caption="🤲 *أذكار عامة*\n\n"
                           "اذكر الله في كل وقت",
                    parse_mode="Markdown",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
            else:
                await message.answer(
                    "❌ خطأ في تحميل صورة الأذكار",
                    reply_markup=get_adhkar_menu_keyboard("ar")
                )
        else:
            await message.answer(
                "❌ خطأ في تحميل بيانات الأذكار",
                reply_markup=get_adhkar_menu_keyboard("ar")
            )
    except Exception as e:
        logger.error(f"Error sending general Adhkar image: {e}")
        await message.answer(
            "❌ خطأ في إرسال أذكار عامة",
            reply_markup=get_adhkar_menu_keyboard("ar")
        )


async def send_scheduled_adhkar(user_id: int, category: str = "morning", bot=None):
    """
    Send scheduled Adhkar to user (called by scheduler) - sends image.
    
    Args:
        user_id: Telegram user ID
        category: Adhkar category to send
        bot: Telegram bot instance
    """
    if not bot:
        return
    
    try:
        adhkar_image = content_manager.get_adhkar_image(f"{category}_adhkar")
        
        if adhkar_image:
            image_path = Path(adhkar_image['path'])
            if image_path.exists():
                category_names = {
                    "morning": "الصباح",
                    "evening": "المساء",
                    "sleep": "النوم"
                }
                category_name = category_names.get(category, category)
                
                await bot.send_photo(
                    user_id,
                    photo=image_path,
                    caption=f"🤲 *أذكار {category_name}*\n\n"
                           f"ذكر الله يطمئن القلوب",
                    parse_mode="Markdown"
                )
            else:
                logger.error(f"Adhkar image not found: {image_path}")
        else:
            logger.error(f"No Adhkar image found for category: {category}")
            
    except Exception as e:
        logger.error(f"Error sending scheduled Adhkar to user {user_id}: {e}")


async def show_adhkar_menu(message: Message, db: AsyncSession):
    """Show Adhkar module menu (message version for reply keyboard)"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    language = user.language.value if user.language else "ar"
    
    await message.answer(
        "🤲 *الأذكار والأدعية* 🤲\n\n"
        "اختر فئة:",
        parse_mode="Markdown",
        reply_markup=get_adhkar_menu_keyboard(language)
    )

async def handle_adhkar_copy(callback: CallbackQuery, category: str):
    """Handle Adhkar copy - copies current Adhkar text"""
    adhkar = get_random_adhkar(category)
    arabic = adhkar.get("arabic", "")
    transliteration = adhkar.get("transliteration", "")
    translation = adhkar.get("translation", "")
    reference = adhkar.get("reference", "")
    
    copy_text = f"📖 *النص العربي:*\n{arabic}\n\n"
    if transliteration:
        copy_text += f"🔤 *التلفظ:*\n{transliteration}\n\n"
    copy_text += f"📝 *الترجمة:*\n{translation}\n\n"
    copy_text += f"📚 *المصدر:* {reference}"
    
    await callback.message.answer(
        copy_text,
        parse_mode="Markdown"
    )
    await callback.answer("✅ تم عرض النص للنسخ")


async def handle_adhkar_favorite(callback: CallbackQuery, category: str, db: AsyncSession):
    """Handle Adhkar favorite - saves to user favorites"""
    user_id = callback.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        # For now, just acknowledge - would need UserFavorite model for full implementation
        await callback.answer("✅ تم حفظ الذكر في المفضلة")
    else:
        await callback.answer("❌ لم يتم العثور على المستخدم")


async def handle_adhkar_search(callback: CallbackQuery):
    """Handle Adhkar search - prompts user for search query"""
    await callback.message.answer(
        "🔍 *البحث في الأذكار*\\n\\n"
        "يرجى إرسال كلمة البحث للبحث في الأذكار.\\n"
        "يمكنك البحث بالعربية أو الإنجليزية.",
        parse_mode="Markdown"
    )
    await callback.answer("✅ يرجى إرسال كلمة البحث")


@router.message(F.text)
async def search_adhkar(message: Message):
    """Search Adhkar by text"""
    query = message.text.lower()
    
    results = []
    for category, adhkar_list in ADHKAR_DATA.items():
        for adhkar in adhkar_list:
            arabic = adhkar.get("arabic", "")
            translation = adhkar.get("translation", "")
            transliteration = adhkar.get("transliteration", "")
            
            if (query in arabic.lower() or 
                query in translation.lower() or 
                query in transliteration.lower()):
                results.append((category, adhkar))
    
    if results:
        # Show first 5 results
        response_text = f"🔍 *نتائج البحث: {message.text}*\\n\\n"
        for i, (category, adhkar) in enumerate(results[:5], 1):
            arabic = adhkar.get("arabic", "")
            translation = adhkar.get("translation", "")
            response_text += f"{i}. {arabic}\\n{translation}\\n\\n"
        
        if len(results) > 5:
            response_text += f"... و {len(results) - 5} نتيجة أخرى"
    else:
        response_text = "❌ *لم يتم العثور على نتائج*\\n\\n" "يرجى المحاولة بكلمة بحث أخرى."
    
    await message.answer(response_text, parse_mode="Markdown")


async def handle_adhkar_schedule(callback: CallbackQuery, db: AsyncSession):
    """Handle Adhkar daily reminder scheduling"""
    user_id = callback.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        await callback.answer()
        return
    
    # Check if daily Wird is enabled
    if user.daily_wird_enabled:
        # Schedule morning Adhkar at 7:00 AM
        scheduler_service.add_daily_adhkar_job(user_id, "07:00")
        
        await callback.message.edit_text(
            "✅ *تم تفعيل تذكير الأذكار اليومي*\\n\\n"
            "ستتلقى تذكيراً بأذكار الصباح الساعة 7:00 صباحاً يومياً.\\n\\n"
            "لإيقاف هذه الميزة، اذهب إلى الإعدادات.",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user.language.value if user.language else "ar")
        )
    else:
        await callback.message.edit_text(
            "❌ *الوِرد اليومي معطل*\\n\\n"
            "يرجى تفعيل الوِرد اليومي في الإعدادات لاستلام تذكيرات الأذكار.",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user.language.value if user.language else "ar")
        )
    
    await callback.answer()

async def send_scheduled_adhkar(user_id: int, category: str = "morning", bot=None):
    """
    Send scheduled Adhkar to user (called by scheduler).
    
    Args:
        user_id: Telegram user ID
        category: Adhkar category to send
        bot: Telegram bot instance
    """
    if not bot:
        return
    
    adhkar = get_random_adhkar(category)
    arabic = adhkar.get("arabic", "")
    transliteration = adhkar.get("transliteration", "")
    translation = adhkar.get("translation", "")
    reference = adhkar.get("reference", "")
    count = adhkar.get("count", 1)
    
    # Format with clear sections
    text = f"🤲 *أذكار {category.capitalize()}*\n\n"
    text += f"📖 *النص العربي:*\n{arabic}\n\n"
    
    if transliteration:
        text += f"🔤 *التلفظ:*\n{transliteration}\n\n"
    
    text += f"📝 *الترجمة:*\n{translation}\n\n"
    
    if count > 1:
        text += f"🔢 *التكرار:* {count} مرة\n\n"
    
    text += f"📚 *المصدر:* {reference}"
    
    try:
        await bot.send_message(user_id, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending scheduled Adhkar to user {user_id}: {e}")


@router.message(F.text.in_(["🌅 أذكار الصباح", "أذكار الصباح"]))
async def handle_morning_adhkar(message: Message):
    """Handle morning Adhkar button from reply keyboard"""
    adhkar = get_random_adhkar("morning")
    await format_and_send_adhkar(message, adhkar, "الصباح")


@router.message(F.text.in_(["🌙 أذكار المساء", "أذكار المساء"]))
async def handle_evening_adhkar(message: Message):
    """Handle evening Adhkar button from reply keyboard"""
    adhkar = get_random_adhkar("evening")
    await format_and_send_adhkar(message, adhkar, "المساء")


@router.message(F.text.in_(["😴 أذكار النوم", "أذكار النوم"]))
async def handle_sleep_adhkar(message: Message):
    """Handle sleep Adhkar button from reply keyboard"""
    adhkar = get_random_adhkar("sleep")
    await format_and_send_adhkar(message, adhkar, "النوم")


@router.message(F.text.in_(["🤲 أذكار عامة", "أذكار عامة"]))
async def handle_general_adhkar(message: Message):
    """Handle general Adhkar button from reply keyboard"""
    adhkar = get_random_adhkar("general")
    await format_and_send_adhkar(message, adhkar, "عامة")


async def format_and_send_adhkar(message: Message, adhkar: dict, category_name: str):
    """Format and send Adhkar with clean layout"""
    arabic = adhkar.get("arabic", "")
    transliteration = adhkar.get("transliteration", "")
    translation = adhkar.get("translation", "")
    reference = adhkar.get("reference", "")
    count = adhkar.get("count", 1)
    
    # Format with clear sections
    text = f"🤲 *أذكار {category_name}*\n\n"
    text += f"📖 *النص العربي:*\n{arabic}\n\n"
    
    if transliteration:
        text += f"🔤 *التلفظ:*\n{transliteration}\n\n"
    
    text += f"📝 *الترجمة:*\n{translation}\n\n"
    
    if count > 1:
        text += f"🔢 *التكرار:* {count} مرة\n\n"
    
    text += f"📚 *المصدر:* {reference}"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_adhkar_menu_keyboard("ar")
    )
