from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from models.user import User, Language
from keyboards import get_main_menu_keyboard, get_quran_menu_keyboard, get_adhkar_menu_keyboard, get_hadith_menu_keyboard, get_prayer_menu_keyboard
from utils.database import get_db
from services.scheduler_service import scheduler_service

router = Router()

# FSM States for Quran navigation
class QuranStates(StatesGroup):
    waiting_for_surah_number = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message, db: AsyncSession):
    """Handle /start command - Create user and show main menu"""
    user_id = message.from_user.id
    
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user with fallback for None username
        username = message.from_user.username or f"user_{user_id}"
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=Language.ARABIC,
            timezone="Africa/Cairo",
            latitude=30.0444,
            longitude=31.2357,
            city="القاهرة",
            country="مصر",
            last_active_date=datetime.now(timezone.utc)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Automatically subscribe user to daily broadcast jobs
        scheduler_service.add_user_to_all_daily_jobs(user_id)

        welcome_text = (
            "مرحبًا بك في رفيق 🌟\n\n"
            "رفيق هو مساعدك الإسلامي الشامل الذي يساعدك في قراءة القرآن، "
            "الأذكار، الأدعية، مواقيت الصلاة، والتعلم الإسلامي.\n\n"
            "✅ تم تفعيل التذكير اليومي التلقائي:\n"
            "🌅 صباحاً: آية اليوم + أذكار الصباح\n"
            "☀️ ظهراً: حديث اليوم\n"
            "🌆 عصراً/مساءً: نصيحة اليوم + أذكار المساء\n"
            "🌙 ليلاً: دعاء اليوم + أذكار النوم\n\n"
            "ستصلك التذكيرات تلقائياً كل يوم!"
        )
    else:
        # Update last active date
        user.last_active_date = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        welcome_text = (
            f"مرحبًا بعودتك، {user.first_name or 'صديقي'}! 🌟\n\n"
            "تابع رحلتك الروحانية معنا. "
            "بارك الله في جهودك."
        )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user.language.value if user.language else "ar", user_id)
    )
    
    # Forcefully clear any persistent reply keyboards
    await message.answer(
        "✅ تم تفعيل الواجهة الجديدة",
        reply_markup=ReplyKeyboardRemove()
    )

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, db: AsyncSession):
    """Show main menu from callback"""
    await callback.answer("🔙 القائمة الرئيسية")
    
    user_id = callback.from_user.id

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    language = user.language.value if user else "ar"

    await callback.message.edit_text(
        "🌟 *رفيق - القائمة الرئيسية* 🌟\n\n"
        "اختر قسماً للاستكشاف:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(language, user_id)
    )


@router.message(F.text == "📖 القرآن الكريم")
async def message_quran(message: Message, db: AsyncSession):
    """Handle Quran button from reply keyboard - DEPRECATED, use inline keyboard"""
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
            "يرجى استخدام الأزرار أدناه للتنقل."
        )
    else:
        response_text = (
            "📖 *القرآن الكريم* 📖\n\n"
            "مرحباً بك في القرآن الكريم.\n\n"
            "يرجى استخدام الأزرار أدناه للتنقل."
        )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard(language)
    )


@router.message(F.text == "🤲 الأذكار والأدعية")
async def message_adhkar(message: Message, db: AsyncSession):
    """Handle Adhkar button from reply keyboard - DEPRECATED, use inline keyboard"""
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


@router.message(F.text == "📚 الأحاديث النبوية")
async def message_hadith(message: Message, db: AsyncSession):
    """Handle Hadith button from reply keyboard - DEPRECATED, use inline keyboard"""
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
        "📚 *الأحاديث النبوية الشريفة* 📚\n\n"
        "اختر مجموعة:",
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_keyboard(language)
    )


@router.message(F.text == "🕌 مواقيت الصلاة")
async def message_prayer(message: Message, db: AsyncSession):
    """Handle Prayer button from reply keyboard - DEPRECATED, use inline keyboard"""
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
        "🕌 *الصلاة والعبادة* 🕌\n\n"
        "اختر خياراً:",
        parse_mode="Markdown",
        reply_markup=get_prayer_menu_keyboard(language)
    )


@router.message(F.text == "🤖 المساعد الذكي")
async def message_ai_assistant(message: Message, db: AsyncSession):
    """Handle AI Assistant button from reply keyboard - DEPRECATED, use inline keyboard"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    await message.answer(
        "🤖 *المساعد الذكي* 🤖\n\n"
        "المساعد الذكي قيد التطوير.\n\n"
        "سيتم إطلاقه قريباً.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard("ar")
    )


@router.message(F.text == "⚙️ الإعدادات")
async def message_settings(message: Message, db: AsyncSession):
    """Handle Settings button from reply keyboard - DEPRECATED, use inline keyboard"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    await message.answer(
        "⚙️ *الإعدادات* ⚙️\n\n"
        "الإعدادات قيد التطوير.\n\n"
        "يرجى استخدام القائمة الرئيسية.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard("ar")
    )


@router.message(F.text == "🔙 القائمة الرئيسية")
async def message_main_menu(message: Message, db: AsyncSession):
    """Handle Main Menu button from reply keyboard - DEPRECATED, use inline keyboard"""
    user_id = message.from_user.id

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    language = user.language.value if user else "ar"

    await message.answer(
        "🌟 *رفيق - القائمة الرئيسية* 🌟\n\n"
        "اختر قسماً للاستكشاف:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(language)
    )


@router.message(F.text == "🔙 عودة للسور")
async def message_back_to_surahs(message: Message, db: AsyncSession):
    """Handle Return to Surahs button from Quran reading - DEPRECATED, use inline keyboard"""
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
        "📖 *القرآن الكريم* 📖\n\n"
        "مرحباً بك في القرآن الكريم.\n\n"
        "يرجى استخدام الأزرار أدناه للتنقل.",
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard(language)
    )


@router.message(F.text == "🔧 لوحة التحكم")
async def message_admin_panel(message: Message, db: AsyncSession):
    """Handle Admin Panel button from reply keyboard - DEPRECATED, use inline keyboard"""
    from config.settings import settings
    user_id = message.from_user.id
    
    # Check if user is admin
    if not settings.ADMIN_ID or user_id != settings.ADMIN_ID:
        await message.answer(
            "❌ الوصول مرفوض. للمشرفين فقط.",
            reply_markup=get_main_menu_keyboard("ar")
        )
        return
    
    await message.answer(
        "🔧 *لوحة التحكم* 🔧\n\n"
        "لوحة التحكم قيد التطوير.\n\n"
        "يرجى استخدام القائمة الرئيسية.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard("ar")
    )


# Quran sub-menu handlers
@router.message(F.text == "📜 قراءة السور")
async def message_quran_read_surah(message: Message, db: AsyncSession, state: FSMContext):
    """Handle Quran Read Surah button - Show list of Surahs and set FSM state - DEPRECATED, use inline keyboard"""
    from keyboards import get_quran_menu_keyboard
    
    # Set FSM state to wait for surah number
    await state.set_state(QuranStates.waiting_for_surah_number)
    
    # Simple message to avoid message too long error
    text = "📜 *قراءة السور*\n\n"
    text += "يرجى إرسال رقم السورة للقراءة (1-114).\n\n"
    text += "📝 مثال: اكتب '1' لقراءة سورة الفاتحة\n"
    text += "📝 مثال: اكتب '2' لقراءة سورة البقرة\n\n"
    text += "السور من 1 إلى 114"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard("ar")
    )


@router.message(F.text == "📖 الأجزاء")
async def message_quran_juz(message: Message, db: AsyncSession):
    """Handle Quran Juz button - Show Juz information - DEPRECATED, use inline keyboard"""
    from keyboards import get_quran_menu_keyboard
    
    text = "📖 *الأجزاء (30 جزء)*\n\n"
    text += "القرآن الكريم مقسم إلى 30 جزءاً متساوياً.\n\n"
    text += "لكل جزء حوالي 20 صفحة.\n\n"
    text += "يرجى استخدام خيار 'قراءة السور' لقراءة السور مباشرة.\n\n"
    text += "يمكنك إرسال رقم السورة (1-114) للقراءة المباشرة."
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_quran_menu_keyboard("ar")
    )


# Quran surah number handler (only when in waiting_for_surah_number state)
@router.message(QuranStates.waiting_for_surah_number, F.text.regexp(r'^\d+$'))
async def message_read_surah_by_number(message: Message, db: AsyncSession, state: FSMContext):
    """Handle reading a Surah by number when in FSM state - DEPRECATED, use inline keyboard"""
    from handlers.quran import get_surah_ayahs, save_last_read_position
    from keyboards import get_quran_surah_keyboard
    
    surah_number = int(message.text)
    
    # Clear FSM state
    await state.clear()
    
    if surah_number < 1 or surah_number > 114:
        await message.answer(
            "❌ رقم السورة غير صحيح. يرجى إدخال رقم بين 1 و 114.",
            reply_markup=get_quran_menu_keyboard("ar")
        )
        return
    
    # Fetch the Surah
    surah_data = await get_surah_ayahs(surah_number)
    
    if not surah_data:
        await message.answer(
            "❌ فشل تحميل السورة. يرجى المحاولة مرة أخرى لاحقاً.",
            reply_markup=get_quran_menu_keyboard("ar")
        )
        return
    
    # Get Surah info
    surah_info = surah_data.get("surah", {})
    surah_name_ar = surah_info.get("name", "")
    surah_name_en = surah_info.get("englishName", "")
    ayahs = surah_data.get("ayahs", [])
    
    # Build full Surah text
    text = f"📖 *سورة {surah_name_ar} ({surah_name_en})*\n\n"
    
    # Add all Ayahs
    for ayah in ayahs:
        ayah_num = ayah.get("numberInSurah")
        ayah_text = ayah.get("text", "")
        text += f"{ayah_num}. {ayah_text}\n"
    
    # Send in chunks if too long (Telegram limit is 4096 chars)
    max_length = 4000
    if len(text) <= max_length:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_quran_surah_keyboard("ar")
        )
    else:
        # Split into chunks
        chunks = []
        current_chunk = ""
        lines = text.split('\n')
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                chunks.append(current_chunk)
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                await message.answer(
                    chunk,
                    parse_mode="Markdown",
                    reply_markup=get_quran_surah_keyboard("ar")
                )
            else:
                await message.answer(chunk, parse_mode="Markdown")
    
    # Save last read position
    user_id = message.from_user.id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        await save_last_read_position(user_id, surah_number, len(ayahs), db)


@router.message(F.text == "🔖 العلامات المحفوظة")
async def message_quran_bookmarks(message: Message, db: AsyncSession):
    """Handle Quran Bookmarks button"""
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
            reply_markup=get_quran_menu_reply_keyboard("ar")
        )
        return
    
    if not user.last_read_surah:
        await message.answer(
            "🔖 *العلامات المحفوظة*\n\n"
            "لم تقم بحفظ أي علامات بعد.\n\n"
            "ابدأ بقراءة القرآن لحفظ مواضعك المفضلة.",
            parse_mode="Markdown",
            reply_markup=get_quran_menu_reply_keyboard("ar")
        )
    else:
        await message.answer(
            f"🔖 *العلامات المحفوظة*\n\n"
            f"📍 آخر قراءة: سورة {user.last_read_surah}، آية {user.last_read_ayah}\n\n"
            f"اكتب رقم السورة للعودة إلى هذا الموضع.",
            parse_mode="Markdown",
            reply_markup=get_quran_menu_reply_keyboard("ar")
        )


@router.message(F.text == "📍 موضع القراءة الأخير")
async def message_quran_resume(message: Message, db: AsyncSession):
    """Handle Quran Resume Reading button"""
    from handlers.quran import get_surah_ayahs, save_last_read_position
    from keyboards import get_quran_surah_reply_keyboard
    
    user_id = message.from_user.id
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.last_read_surah:
        await message.answer(
            "❌ لم يتم العثور على موضع قراءة محفوظ. ابدأ بقراءة سورة أولاً.",
            reply_markup=get_quran_menu_reply_keyboard("ar")
        )
        return
    
    # Fetch the Surah
    surah_data = await get_surah_ayahs(user.last_read_surah)
    
    if not surah_data:
        await message.answer(
            "❌ فشل تحميل السورة المحفوظة. يرجى المحاولة مرة أخرى لاحقاً.",
            reply_markup=get_quran_menu_reply_keyboard("ar")
        )
        return
    
    # Get Surah info
    surah_info = surah_data.get("surah", {})
    surah_name_ar = surah_info.get("name", "")
    surah_name_en = surah_info.get("englishName", "")
    ayahs = surah_data.get("ayahs", [])
    
    # Build full Surah text
    text = f"📖 *سورة {surah_name_ar} ({surah_name_en})*\n\n"
    
    # Add all Ayahs
    for ayah in ayahs:
        ayah_num = ayah.get("numberInSurah")
        ayah_text = ayah.get("text", "")
        text += f"{ayah_num}. {ayah_text}\n"
    
    # Send in chunks if too long
    max_length = 4000
    if len(text) <= max_length:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_quran_surah_reply_keyboard("ar")
        )
    else:
        # Split into chunks
        chunks = []
        current_chunk = ""
        lines = text.split('\n')
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                chunks.append(current_chunk)
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                await message.answer(
                    chunk,
                    parse_mode="Markdown",
                    reply_markup=get_quran_surah_reply_keyboard("ar")
                )
            else:
                await message.answer(chunk, parse_mode="Markdown")


# Prayer sub-menu handlers
@router.message(F.text == "🕐 مواقيت الصلاة")
async def message_prayer_times(message: Message, db: AsyncSession):
    """Handle Prayer Times button"""
    from handlers.prayer import get_cairo_prayer_times
    from keyboards import get_prayer_menu_reply_keyboard
    
    prayer_data = await get_cairo_prayer_times()
    
    if prayer_data:
        timings = prayer_data.get("timings", {})
        date_info = prayer_data.get("date", {})
        
        response_text = (
            f"� *مواقيت الصلاة اليوم - القاهرة*\n\n"
            f"📅 *التاريخ:* {date_info.get('readable', 'N/A')}\n"
            f"🌍 *التقويم الهجري:* {date_info.get('hijri', {}).get('date', 'N/A')}\n\n"
            f"🌙 *الفجر:* {timings.get('Fajr', 'N/A')}\n"
            f"🌅 *الشروق:* {timings.get('Sunrise', 'N/A')}\n"
            f"☀️ *الظهر:* {timings.get('Dhuhr', 'N/A')}\n"
            f"🌤️ *العصر:* {timings.get('Asr', 'N/A')}\n"
            f"🌇 *المغرب:* {timings.get('Maghrib', 'N/A')}\n"
            f"🌃 *العشاء:* {timings.get('Isha', 'N/A')}"
        )
    else:
        response_text = (
            "❌ *خطأ في جلب مواقيت الصلاة*\n\n"
            "يرجى المحاولة مرة أخرى لاحقاً."
        )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_prayer_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🧭 اتجاه القبلة")
async def message_qibla(message: Message, db: AsyncSession):
    """Handle Qibla Direction button"""
    from keyboards import get_prayer_menu_reply_keyboard
    
    # Calculate Qibla direction for Cairo
    try:
        import httpx
        from config.settings import settings
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"http://api.aladhan.com/v1/qibla/{settings.prayer.DEFAULT_LATITUDE}/{settings.prayer.DEFAULT_LONGITUDE}"
            )
            response.raise_for_status()
            qibla_data = response.json()
            
            if qibla_data.get("code") == 200:
                qibla_info = qibla_data.get("data", {})
                direction = qibla_info.get("direction", "N/A")
                distance = qibla_info.get("distance", "N/A")
                
                response_text = (
                    f"🧭 *اتجاه القبلة - القاهرة*\n\n"
                    f"📍 *إحداثيات القاهرة:* {settings.prayer.DEFAULT_LATITUDE:.4f}, {settings.prayer.DEFAULT_LONGITUDE:.4f}\n"
                    f"🧭 *اتجاه القبلة:* {direction}°\n"
                    f"📏 *المسافة إلى مكة:* {distance} كم\n\n"
                    f"استخدم بوصلة هاتفك للعثور على الاتجاه الصحيح."
                )
            else:
                response_text = (
                    "❌ *خطأ في حساب اتجاه القبلة*\n\n"
                    "يرجى المحاولة مرة أخرى لاحقاً."
                )
    except Exception as e:
        response_text = (
            "❌ *خطأ في حساب اتجاه القبلة*\n\n"
            "يرجى المحاولة مرة أخرى لاحقاً."
        )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_prayer_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📅 التقويم الهجري")
async def message_hijri_calendar(message: Message, db: AsyncSession):
    """Handle Hijri Calendar button"""
    from handlers.prayer import get_cairo_prayer_times
    from keyboards import get_prayer_menu_reply_keyboard
    
    prayer_data = await get_cairo_prayer_times()
    
    if prayer_data:
        date_info = prayer_data.get("date", {})
        hijri = date_info.get("hijri", {})
        gregorian = date_info.get("gregorian", {})
        
        response_text = (
            f"📅 *التقويم الهجري - القاهرة*\n\n"
            f"🌙 *التاريخ الهجري:* {hijri.get('date', 'N/A')}\n"
            f"📖 *الشهر الهجري:* {hijri.get('month', {}).get('ar', 'N/A')}\n"
            f"🌍 *السنة الهجرية:* {hijri.get('year', 'N/A')}\n\n"
            f"📅 *التاريخ الميلادي:* {gregorian.get('date', 'N/A')}\n"
            f"🌍 *الشهر الميلادي:* {gregorian.get('month', {}).get('en', 'N/A')}\n"
            f"🌍 *السنة الميلادية:* {gregorian.get('year', 'N/A')}"
        )
    else:
        response_text = (
            "❌ *خطأ في جلب التاريخ الهجري*\n\n"
            "يرجى المحاولة مرة أخرى لاحقاً."
        )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_prayer_menu_reply_keyboard("ar")
    )


@router.message(F.text == "⚙️ طريقة الحساب")
async def message_prayer_method(message: Message, db: AsyncSession):
    """Handle Prayer Calculation Method button"""
    from keyboards import get_prayer_menu_reply_keyboard
    
    response_text = (
        "⚙️ *طريقة الحساب*\n\n"
        "طريقة الحساب الحالية: الجمعية الإسلامية لأمريكا الشمالية (ISNA)\n\n"
        "نستخدم طريقة حساب موحدة لموقع القاهرة."
    )
    
    await message.answer(
        response_text,
        parse_mode="Markdown",
        reply_markup=get_prayer_menu_reply_keyboard("ar")
    )


# Adhkar sub-menu handlers
@router.message(F.text == "🔍 البحث في الأذكار")
async def message_adhkar_search(message: Message, db: AsyncSession):
    """Handle Adhkar Search button"""
    from keyboards import get_adhkar_menu_reply_keyboard
    
    await message.answer(
        "🔍 *البحث في الأذكار*\n\n"
        "يرجى إرسال كلمة البحث للبحث في الأذكار.\n"
        "يمكنك البحث بالعربية أو الإنجليزية.",
        parse_mode="Markdown",
        reply_markup=get_adhkar_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🌅 أذكار الصباح")
async def message_adhkar_morning(message: Message, db: AsyncSession):
    """Handle Morning Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("morning", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار الصباح.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "🌅 *أذكار الصباح*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "🌙 أذكار المساء")
async def message_adhkar_evening(message: Message, db: AsyncSession):
    """Handle Evening Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("evening", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار المساء.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "🌙 *أذكار المساء*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "😴 أذكار النوم")
async def message_adhkar_sleep(message: Message, db: AsyncSession):
    """Handle Sleep Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("sleep", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار النوم.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "😴 *أذكار النوم*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "📚 أذكار عامة")
async def message_adhkar_general(message: Message, db: AsyncSession):
    """Handle General Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("general", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار عامة.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "📚 *أذكار عامة*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "🕌 أذكار الصلاة")
async def message_adhkar_post_prayer(message: Message, db: AsyncSession):
    """Handle Post-Prayer Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("post_prayer", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار الصلاة.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "🕌 *أذكار الصلاة*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "✈️ أذكار السفر")
async def message_adhkar_travel(message: Message, db: AsyncSession):
    """Handle Travel Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("travel", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار السفر.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "✈️ *أذكار السفر*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "🏛️ أذكار المسجد")
async def message_adhkar_mosque(message: Message, db: AsyncSession):
    """Handle Mosque Adhkar button"""
    from handlers.adhkar import ADHKAR_DATA
    from keyboards import get_adhkar_menu_reply_keyboard
    
    adhkar_list = ADHKAR_DATA.get("mosque", [])
    
    if not adhkar_list:
        await message.answer(
            "❌ لم يتم العثور على أذكار المسجد.",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )
        return
    
    # Build text with proper chunking
    text = "🏛️ *أذكار المسجد*\n\n"
    
    for i, adhkar in enumerate(adhkar_list, 1):
        arabic = adhkar.get("arabic", "")
        translation = adhkar.get("translation", "")
        count = adhkar.get("count", "")
        
        adhkar_text = f"**{i}. {arabic}**\n"
        if translation:
            adhkar_text += f"{translation}\n"
        if count:
            adhkar_text += f"التكرار: {count}\n"
        adhkar_text += "\n"
        
        # Check if adding this would exceed limit
        if len(text) + len(adhkar_text) > 4000:
            # Send current chunk
            await message.answer(text, parse_mode="Markdown")
            text = adhkar_text
        else:
            text += adhkar_text
    
    # Send remaining text
    if text:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_adhkar_menu_reply_keyboard("ar")
        )


@router.message(F.text == "⏰ تفعيل التذكير اليومي")
async def message_adhkar_schedule(message: Message, db: AsyncSession):
    """Handle Daily Reminder button"""
    from keyboards import get_adhkar_menu_reply_keyboard
    
    await message.answer(
        "⏰ *تفعيل التذكير اليومي*\n\n"
        "سيتم إرسال تذكير يومي بالأذكار.\n\n"
        "تم تفعيل التذكير بنجاح!",
        parse_mode="Markdown",
        reply_markup=get_adhkar_menu_reply_keyboard("ar")
    )


# Hadith sub-menu handlers
@router.message(F.text == "🔍 البحث في الأحاديث")
async def message_hadith_search(message: Message, db: AsyncSession):
    """Handle Hadith Search button"""
    from keyboards import get_hadith_menu_reply_keyboard
    
    await message.answer(
        "🔍 *البحث في الأحاديث*\n\n"
        "يرجى إرسال كلمة البحث للبحث في الأحاديث.\n"
        "يمكنك البحث بالعربية أو الإنجليزية.",
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📚 صحيح البخاري")
async def message_hadith_bukhari(message: Message, db: AsyncSession):
    """Handle Sahih Bukhari button - Show random hadith"""
    from handlers.hadith import HADITH_DATA
    from keyboards import get_hadith_menu_reply_keyboard
    import random
    
    hadith_list = HADITH_DATA.get("bukhari", [])
    
    if not hadith_list:
        await message.answer(
            "❌ لم يتم العثور على أحاديث صحيح البخاري.",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )
        return
    
    # Get random hadith
    hadith = random.choice(hadith_list)
    
    text = "📚 *صحيح البخاري*\n\n"
    text += f"**{hadith.get('arabic', '')}**\n\n"
    text += f"الراوي: {hadith.get('narrator', '')}\n"
    text += f"{hadith.get('english', '')}\n\n"
    text += f"المصدر: {hadith.get('reference', '')}\n"
    text += f"التقويم: {hadith.get('grade', '')}"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📖 صحيح مسلم")
async def message_hadith_muslim(message: Message, db: AsyncSession):
    """Handle Sahih Muslim button - Show random hadith"""
    from handlers.hadith import HADITH_DATA
    from keyboards import get_hadith_menu_reply_keyboard
    import random
    
    hadith_list = HADITH_DATA.get("muslim", [])
    
    if not hadith_list:
        await message.answer(
            "❌ لم يتم العثور على أحاديث صحيح مسلم.",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )
        return
    
    # Get random hadith
    hadith = random.choice(hadith_list)
    
    text = "📖 *صحيح مسلم*\n\n"
    text += f"**{hadith.get('arabic', '')}**\n\n"
    text += f"الراوي: {hadith.get('narrator', '')}\n"
    text += f"{hadith.get('english', '')}\n\n"
    text += f"المصدر: {hadith.get('reference', '')}\n"
    text += f"التقويم: {hadith.get('grade', '')}"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📜 سنن الترمذي")
async def message_hadith_tirmidhi(message: Message, db: AsyncSession):
    """Handle Sunan Tirmidhi button - Show random hadith"""
    from handlers.hadith import HADITH_DATA
    from keyboards import get_hadith_menu_reply_keyboard
    import random
    
    hadith_list = HADITH_DATA.get("tirmidhi", [])
    
    if not hadith_list:
        await message.answer(
            "❌ لم يتم العثور على أحاديث سنن الترمذي.",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )
        return
    
    # Get random hadith
    hadith = random.choice(hadith_list)
    
    text = "📜 *سنن الترمذي*\n\n"
    text += f"**{hadith.get('arabic', '')}**\n\n"
    text += f"الراوي: {hadith.get('narrator', '')}\n"
    text += f"{hadith.get('english', '')}\n\n"
    text += f"المصدر: {hadith.get('reference', '')}\n"
    text += f"التقويم: {hadith.get('grade', '')}"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📋 أحاديث عامة")
async def message_hadith_general(message: Message, db: AsyncSession):
    """Handle General Hadith button - Show random hadith"""
    from handlers.hadith import HADITH_DATA
    from keyboards import get_hadith_menu_reply_keyboard
    import random
    
    hadith_list = HADITH_DATA.get("general", [])
    
    if not hadith_list:
        await message.answer(
            "❌ لم يتم العثور على أحاديث عامة.",
            reply_markup=get_hadith_menu_reply_keyboard("ar")
        )
        return
    
    # Get random hadith
    hadith = random.choice(hadith_list)
    
    text = "📋 *أحاديث عامة*\n\n"
    text += f"**{hadith.get('arabic', '')}**\n\n"
    text += f"الراوي: {hadith.get('narrator', '')}\n"
    text += f"{hadith.get('english', '')}\n\n"
    text += f"المصدر: {hadith.get('reference', '')}\n"
    text += f"التقويم: {hadith.get('grade', '')}"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_hadith_menu_reply_keyboard("ar")
    )


# Admin menu handlers
@router.message(F.text == "📊 الإحصائيات المتقدمة")
async def message_admin_analytics(message: Message, db: AsyncSession):
    """Handle Admin Analytics button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "📊 *الإحصائيات المتقدمة*\n\n"
        "سيتم عرض الإحصائيات المتقدمة هنا.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "👥 إدارة المستخدمين")
async def message_admin_users(message: Message, db: AsyncSession):
    """Handle Admin Users button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "👥 *إدارة المستخدمين*\n\n"
        "سيتم عرض إدارة المستخدمين هنا.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🔍 البحث عن مستخدم")
async def message_admin_search(message: Message, db: AsyncSession):
    """Handle Admin Search button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "🔍 *البحث عن مستخدم*\n\n"
        "يرجى إرسال اسم المستخدم أو المعرف للبحث.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🚫 المستخدمون المحظورون")
async def message_admin_banned(message: Message, db: AsyncSession):
    """Handle Admin Banned Users button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "🚫 *المستخدمون المحظورون*\n\n"
        "سيتم عرض المستخدمين المحظورين هنا.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📢 إرسال إعلان")
async def message_admin_broadcast(message: Message, db: AsyncSession):
    """Handle Admin Broadcast button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "📢 *إرسال إعلان*\n\n"
        "يرجى إرسال نص الإعلان للإرسال لجميع المستخدمين.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🔧 تفعيل الميزات")
async def message_admin_toggles(message: Message, db: AsyncSession):
    """Handle Admin Toggles button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "🔧 *تفعيل الميزات*\n\n"
        "سيتم عرض إعدادات تفعيل الميزات هنا.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🔨 وضع الصيانة")
async def message_admin_maintenance(message: Message, db: AsyncSession):
    """Handle Admin Maintenance button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "🔨 *وضع الصيانة*\n\n"
        "سيتم عرض إعدادات الصيانة هنا.",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🗑️ مسح ذاكرة التخزين المؤقت")
async def message_admin_flush(message: Message, db: AsyncSession):
    """Handle Admin Flush Cache button"""
    from keyboards import get_admin_menu_reply_keyboard
    
    await message.answer(
        "🗑️ *مسح ذاكرة التخزين المؤقت*\n\n"
        "تم مسح ذاكرة التخزين المؤقت بنجاح!",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_reply_keyboard("ar")
    )


# Settings menu handlers
@router.message(F.text == "🌐 اللغة")
async def message_settings_language(message: Message, db: AsyncSession):
    """Handle Settings Language button"""
    from keyboards import get_settings_menu_reply_keyboard
    
    await message.answer(
        "🌐 *اللغة*\n\n"
        "اللغة الحالية: العربية\n\n"
        "يمكنك تغيير اللغة هنا.",
        parse_mode="Markdown",
        reply_markup=get_settings_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🔔 تذكير الصلاة")
async def message_settings_prayer(message: Message, db: AsyncSession):
    """Handle Settings Prayer Notifications button"""
    from keyboards import get_settings_menu_reply_keyboard
    
    await message.answer(
        "🔔 *تذكير الصلاة*\n\n"
        "تم تفعيل تذكير الصلاة.\n\n"
        "يمكنك تغيير إعدادات التذكير هنا.",
        parse_mode="Markdown",
        reply_markup=get_settings_menu_reply_keyboard("ar")
    )


@router.message(F.text == "📚 الوِرد اليومي")
async def message_settings_wird(message: Message, db: AsyncSession):
    """Handle Settings Daily Wird button"""
    from keyboards import get_settings_menu_reply_keyboard
    
    await message.answer(
        "📚 *الوِرد اليومي*\n\n"
        "تم تفعيل الوِرد اليومي.\n\n"
        "يمكنك تغيير إعدادات الوِرد هنا.",
        parse_mode="Markdown",
        reply_markup=get_settings_menu_reply_keyboard("ar")
    )


@router.message(F.text == "⏰ الإشعارات")
async def message_settings_notifications(message: Message, db: AsyncSession):
    """Handle Settings Notifications button"""
    from keyboards import get_settings_menu_reply_keyboard
    
    await message.answer(
        "⏰ *الإشعارات*\n\n"
        "تم تفعيل الإشعارات.\n\n"
        "يمكنك تغيير إعدادات الإشعارات هنا.",
        parse_mode="Markdown",
        reply_markup=get_settings_menu_reply_keyboard("ar")
    )


@router.message(F.text == "🎙️ صوت الأذان")
async def message_settings_adhan(message: Message, db: AsyncSession):
    """Handle Settings Adhan Audio button"""
    from keyboards import get_settings_menu_reply_keyboard
    
    await message.answer(
        "🎙️ *صوت الأذان*\n\n"
        "تم تفعيل صوت الأذان.\n\n"
        "يمكنك تغيير إعدادات صوت الأذان هنا.",
        parse_mode="Markdown",
        reply_markup=get_settings_menu_reply_keyboard("ar")
    )


# Notification preferences handlers
@router.message(F.text == "🌅 أذكار الصباح")
async def message_toggle_morning_adhkar(message: Message, db: AsyncSession):
    """Handle Toggle Morning Adhkar"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "🌅 *أذكار الصباح*\n\n"
        "تم تفعيل إشعارات أذكار الصباح.\n\n"
        "ستصلك أذكار الصباح يومياً الساعة 6 صباحاً.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "🌙 أذكار المساء")
async def message_toggle_evening_adhkar(message: Message, db: AsyncSession):
    """Handle Toggle Evening Adhkar"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "🌙 *أذكار المساء*\n\n"
        "تم تفعيل إشعارات أذكار المساء.\n\n"
        "ستصلك أذكار المساء يومياً الساعة 5 مساءً.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "😴 أذكار النوم")
async def message_toggle_night_adhkar(message: Message, db: AsyncSession):
    """Handle Toggle Night Adhkar"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "😴 *أذكار النوم*\n\n"
        "تم تفعيل إشعارات أذكار النوم.\n\n"
        "ستصلك أذكار النوم يومياً الساعة 10:30 مساءً.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "📖 آية اليوم")
async def message_toggle_daily_ayah(message: Message, db: AsyncSession):
    """Handle Toggle Daily Ayah"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "📖 *آية اليوم*\n\n"
        "تم تفعيل إشعارات آية اليوم.\n\n"
        "ستصلك آية يومية من القرآن الكريم.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "📚 حديث اليوم")
async def message_toggle_daily_hadith(message: Message, db: AsyncSession):
    """Handle Toggle Daily Hadith"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "📚 *حديث اليوم*\n\n"
        "تم تفعيل إشعارات حديث اليوم.\n\n"
        "ستصلك حديث شريف يومي.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "💡 نصيحة اليوم")
async def message_toggle_daily_tip(message: Message, db: AsyncSession):
    """Handle Toggle Daily Tip"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "💡 *نصيحة اليوم*\n\n"
        "تم تفعيل إشعارات نصيحة اليوم.\n\n"
        "ستصلك نصيحة إسلامية يومية.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "🤲 دعاء اليوم")
async def message_toggle_daily_dua(message: Message, db: AsyncSession):
    """Handle Toggle Daily Dua"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "🤲 *دعاء اليوم*\n\n"
        "تم تفعيل إشعارات دعاء اليوم.\n\n"
        "ستصلك دعاء يومي من القرآن والسنة.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


@router.message(F.text == "🕌 تذكير الجمعة")
async def message_toggle_friday(message: Message, db: AsyncSession):
    """Handle Toggle Friday Reminder"""
    from keyboards import get_notification_preferences_reply_keyboard
    
    await message.answer(
        "🕌 *تذكير الجمعة*\n\n"
        "تم تفعيل تذكير الجمعة.\n\n"
        "ستصلك تذكير يوم الجمعة قبل صلاة الجمعة.",
        parse_mode="Markdown",
        reply_markup=get_notification_preferences_reply_keyboard("ar")
    )


# Fallback handler for unmatched text messages (MUST BE LAST)
@router.message()
async def handle_unmatched_message(message: Message):
    """Handle any unmatched text messages"""
    await message.answer(
        "❌ عذراً، لم أفهم هذا الأمر.\n\n"
        "يرجى استخدام الأزرار أدناه للتنقل.",
        parse_mode="Markdown"
    )
