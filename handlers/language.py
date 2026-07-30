"""
Multi-language interface handler.
Allows users to switch between different languages.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User, Language
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()

# Supported languages
LANGUAGES = {
    "ar": {
        "name": "العربية",
        "emoji": "🇸🇦",
        "code": "ar"
    },
    "en": {
        "name": "English",
        "emoji": "🇬🇧",
        "code": "en"
    },
    "ur": {
        "name": "اردو",
        "emoji": "🇵🇰",
        "code": "ur"
    },
    "tr": {
        "name": "Türkçe",
        "emoji": "🇹🇷",
        "code": "tr"
    }
}


@router.callback_query(F.data == "language_menu")
async def handle_language_menu(callback: CallbackQuery, db: AsyncSession):
    """Show language selection menu"""
    await callback.answer("🌐 إعدادات اللغة")
    
    user_id = callback.from_user.id
    
    try:
        # Get current user language
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        current_lang = user.language.value if user else "ar"
        
        builder = InlineKeyboardBuilder()
        
        # Build language selection buttons
        for lang_code, lang_info in LANGUAGES.items():
            is_current = lang_code == current_lang
            status_emoji = "✅" if is_current else "⚪"
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_emoji} {lang_info['emoji']} {lang_info['name']}",
                    callback_data=f"lang_select_{lang_code}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            "🌐 *اختر اللغة*\n\n"
            "اختر اللغة المفضلة للبوت:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing language menu: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


@router.callback_query(F.data.startswith("lang_select_"))
async def handle_language_selection(callback: CallbackQuery, db: AsyncSession):
    """Handle language selection"""
    await callback.answer()
    
    lang_code = callback.data.replace("lang_select_", "")
    
    if lang_code not in LANGUAGES:
        await callback.message.edit_text("❌ لغة غير مدعومة")
        return
    
    lang_info = LANGUAGES[lang_code]
    await callback.answer(f"{lang_info['emoji']} {lang_info['name']}")
    
    user_id = callback.from_user.id
    
    try:
        # Update user language in database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Map language code to Language enum
            lang_mapping = {
                "ar": Language.ARABIC,
                "en": Language.ENGLISH,
                "ur": Language.URDU,
                "tr": Language.TURKISH
            }
            
            new_language = lang_mapping.get(lang_code, Language.ARABIC)
            user.language = new_language
            await db.commit()
            
            logger.info(f"Language changed for user {user_id} to {lang_code}")
        
        # Cache language preference in Redis
        await redis_client.client.set(f"user_language:{user_id}", lang_code)
        
        # Build updated keyboard
        builder = InlineKeyboardBuilder()
        
        for lc, li in LANGUAGES.items():
            is_current = lc == lang_code
            status_emoji = "✅" if is_current else "⚪"
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_emoji} {li['emoji']} {li['name']}",
                    callback_data=f"lang_select_{lc}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="go_main_menu")
        )
        
        await callback.message.edit_text(
            f"✅ تم تغيير اللغة إلى {lang_info['emoji']} {lang_info['name']}\n\n"
            f"اختر اللغة المفضلة للبوت:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        await callback.answer(f"❌ خطأ: {e}", show_alert=True)


async def get_user_language(user_id: int, db: AsyncSession) -> str:
    """
    Get user's preferred language.
    
    Args:
        user_id: Telegram user ID
        db: Database session
    
    Returns:
        Language code (e.g., 'ar', 'en')
    """
    try:
        # Check Redis cache first
        cached_lang = await redis_client.client.get(f"user_language:{user_id}")
        if cached_lang:
            return cached_lang
        
        # Fallback to database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            lang_code = user.language.value if user.language else "ar"
            # Cache in Redis
            await redis_client.client.set(f"user_language:{user_id}", lang_code)
            return lang_code
        
        return "ar"  # Default to Arabic
        
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return "ar"  # Default to Arabic


def get_text(key: str, language: str = "ar") -> str:
    """
    Get localized text for a given key.
    
    Args:
        key: Text key to look up
        language: Language code
    
    Returns:
        Localized text
    """
    # Simple translation dictionary
    translations = {
        "main_menu": {
            "ar": "القائمة الرئيسية",
            "en": "Main Menu",
            "ur": "مین مینو",
            "tr": "Ana Menü"
        },
        "quran": {
            "ar": "القرآن الكريم",
            "en": "Holy Quran",
            "ur": "قرآن پاک",
            "tr": "Kuran-ı Kerim"
        },
        "hadith": {
            "ar": "الأحاديث",
            "en": "Hadith",
            "ur": "حدیث",
            "tr": "Hadis"
        },
        "adhkar": {
            "ar": "الأذكار",
            "en": "Adhkar",
            "ur": "اذکار",
            "tr": "Ezkâr"
        },
        "prayer": {
            "ar": "الصلاة",
            "en": "Prayer",
            "ur": "نماز",
            "tr": "Namaz"
        },
        "back": {
            "ar": "العودة",
            "en": "Back",
            "ur": "واپس",
            "tr": "Geri"
        }
    }
    
    return translations.get(key, {}).get(language, translations.get(key, {}).get("ar", key))
