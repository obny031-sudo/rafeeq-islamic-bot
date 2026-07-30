"""
Quran Plugin implementation.
Provides Quran reading with pagination and API integration.
"""

import logging
from typing import Optional
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from bot.core.base_plugin import BasePlugin
from config.settings import settings
from cache import RedisCache, CacheKeyBuilder
from repositories import UserRepository
from utils.logger import get_logger
from keyboards import get_main_menu_keyboard

logger = get_logger("rafeeq.quran")


# FSM States for Quran navigation
class QuranStates(StatesGroup):
    reading = State()
    selecting_surah = State()


class QuranPlugin(BasePlugin):
    """Plugin for Quran reading with pagination"""
    
    name = "quran"
    version = "1.0.0"
    description = "Quran reading with pagination and API integration"
    author = "Rafeeq Team"
    
    def __init__(self):
        super().__init__()
        self.router = Router()
        self.cache: Optional[RedisCache] = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup plugin handlers"""
        
        @self.router.callback_query(F.data == "quran")
        async def show_quran_menu(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
            """Show Quran module menu"""
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
            
            # Create inline keyboard for Quran options
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram.types import InlineKeyboardButton
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="📜 قراءة السور", callback_data="quran_read_surah"),
                InlineKeyboardButton(text="🔍 بحث", callback_data="quran_search")
            )
            builder.row(
                InlineKeyboardButton(text="📖 موضع القراءة الأخير", callback_data="quran_resume")
            )
            builder.row(
                InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")
            )
            
            await callback.message.edit_text(
                response_text,
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
        
        logger.info("Quran plugin initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the plugin"""
        if self.cache:
            await self.cache.disconnect()
        logger.info("Quran plugin shutdown")
    
    def get_router(self) -> Router:
        """Get the router for this plugin"""
        return self.router
