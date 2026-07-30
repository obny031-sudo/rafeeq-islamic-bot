"""Quran reading sub-handlers (surah list, pagination, resume)."""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from keyboards import get_main_menu_keyboard
from services.quran_service import quran_service
from services.user_service import UserService

logger = logging.getLogger(__name__)

router = Router()


async def display_surah_page(callback: CallbackQuery, surahs: list, page: int, state: FSMContext):
    """Display a page of Surahs with pagination."""
    surahs_per_page = 10
    start_idx = page * surahs_per_page
    end_idx = start_idx + surahs_per_page
    page_surahs = surahs[start_idx:end_idx]

    text = "📜 *اختر سورة للقراءة*\n\n"
    for surah in page_surahs:
        surah_num = surah.get("number")
        surah_name = surah.get("englishName")
        surah_name_ar = surah.get("name", "")
        ayahs_count = surah.get("numberOfAyahs", 0)
        revelation_type = surah.get("revelationType", "")
        text += f"{surah_num}. {surah_name_ar} ({surah_name})\n"
        text += f"   {ayahs_count} آية • {revelation_type}\n\n"

    builder = InlineKeyboardBuilder()
    for surah in page_surahs:
        surah_num = surah.get("number")
        surah_name_ar = surah.get("name", "")
        builder.row(
            InlineKeyboardButton(
                text=f"{surah_num}. {surah_name_ar}",
                callback_data=f"quran_surah_{surah_num}",
            )
        )

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"quran_page_{page - 1}"))
    if end_idx < len(surahs):
        nav_row.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"quran_page_{page + 1}"))
    if nav_row:
        builder.row(*nav_row)

    builder.row(InlineKeyboardButton(text="🔙 عودة", callback_data="quran"))
    await state.update_data(surah_page=page)

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


async def display_ayah_page(
    callback: CallbackQuery,
    surah_data: dict,
    page: int,
    state: FSMContext,
    db: AsyncSession,
):
    """Display a page of Ayahs from a Surah."""
    ayahs_per_page = 5
    ayahs = surah_data.get("ayahs", [])
    surah_info = surah_data.get("surah", {})

    start_idx = page * ayahs_per_page
    end_idx = start_idx + ayahs_per_page
    page_ayahs = ayahs[start_idx:end_idx]

    surah_name = surah_info.get("englishName", "")
    surah_name_ar = surah_info.get("name", "")
    text = f"📖 *سورة {surah_name_ar} ({surah_name})*\n\n"

    for ayah in page_ayahs:
        ayah_num = ayah.get("numberInSurah")
        ayah_text = ayah.get("text", "")
        text += f"{ayah_num}. {ayah_text}\n\n"

    builder = InlineKeyboardBuilder()
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ السابق", callback_data="quran_ayah_prev"))
    if end_idx < len(ayahs):
        nav_row.append(InlineKeyboardButton(text="التالي ➡️", callback_data="quran_ayah_next"))
    if nav_row:
        builder.row(*nav_row)

    builder.row(InlineKeyboardButton(text="🔙 عودة للسور", callback_data="quran_read_surah"))
    builder.row(InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu"))

    await state.update_data(ayah_page=page)

    if page_ayahs:
        user_service = UserService(db)
        await user_service.update_quran_position(
            callback.from_user.id,
            surah_info.get("number"),
            page_ayahs[-1].get("numberInSurah"),
        )

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "quran_read_surah")
async def show_surah_list(callback: CallbackQuery, state: FSMContext):
    """Show list of Surahs to read."""
    await callback.answer()
    
    surahs = await quran_service.get_surah_list()
    if not surahs:
        await callback.message.edit_text("❌ تعذر تحميل قائمة السور. يرجى المحاولة مرة أخرى لاحقاً.")
        return
    await display_surah_page(callback, surahs, page=0, state=state)


@router.callback_query(F.data.startswith("quran_page_"))
async def navigate_surah_page(callback: CallbackQuery, state: FSMContext):
    """Navigate between Surah pages."""
    await callback.answer()
    
    page = int(callback.data.split("_")[-1])
    surahs = await quran_service.get_surah_list()
    if surahs:
        await display_surah_page(callback, surahs, page, state)
    else:
        await callback.message.edit_text("تعذر تحميل قائمة السور")


@router.callback_query(F.data.startswith("quran_surah_"))
async def read_surah(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Read a specific Surah with pagination."""
    await callback.answer()
    
    surah_number = int(callback.data.split("_")[-1])
    surah_data = await quran_service.get_surah_ayahs(surah_number)

    if not surah_data:
        await callback.message.edit_text("❌ تعذر تحميل السورة. يرجى المحاولة مرة أخرى لاحقاً.")
        return

    await state.update_data(current_surah=surah_number, surah_data=surah_data, ayah_page=0)
    await display_ayah_page(callback, surah_data, page=0, state=state, db=db)


@router.callback_query(F.data == "quran_ayah_next")
async def next_ayah_page(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Navigate to next Ayah page."""
    await callback.answer()
    
    data = await state.get_data()
    current_page = data.get("ayah_page", 0)
    surah_data = data.get("surah_data")
    if surah_data:
        await display_ayah_page(callback, surah_data, current_page + 1, state, db)
    else:
        await callback.answer("خطأ: لم يتم العثور على بيانات السورة")


@router.callback_query(F.data == "quran_ayah_prev")
async def prev_ayah_page(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Navigate to previous Ayah page."""
    await callback.answer()
    
    data = await state.get_data()
    current_page = data.get("ayah_page", 0)
    surah_data = data.get("surah_data")
    if surah_data and current_page > 0:
        await display_ayah_page(callback, surah_data, current_page - 1, state, db)
    else:
        await callback.answer("أنت بالفعل في الصفحة الأولى")


@router.callback_query(F.data == "quran_resume")
async def resume_reading(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Resume reading from last position."""
    await callback.answer()
    
    data = await state.get_data()
    result = await db.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user or not user.last_read_surah:
        await callback.message.edit_text("❌ لم يتم العثور على موضع قراءة محفوظ. ابدأ بقراءة سورة أولاً.")
        return

    surah_data = await quran_service.get_surah_ayahs(user.last_read_surah)
    if not surah_data:
        await callback.message.edit_text("❌ تعذر تحميل السورة المحفوظة. يرجى المحاولة مرة أخرى لاحقاً.")
        return

    ayahs = surah_data.get("ayahs", [])
    ayahs_per_page = 5
    target_page = 0
    for i, ayah in enumerate(ayahs):
        if ayah.get("numberInSurah") == user.last_read_ayah:
            target_page = i // ayahs_per_page
            break

    await state.update_data(
        current_surah=user.last_read_surah,
        surah_data=surah_data,
        ayah_page=target_page,
    )
    await display_ayah_page(callback, surah_data, target_page, state, db)
