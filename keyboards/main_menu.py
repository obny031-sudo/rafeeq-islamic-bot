from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_keyboard(language: str = "ar", user_id: int = None) -> InlineKeyboardMarkup:
    """Generate main menu inline keyboard (Arabic only)"""
    from config.settings import settings
    
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📖 القرآن الكريم", callback_data="quran"),
        InlineKeyboardButton(text="🤲 الأذكار والأدعية", callback_data="adhkar")
    )
    builder.row(
        InlineKeyboardButton(text="📚 الأحاديث النبوية", callback_data="hadith"),
        InlineKeyboardButton(text="🕌 مواقيت الصلاة", callback_data="prayer")
    )
    builder.row(
        InlineKeyboardButton(text="🤖 المساعد الذكي", callback_data="ai_assistant"),
        InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="settings")
    )
    builder.row(
        InlineKeyboardButton(text="📿 التسبيح", callback_data="tasbeeh")
    )
    
    # Dynamic admin button for admin users only
    is_admin = user_id and settings.ADMIN_ID and user_id == settings.ADMIN_ID
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ لوحة الإدارة", callback_data="admin_panel")
        )

    return builder.as_markup()


def get_prayer_menu_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
    """Generate prayer module inline keyboard (Arabic only)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🕐 مواقيت الصلاة", callback_data="prayer_times"),
        InlineKeyboardButton(text="🧭 اتجاه القبلة", callback_data="qibla")
    )
    builder.row(
        InlineKeyboardButton(text="📅 التقويم الهجري", callback_data="hijri_calendar"),
        InlineKeyboardButton(text="⚙️ طريقة الحساب", callback_data="prayer_method")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )

    return builder.as_markup()


def get_quran_menu_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
    """Generate Quran module inline keyboard (Arabic only)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📜 قراءة السور", callback_data="quran_surah_list"),
        InlineKeyboardButton(text="📖 الأجزاء", callback_data="quran_juz_list")
    )
    builder.row(
        InlineKeyboardButton(text="🔖 العلامات المحفوظة", callback_data="quran_bookmarks"),
        InlineKeyboardButton(text="📍 موضع القراءة الأخير", callback_data="quran_last_position")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )

    return builder.as_markup()


def get_quran_surah_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
    """Generate Quran surah reading inline keyboard (Arabic only)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔙 عودة للسور", callback_data="quran"),
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )

    return builder.as_markup()


def get_adhkar_menu_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
    """Generate Adhkar module inline keyboard (Arabic only)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔍 البحث في الأذكار", callback_data="adhkar_search")
    )
    builder.row(
        InlineKeyboardButton(text="🌅 أذكار الصباح", callback_data="adhkar_morning"),
        InlineKeyboardButton(text="🌙 أذكار المساء", callback_data="adhkar_evening")
    )
    builder.row(
        InlineKeyboardButton(text="😴 أ الذكار", callback_data="adhkar_sleep"),
        InlineKeyboardButton(text="📚 أذكار عامة", callback_data="adhkar_general")
    )
    builder.row(
        InlineKeyboardButton(text="🕌 أذكار الصلاة", callback_data="adhkar_prayer"),
        InlineKeyboardButton(text="✈️ أذكار السفر", callback_data="adhkar_travel")
    )
    builder.row(
        InlineKeyboardButton(text="🏛️ أذكار المسجد", callback_data="adhkar_mosque"),
        InlineKeyboardButton(text="⏰ تفعيل التذكير اليومي", callback_data="customize_adhkar_timings")
    )
    builder.row(
        InlineKeyboardButton(text="😊 الأذكار حسب المزاج", callback_data="mood_adhkar_menu")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )

    return builder.as_markup()


def get_hadith_menu_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
    """Generate Hadith module inline keyboard (Arabic only)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔍 البحث في الأحاديث", callback_data="hadith_search")
    )
    builder.row(
        InlineKeyboardButton(text="📚 صحيح البخاري", callback_data="hadith_bukhari"),
        InlineKeyboardButton(text="📖 صحيح مسلم", callback_data="hadith_muslim")
    )
    builder.row(
        InlineKeyboardButton(text="📜 سنن الترمذي", callback_data="hadith_tirmidhi"),
        InlineKeyboardButton(text="📋 أحاديث عامة", callback_data="hadith_general")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )

    return builder.as_markup()


def get_location_request_keyboard(language: str = "ar") -> InlineKeyboardMarkup:
    """Generate location request keyboard (Arabic only)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📍 إرسال موقعي", callback_data="send_location")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
    )

    return builder.as_markup()


