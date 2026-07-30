"""
Adhkar Plugin implementation.
Provides daily Adhkar and supplications.
"""

import logging
from typing import Optional
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import random

from bot.core.base_plugin import BasePlugin
from config.settings import settings
from cache import RedisCache, CacheKeyBuilder
from repositories import UserRepository
from utils.logger import get_logger
from keyboards import get_main_menu_keyboard

logger = get_logger("rafeeq.adjkar")


# Adhkar database
ADHKAR_DATA = {
    "morning": [
        {
            "arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ",
            "transliteration": "Asbahna wa asbahal mulku lillah, walhamdu lillah",
            "translation": "We have entered the morning and the dominion belongs to Allah, and all praise is for Allah.",
            "reference": "Muslim 271"
        },
        {
            "arabic": "اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُور",
            "transliteration": "Allahumma bika asbahna wa bika amsayna, wa bika nahya wa bika namutu, wa ilaykan-nushur",
            "translation": "O Allah, by Your grace we enter the morning and by Your grace we enter the evening, by Your grace we live and by Your grace we die, and to You is the resurrection.",
            "reference": "Tirmidhi 3392"
        }
    ],
    "evening": [
        {
            "arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ",
            "transliteration": "Amsayna wa amsal mulku lillah, walhamdu lillah",
            "translation": "We have entered the evening and the dominion belongs to Allah, and all praise is for Allah.",
            "reference": "Muslim 271"
        }
    ],
    "general": [
        {
            "arabic": "سُبْحَانَ اللهِ",
            "transliteration": "SubhanAllah",
            "translation": "Glory be to Allah.",
            "reference": "Muslim 2692"
        }
    ]
}


class AdhkarPlugin(BasePlugin):
    """Plugin for daily Adhkar and supplications"""
    
    name = "adhkar"
    version = "1.0.0"
    description = "Daily Adhkar and supplications"
    author = "Rafeeq Team"
    
    def __init__(self):
        super().__init__()
        self.router = Router()
        self.cache: Optional[RedisCache] = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup plugin handlers"""
        
        @self.router.callback_query(F.data == "adhkar")
        async def show_adhkar_menu(callback: CallbackQuery, db: AsyncSession):
            """Show Adhkar module menu"""
            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(callback.from_user.id)
            
            if not user:
                await callback.message.edit_text(
                    "❌ يرجى بدء البوت أولاً باستخدام الأمر /start",
                    reply_markup=get_main_menu_keyboard("ar")
                )
                await callback.answer()
                return
            
            # Force Arabic only
            language = "ar"
            
            # Build Adhkar menu
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram.types import InlineKeyboardButton
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🌅 أذكار الصباح", callback_data="adhkar_morning"),
                InlineKeyboardButton(text="🌙 أذكار المساء", callback_data="adhkar_evening")
            )
            builder.row(
                InlineKeyboardButton(text="📚 أذكار عامة", callback_data="adhkar_general")
            )
            builder.row(
                InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")
            )
            
            await callback.message.edit_text(
                "🤲 *الأذكار والأدعية* 🤲\n\n"
                "اختر القسم المطلوب:",
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
        
        @self.router.callback_query(F.data.startswith("adhkar_"))
        async def show_adhkar_category(callback: CallbackQuery, db: AsyncSession):
            """Show Adhkar from a specific category"""
            category = callback.data.split("_")[-1]
            
            if category not in ADHKAR_DATA:
                await callback.answer("فئة غير صالحة")
                return
            
            # Get random Adhkar from category
            adhkar = random.choice(ADHKAR_DATA[category])
            
            # Build response
            arabic = adhkar.get("arabic", "")
            transliteration = adhkar.get("transliteration", "")
            translation = adhkar.get("translation", "")
            reference = adhkar.get("reference", "")
            
            # Arabic category names
            category_names = {
                "morning": "أذكار الصباح",
                "evening": "أذكار المساء",
                "general": "أذكار عامة"
            }
            category_ar = category_names.get(category, category)
            
            text = f"🤲 *{category_ar}*\n\n"
            text += f"📖 *النص العربي:*\n{arabic}\n\n"
            text += f"🔤 *النطق:*\n{transliteration}\n\n"
            text += f"📝 *الترجمة:*\n{translation}\n\n"
            text += f"📚 *المصدر:* {reference}"
            
            # Build keyboard with "Next" button
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram.types import InlineKeyboardButton
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🔄 ذكر آخر", callback_data=f"adhkar_{category}")
            )
            builder.row(
                InlineKeyboardButton(text="🔙 العودة للقائمة", callback_data="adhkar")
            )
            
            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
    
    async def initialize(self, bot: Bot) -> None:
        """Initialize the plugin"""
        self.bot = bot
        
        # Initialize cache
        self.cache = RedisCache(settings.REDIS_URL, settings.REDIS_CACHE_DB)
        await self.cache.connect()
        
        logger.info("Adhkar plugin initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the plugin"""
        if self.cache:
            await self.cache.disconnect()
        logger.info("Adhkar plugin shutdown")
    
    def get_router(self) -> Router:
        """Get the router for this plugin"""
        return self.router
