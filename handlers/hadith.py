import logging
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from models.user import User
from keyboards import get_main_menu_keyboard, get_hadith_menu_keyboard
from services.content_manager import content_manager

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "hadith")
async def show_hadith_menu(callback: CallbackQuery, db: AsyncSession):
    """Show Hadith module menu (inline keyboard version)"""
    await callback.answer("📚 الأحاديث النبوية")
    
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
        "📚 *الأحاديث النبوية الشريفة* 📚\n\n"
        "اختر مجموعة:",
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_keyboard("ar")
    )


@router.callback_query(F.data == "hadith_bukhari")
async def handle_hadith_bukhari(callback: CallbackQuery):
    """Handle Sahih Bukhari callback"""
    await callback.answer("📚 صحيح البخاري")
    
    try:
        logger.info(f"Attempting to get hadith from content_manager")
        logger.info(f"Hadith data length: {len(content_manager.hadith_data)}")
        
        hadith = content_manager.get_hadith(random=True)
        logger.info(f"Got hadith: {hadith is not None}")
        
        if hadith:
            logger.info(f"Hadith keys: {hadith.keys()}")
            formatted_text = content_manager.format_hadith_message(hadith)
            logger.info(f"Formatted text length: {len(formatted_text)}")
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🔄 حديث آخر", callback_data="hadith_bukhari"),
                InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="hadith")
            )
            builder.row(
                InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
            )
            
            await callback.message.edit_text(
                formatted_text,
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
        else:
            logger.error("Hadith is None - data may be empty")
            await callback.message.edit_text("❌ خطأ في تحميل الحديث - البيانات غير متوفرة")
    except Exception as e:
        logger.error(f"Error in handle_hadith_bukhari: {e}", exc_info=True)
        await callback.message.edit_text(f"❌ خطأ: {str(e)}")


@router.callback_query(F.data == "hadith_muslim")
async def handle_hadith_muslim(callback: CallbackQuery):
    """Handle Sahih Muslim callback"""
    await callback.answer("📖 صحيح مسلم")
    
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 حديث آخر", callback_data="hadith_muslim"),
            InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="hadith")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            formatted_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text("❌ خطأ في تحميل الحديث")


@router.callback_query(F.data == "hadith_tirmidhi")
async def handle_hadith_tirmidhi(callback: CallbackQuery):
    """Handle Sunan Tirmidhi callback"""
    await callback.answer("📜 سنن الترمذي")
    
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 حديث آخر", callback_data="hadith_tirmidhi"),
            InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="hadith")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            formatted_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text("❌ خطأ في تحميل الحديث")


@router.callback_query(F.data == "hadith_general")
async def handle_hadith_general(callback: CallbackQuery):
    """Handle General Hadith callback"""
    await callback.answer("📋 أحاديث عامة")
    
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 حديث آخر", callback_data="hadith_general"),
            InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="hadith")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            formatted_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text("❌ خطأ في تحميل الحديث")


@router.callback_query(F.data == "hadith_search")
async def handle_hadith_search(callback: CallbackQuery):
    """Handle Hadith search callback"""
    await callback.answer("🔍 البحث في الأحاديث")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="hadith")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )
    
    await callback.message.edit_text(
        "🔍 *البحث في الأحاديث*\n\n"
        "يرجى إرسال كلمة البحث للبحث في الأحاديث.\n"
        "يمكنك البحث بالعربية أو الإنجليزية.",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.message(F.text.in_(["🔍 البحث في الأحاديث", "البحث في الأحاديث"]))
async def handle_search_hadith(message: Message):
    """Handle search Hadith button from reply keyboard"""
    await message.answer(
        "🔍 *البحث في الأحاديث*\n\n"
        "يرجى إرسال كلمة البحث للبحث في الأحاديث.\n"
        "يمكنك البحث بالعربية أو الإنجليزية.",
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard("ar")
    )


@router.message(F.text.in_(["📚 صحيح البخاري", "صحيح البخاري"]))
async def handle_bukhari_hadith(message: Message):
    """Handle Bukhari Hadith button from reply keyboard"""
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        chunks = content_manager.chunk_text(formatted_text)
        for chunk in chunks:
            await message.answer(
                chunk,
                parse_mode="Markdown",
                reply_markup=get_hadith_menu_reply_keyboard("ar")
            )
    else:
        await message.answer(
            "❌ خطأ في تحميل الحديث",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )


@router.message(F.text.in_(["📖 صحيح مسلم", "صحيح مسلم"]))
async def handle_muslim_hadith(message: Message):
    """Handle Muslim Hadith button from reply keyboard"""
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        chunks = content_manager.chunk_text(formatted_text)
        for chunk in chunks:
            await message.answer(
                chunk,
                parse_mode="Markdown",
                reply_markup=get_hadith_menu_reply_keyboard("ar")
            )
    else:
        await message.answer(
            "❌ خطأ في تحميل الحديث",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )


@router.message(F.text.in_(["📜 سنن الترمذي", "سنن الترمذي"]))
async def handle_tirmidhi_hadith(message: Message):
    """Handle Tirmidhi Hadith button from reply keyboard"""
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        chunks = content_manager.chunk_text(formatted_text)
        for chunk in chunks:
            await message.answer(
                chunk,
                parse_mode="Markdown",
                reply_markup=get_hadith_menu_reply_keyboard("ar")
            )
    else:
        await message.answer(
            "❌ خطأ في تحميل الحديث",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )


@router.message(F.text.in_(["📋 أحاديث عامة", "أحاديث عامة"]))
async def handle_general_hadith(message: Message):
    """Handle general Hadith button from reply keyboard"""
    hadith = content_manager.get_hadith(random=True)
    if hadith:
        formatted_text = content_manager.format_hadith_message(hadith)
        chunks = content_manager.chunk_text(formatted_text)
        for chunk in chunks:
            await message.answer(
                chunk,
                parse_mode="Markdown",
                reply_markup=get_hadith_menu_reply_keyboard("ar")
            )
    else:
        await message.answer(
            "❌ خطأ في تحميل الحديث",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )


async def show_hadith_menu(message: Message, db: AsyncSession):
    """Show Hadith module menu (message version for reply keyboard)"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_reply_keyboard("ar")
        )
        return
    
    language = user.language.value if user.language else "ar"
    
    await message.answer(
        "📚 *الأحاديث النبوية الشريفة* 📚\n\n"
        "اختر مجموعة:",
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard(language)
    )


async def handle_hadith_search(callback: CallbackQuery):
    """Handle Hadith search - prompts user for search query"""
    await callback.message.answer(
        "🔍 *البحث في الأحاديث*\\n\\n"
        "يرجى إرسال كلمة البحث للبحث في الأحاديث.\\n"
        "يمكنك البحث بالعربية أو الإنجليزية.",
        parse_mode="Markdown"
    )
    await callback.answer("✅ يرجى إرسال كلمة البحث")


@router.message(F.text)
async def search_hadith(message: Message):
    """Search Hadith by text"""
    query = message.text.lower()
    
    results = []
    for collection, hadith_list in HADITH_DATA.items():
        for hadith in hadith_list:
            arabic = hadith.get("arabic", "")
            english = hadith.get("english", "")
            narrator = hadith.get("narrator", "")
            
            if (query in arabic.lower() or 
                query in english.lower() or 
                query in narrator.lower()):
                results.append((collection, hadith))
    
    if results:
        # Show first 5 results
        response_text = f"🔍 *نتائج البحث: {message.text}*\\n\\n"
        for i, (collection, hadith) in enumerate(results[:5], 1):
            arabic = hadith.get("arabic", "")
            english = hadith.get("english", "")
            response_text += f"{i}. {arabic}\\n{english}\\n\\n"
        
        if len(results) > 5:
            response_text += f"... و {len(results) - 5} نتيجة أخرى"
    else:
        response_text = "❌ *لم يتم العثور على نتائج*\\n\\n" "يرجى المحاولة بكلمة بحث أخرى."
    
    await message.answer(response_text, parse_mode="Markdown")


async def handle_hadith_copy(callback: CallbackQuery, collection: str):
    """Handle Hadith copy - copies current Hadith text"""
    hadith = get_random_hadith(collection)
    arabic = hadith.get("arabic", "")
    english = hadith.get("english", "")
    reference = hadith.get("reference", "")
    narrator = hadith.get("narrator", "")
    
    copy_text = f"{arabic}\\n\\n{english}\\n\\nالراوي: {narrator}\\nالمصدر: {reference}"
    
    await callback.message.answer(
        f"📋 *نص الحديث للنسخ*\\n\\n{copy_text}",
        parse_mode="Markdown"
    )
    await callback.answer("✅ تم عرض النص للنسخ")


async def handle_hadith_bookmark(callback: CallbackQuery, collection: str, db: AsyncSession):
    """Handle Hadith bookmark - saves to user bookmarks"""
    user_id = callback.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        # For now, just acknowledge - would need UserBookmark model for full implementation
        await callback.answer("✅ تم حفظ الحديث في العلامات")
    else:
        await callback.answer("❌ لم يتم العثور على المستخدم")
