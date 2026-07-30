"""
Prayer Plugin implementation.
Provides location-based prayer times and notifications.
"""

import logging
from typing import Optional
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.base_plugin import BasePlugin
from config.settings import settings
from cache import RedisCache, cached, CacheKeyBuilder
from utils.logger import get_logger

logger = get_logger("rafeeq.prayer")


class PrayerPlugin(BasePlugin):
    """Plugin for prayer times and notifications"""
    
    name = "prayer"
    version = "1.0.0"
    description = "Location-based prayer times and notifications"
    author = "Rafeeq Team"
    
    def __init__(self):
        super().__init__()
        self.router = Router()
        self.cache: Optional[RedisCache] = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup plugin handlers"""
        @self.router.callback_query(F.data == "prayer")
        async def show_prayer_menu(callback: CallbackQuery, db: AsyncSession):
            """Show prayer module menu"""
            from repositories import UserRepository
            from keyboards import get_prayer_menu_keyboard
            
            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(callback.from_user.id)
            
            language = user.language.value if user and user.language else "ar"
            
            await callback.message.edit_text(
                "🕌 *الصلاة والعبادة* 🕌\n\n"
                "اختر خياراً:",
                parse_mode="Markdown",
                reply_markup=get_prayer_menu_keyboard(language)
            )
            
            await callback.answer()
        
        @self.router.callback_query(F.data == "send_location")
        async def request_location(callback: CallbackQuery, db: AsyncSession):
            """Prompt user to share their location."""
            from repositories import UserRepository

            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(callback.from_user.id)
            language = user.language.value if user and user.language else "en"

            if language == "ar":
                text = (
                    "📍 *يرجى مشاركة موقعك*\n\n"
                    "أرسل موقعك الحالي من قائمة المرفقات في تيليجرام."
                )
            else:
                text = (
                    "📍 *Please share your location*\n\n"
                    "Send your current location using Telegram's attachment menu."
                )

            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()

        @self.router.callback_query(F.data.in_({"qibla", "hijri_calendar", "fasting_reminders"}))
        async def show_coming_soon(callback: CallbackQuery, db: AsyncSession):
            """Show coming soon message for prayer sub-features."""
            from repositories import UserRepository
            from keyboards import get_prayer_menu_keyboard

            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(callback.from_user.id)
            language = user.language.value if user and user.language else "en"

            if language == "ar":
                text = (
                    "🚧 *قريباً!* 🚧\n\n"
                    "هذه الميزة قيد التطوير وستكون متاحة قريباً."
                )
            else:
                text = (
                    "🚧 *Coming Soon!* 🚧\n\n"
                    "This feature is under development and will be available soon."
                )

            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_prayer_menu_keyboard(language),
            )
            await callback.answer()

        @self.router.message(F.content_type == "location")
        async def handle_location(message: Message, db: AsyncSession):
            """Handle location message from user"""
            from repositories import UserRepository
            from keyboards import get_main_menu_keyboard
            
            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(message.from_user.id)
            
            if user:
                latitude = message.location.latitude
                longitude = message.location.longitude
                
                # Update user location
                await user_repo.update_location(
                    message.from_user.id,
                    latitude,
                    longitude
                )
                
                # Fetch prayer times with caching
                prayer_data = await self._get_prayer_times_cached(
                    latitude=latitude,
                    longitude=longitude,
                    method=user.prayer_method,
                    asr_method=user.asr_method,
                    timezone=user.timezone
                )
                
                if prayer_data:
                    timings = prayer_data.get("timings", {})
                    date_info = prayer_data.get("date", {})
                    
                    response_text = (
                        f"✅ *Location Saved Successfully!*\n\n"
                        f"📍 *Coordinates:* {latitude:.4f}, {longitude:.4f}\n"
                        f"📅 *Date:* {date_info.get('readable', 'N/A')}\n\n"
                        f"🕌 *Today's Prayer Times:*\n\n"
                        f"Fajr: {timings.get('Fajr', 'N/A')}\n"
                        f"Sunrise: {timings.get('Sunrise', 'N/A')}\n"
                        f"Dhuhr: {timings.get('Dhuhr', 'N/A')}\n"
                        f"Asr: {timings.get('Asr', 'N/A')}\n"
                        f"Maghrib: {timings.get('Maghrib', 'N/A')}\n"
                        f"Isha: {timings.get('Isha', 'N/A')}"
                    )
                else:
                    response_text = (
                        "✅ *Location Saved Successfully!*\n\n"
                        f"📍 *Coordinates:* {latitude:.4f}, {longitude:.4f}\n\n"
                        "❌ Could not fetch prayer times at this moment."
                    )
                
                await message.answer(
                    response_text,
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard(user.language.value if user.language else "en")
                )
            else:
                await message.answer("❌ Please start the bot first using /start command.")
        
        @self.router.callback_query(F.data == "prayer_times")
        async def show_prayer_times(callback: CallbackQuery, db: AsyncSession):
            """Show current prayer times for Cairo"""
            from repositories import UserRepository
            from keyboards import get_prayer_menu_keyboard
            
            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(callback.from_user.id)
            
            # Use Cairo coordinates as default
            latitude = 30.0444  # Cairo
            longitude = 31.2357  # Cairo
            method = 5  # Egyptian General Authority of Survey
            asr_method = 1  # Shafi
            timezone = "Africa/Cairo"
            
            prayer_data = await self._get_prayer_times_cached(
                latitude=latitude,
                longitude=longitude,
                method=method,
                asr_method=asr_method,
                timezone=timezone
            )
            
            if prayer_data:
                timings = prayer_data.get("timings", {})
                date_info = prayer_data.get("date", {})
                
                response_text = (
                    f"🕌 *مواقيت الصلاة - القاهرة*\n\n"
                    f"📅 *التاريخ:* {date_info.get('readable', 'N/A')}\n"
                    f"🌍 *الهجري:* {date_info.get('hijri', {}).get('date', 'N/A')}\n\n"
                    f"🌙 *الفجر:* {timings.get('Fajr', 'N/A')}\n"
                    f"🌅 *الشروق:* {timings.get('Sunrise', 'N/A')}\n"
                    f"☀️ *الظهر:* {timings.get('Dhuhr', 'N/A')}\n"
                    f"🌤️ *العصر:* {timings.get('Asr', 'N/A')}\n"
                    f"🌇 *المغرب:* {timings.get('Maghrib', 'N/A')}\n"
                    f"🌃 *العشاء:* {timings.get('Isha', 'N/A')}"
                )
            else:
                response_text = "❌ *خطأ في جلب مواقيت الصلاة*"
            
            await callback.message.edit_text(
                response_text,
                parse_mode="Markdown",
                reply_markup=get_prayer_menu_keyboard(user.language.value if user.language else "ar")
            )
            await callback.answer()
    
    async def _get_prayer_times_cached(
        self,
        latitude: float,
        longitude: float,
        method: int,
        asr_method: int,
        timezone: str
    ) -> Optional[dict]:
        """Get prayer times with caching"""
        from services.prayer_service import prayer_service
        
        cache_key = CacheKeyBuilder.prayer_times(
            latitude, longitude, method, timezone
        )
        
        # Try cache first
        if self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for prayer times: {cache_key}")
                return cached_data
        
        # Fetch from API
        prayer_data = await prayer_service.get_prayer_times(
            latitude=latitude,
            longitude=longitude,
            method=method,
            asr_method=asr_method,
            timezone=timezone
        )
        
        # Cache the result
        if prayer_data and self.cache:
            await self.cache.set(
                cache_key,
                prayer_data,
                settings.prayer.PRAYER_CACHE_TTL
            )
            logger.debug(f"Cached prayer times: {cache_key}")
        
        return prayer_data
    
    async def initialize(self, bot: Bot) -> None:
        """Initialize the plugin"""
        self.bot = bot
        
        # Initialize cache
        from config.settings import settings
        self.cache = RedisCache(settings.REDIS_URL, settings.REDIS_CACHE_DB)
        await self.cache.connect()
        
        logger.info(f"Prayer plugin initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the plugin"""
        if self.cache:
            await self.cache.disconnect()
        logger.info("Prayer plugin shutdown")
    
    def get_router(self) -> Router:
        """Get the router for this plugin"""
        return self.router
