import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from models.user import User
from keyboards import get_main_menu_keyboard, get_quran_menu_keyboard
from services.content_manager import content_manager

logger = logging.getLogger(__name__)

router = Router()

# FSM States for Quran navigation
class QuranStates(StatesGroup):
    reading = State()
    selecting_surah = State()


@router.message(F.text.in_(["📜 قراءة السور", "قراءة السور"]))
async def handle_read_surah(message: Message, db: AsyncSession):
    """Handle read Surah button from reply keyboard"""
    try:
        # Get Surah Al-Fatiha (Surah 1) as default
        surah = content_manager.get_full_surah(1)
        
        if not surah:
            await message.answer(
                "❌ خطأ في تحميل البيانات",
                reply_markup=get_quran_menu_keyboard("ar")
            )
            return
        
        # Format full surah message
        text = f"📖 *سورة {surah.get('name', 'الفاتحة')}*\n\n"
        text += f"🔢 رقم السورة: {surah.get('surah_number', 1)}\n"
        text += f"📊 عدد الآيات: {len(surah.get('ayahs', []))}\n\n"
        
        # Add all ayahs
        ayahs = surah.get('ayahs', [])
        for i, ayah in enumerate(ayahs, 1):
            arabic = ayah.get('arabic_text', '')
            text += f"{i}. {arabic}\n"
        
        # Chunk if too long
        chunks = content_manager.chunk_text(text)
        
        for chunk in chunks:
            await message.answer(
                chunk,
                parse_mode="Markdown",
                reply_markup=get_quran_menu_keyboard("ar")
            )
            
    except Exception as e:
        logger.error(f"Error reading Surah: {e}")
        await message.answer(
            "❌ خطأ في قراءة السورة",
            reply_markup=get_quran_menu_keyboard("ar")
        )


@router.message(F.text.in_(["📖 الأجزاء", "الأجزاء"]))
async def handle_juz(message: Message, db: AsyncSession):
    """Handle Juz button from reply keyboard"""
    await message.answer(
        "📖 *الأجزاء الثلاثون*\n\n"
        "سيتم إضافة هذه الميزة قريباً.",
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard("ar")
    )


@router.message(F.text.in_(["🔖 العلامات المحفوظة", "العلامات المحفوظة"]))
async def handle_bookmarks(message: Message, db: AsyncSession):
    """Handle bookmarks button from reply keyboard"""
    await message.answer(
        "🔖 *العلامات المحفوظة*\n\n"
        "سيتم إضافة هذه الميزة قريباً.",
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard("ar")
    )


@router.message(F.text.in_(["📍 موضع القراءة الأخير", "موضع القراءة الأخير"]))
async def handle_last_position(message: Message, db: AsyncSession):
    """Handle last reading position button from reply keyboard"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.last_read_surah:
        await message.answer(
            "📍 *لم يتم تسجيل أي قراءة بعد*\n\n"
            "ابدأ بقراءة سورة لتسجيل موقعك.",
            parse_mode="Markdown",
            reply_markup=get_quran_menu_keyboard("ar")
        )
        return
    
    # Get the last read surah
    surah = content_manager.get_full_surah(user.last_read_surah)
    
    if surah:
        text = f"📍 *آخر قراءة*\n\n"
        text += f"📖 سورة: {surah.get('name', 'غير معروف')}\n"
        text += f"🔢 الآية: {user.last_read_ayah}\n\n"
        
        # Get the specific ayah
        ayah = content_manager.get_surah_ayah(user.last_read_surah, user.last_read_ayah)
        if ayah:
            text += f"📜 *النص:*\n{ayah.get('arabic_text', '')}"
        
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_quran_menu_keyboard("ar")
        )
    else:
        await message.answer(
            "❌ خطأ في تحميل موقع القراءة",
            reply_markup=get_quran_menu_keyboard("ar")
        )


async def show_quran_menu(message: Message, db: AsyncSession):
    """Show Quran module menu (message version for reply keyboard)"""
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
    
    # Check if user has a saved reading position
    if user.last_read_surah:
        response_text = (
            f"📖 *القرآن الكريم* 📖\n\n"
            f"📍 *آخر قراءة:* سورة {user.last_read_surah}، آية {user.last_read_ayah}\n\n"
            f"اختر خياراً:"
        )
    else:
        response_text = (
            f"📖 *القرآن الكريم* 📖\n\n"
            f"اختر خياراً:"
        )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard(language)
    )


@router.callback_query(F.data == "quran_surah_list")
async def handle_quran_surah_list(callback: CallbackQuery):
    """Handle Quran surah list button"""
    await callback.answer("📜 قائمة السور")
    
    # Get all surahs
    quran_data = content_manager.quran_data
    
    text = "📜 *قائمة السور*\n\n"
    for surah in quran_data[:30]:  # Show first 30 surahs
        text += f"{surah.get('id', 0)}. {surah.get('name', 'غير معروف')}\n"
    
    text += "\n... المزيد قريباً"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "quran_search")
async def handle_quran_search(callback: CallbackQuery):
    """Handle Quran search button"""
    await callback.answer("🔍 البحث في القرآن")
    
    text = "🔍 *البحث في القرآن*\n\n"
    text += "أرسل كلمة البحث للبحث في آيات القرآن الكريم.\n\n"
    text += "مثال: \"الرحمن\" أو \"الصلاة\""
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "quran_juz")
async def handle_quran_juz(callback: CallbackQuery):
    """Handle Quran Juz button"""
    await callback.answer("📖 الأجزاء")
    
    text = "📖 *الأجزاء الثلاثون*\n\n"
    text += "سيتم إضافة هذه الميزة قريباً."
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
